import json
import shutil

import pytest
import yaml

from eval.mutate import apply_mutations
from eval.run_contracts import (
    ALL_HARNESSES,
    REPO,
    SKILL_SRC,
    Outcome,
    load_contracts,
    select_harnesses,
    select_subject_model,
    validate_contract,
    write_results,
)


def test_runner_targets_the_production_skill():
    assert SKILL_SRC.name == "miniproject"
    assert SKILL_SRC.parent.name == "skills"


def test_every_contract_has_an_applicable_negative_control(tmp_path):
    contracts = load_contracts(None)
    assert contracts

    for contract in contracts:
        installed = tmp_path / contract["id"]
        shutil.copytree(SKILL_SRC, installed)
        result = apply_mutations(installed, contract["negative_control"]["mutate"])
        assert result.applied, f"{contract['id']}: {result.detail}"


def test_every_contract_claims_all_three_harnesses():
    for contract in load_contracts(None):
        assert set(contract["harnesses"]) == set(ALL_HARNESSES)


def test_behavioral_contracts_cover_every_user_story():
    coverage = yaml.safe_load((REPO / "eval" / "user_story_coverage.yaml").read_text())
    claimed = {
        story_id
        for contract in load_contracts(None)
        for story_id in contract.get("stories", [])
    }

    assert claimed == set(coverage)


def test_at_least_one_contract_asserts_on_an_artifact():
    assert any(c["assert"]["type"] == "artifact" for c in load_contracts(None))


def test_broken_phase_zero_bundling_contract_is_replaced_by_counter_prior_validation():
    contract = load_contracts("MP-C02")[0]
    combined = " ".join(
        (contract["name"], contract["subject"]["prompt"], str(contract["assert"]))
    ).lower()
    assert "presence" in combined
    assert "not yet" in combined
    assert "backend api changes for widget reporting" not in combined


def test_discovery_contract_targets_a_terminal_outcome_not_estimation_priors():
    contract = load_contracts("MP-C01")[0]
    combined = " ".join(
        (contract["name"], contract["subject"]["prompt"], str(contract["assert"]))
    ).lower()
    assert "more discovery" in combined
    assert "next question" in combined
    assert "paste-ready" in combined
    assert "story points" not in combined


def test_discovery_contract_asserts_on_the_written_decision_record():
    contract = load_contracts("MP-C01")[0]

    assert contract["subject"]["sandbox"] == "workspace-write"
    assert contract["assert"]["type"] == "artifact"
    assert {
        (check["kind"], check["path"])
        for check in contract["assert"]["checks"]
    } == {
        ("exists", "discovery-decision.md"),
        ("contains", "discovery-decision.md"),
    }
    patterns = [
        check.get("pattern", "") for check in contract["assert"]["checks"]
    ]
    assert r"(?i)more discovery" in patterns


def test_owner_contract_distinguishes_contribution_from_fragmented_accountability():
    criterion = load_contracts("MP-C04")[0]["assert"]["pass"].lower()
    assert "may lead or implement" in criterion
    assert "explicitly makes them owners" in criterion


def test_contract_without_negative_control_is_rejected():
    with pytest.raises(ValueError, match="negative_control"):
        validate_contract(
            {
                "id": "MP-X",
                "name": "missing mutation",
                "subject": {"fixture": "fixtures/p0-2", "prompt": "x"},
                "assert": {"type": "response", "pass": "x"},
                "harnesses": list(ALL_HARNESSES),
            }
        )


def test_default_selection_uses_each_contract_claim_and_filter_restricts_it():
    contract = {"harnesses": ["codex", "junie", "claude"]}
    assert select_harnesses(contract, None) == ["codex", "junie", "claude"]
    assert select_harnesses(contract, ["junie"]) == ["junie"]


def test_results_are_recorded_one_row_per_contract_harness(tmp_path):
    outcomes = [
        Outcome("MP-C01", "codex", "normal", "PASS"),
        Outcome("MP-C01", "junie", "normal", "PASS"),
        Outcome("MP-C01", "claude", "normal", "PASS"),
    ]

    path = write_results(tmp_path, outcomes, {name: "v1" for name in ALL_HARNESSES})
    rows = [json.loads(line) for line in path.read_text().splitlines()]

    assert [row["harness"] for row in rows] == list(ALL_HARNESSES)
    assert {row["cli_version"] for row in rows} == {"v1"}


def test_contract_model_override_is_scoped_to_one_harness():
    contract = {"subject": {"models": {"claude": "sonnet"}}}
    assert select_subject_model(contract, "claude") == "sonnet"
    assert select_subject_model(contract, "codex") == "gpt-5.6-luna"


def test_artifact_contracts_pin_claude_to_sonnet():
    for contract in load_contracts(None):
        if contract["assert"]["type"] == "artifact":
            assert contract["subject"]["models"]["claude"] == "sonnet"
