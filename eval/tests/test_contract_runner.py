import json
import os
import shutil

import pytest
import yaml

from eval.mutate import apply_mutations
from eval.run_contracts import (
    ALL_HARNESSES,
    BudgetExceeded,
    REPO,
    SKILL_SRC,
    Outcome,
    enforce_metered_budget,
    install_codex_skill,
    load_contracts,
    select_harnesses,
    select_subject_model,
    subject_environment,
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


def test_contract_rejects_environment_variables_outside_the_capture_allowlist():
    with pytest.raises(ValueError, match="environment"):
        validate_contract(
            {
                "id": "MP-X",
                "name": "unsafe environment",
                "subject": {
                    "fixture": "fixtures/p0-2",
                    "prompt": "x",
                    "environment": {"ANTHROPIC_API_KEY": "do-not-inject"},
                },
                "assert": {"type": "response", "pass": "x"},
                "negative_control": {
                    "mutate": {
                        "file": "SKILL.md",
                        "op": "replace",
                        "pattern": "MiniProject",
                        "value": "LargeProject",
                    }
                },
                "harnesses": list(ALL_HARNESSES),
            }
        )


def test_subject_environment_is_scoped_and_restored(monkeypatch):
    monkeypatch.setenv("MINIPROJECT_REGISTER", "before.jsonl")
    monkeypatch.delenv("MINIPROJECT_SOURCE_SESSION", raising=False)

    with subject_environment(
        {
            "MINIPROJECT_REGISTER": "improvement-register.jsonl",
            "MINIPROJECT_SOURCE_SESSION": "capture-contract-001",
        }
    ):
        assert os.environ["MINIPROJECT_REGISTER"] == "improvement-register.jsonl"
        assert os.environ["MINIPROJECT_SOURCE_SESSION"] == "capture-contract-001"

    assert os.environ["MINIPROJECT_REGISTER"] == "before.jsonl"
    assert "MINIPROJECT_SOURCE_SESSION" not in os.environ


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


def test_every_user_facing_workflow_has_an_exact_plain_language_contract():
    expected = {
        "MP-C09": ({"US-OWN-001"}, "The deterministic validator reported no findings. "),
        "MP-C10": ({"US-OWN-003"}, "VALID — {count} resulting MiniProjects passed validation. "),
        "MP-C11": ({"US-FAC-001"}, "VALID — Tech Refinement resolved {resolved} {noun}. "),
        "MP-C12": ({"US-FAC-002"}, "VALID — Tech Estimation satisfies the measurement rules for every item. "),
        "MP-C13": ({"US-VAL-001"}, "VALID — The Project has explicit in/out scope, {len(ranked)} ranked "),
        "MP-C14": ({"US-REQ-001"}, "CHORE — Route this specific request through the fast lane. "),
    }

    for contract_id, (stories, removed_wording) in expected.items():
        contract = load_contracts(contract_id)[0]
        assert set(contract["stories"]) == stories
        assert contract["assert"]["type"] == "artifact"
        prompt = contract["subject"]["prompt"].lower()
        assert "redirect stdout directly" in prompt
        assert "do not reconstruct" in prompt
        patterns = [
            check["pattern"]
            for check in contract["assert"]["checks"]
            if check["kind"] == "contains"
        ]
        assert patterns
        assert all(
            pattern.startswith(r"\A") and pattern.endswith(r"\n?\Z")
            for pattern in patterns
        )
        mutation = contract["negative_control"]["mutate"]
        assert mutation["pattern"] == removed_wording
        assert mutation["value"] != removed_wording


def test_metered_budget_reserves_room_for_the_next_subject_call(monkeypatch):
    monkeypatch.setattr(
        "eval.run_contracts.totals",
        lambda **_: {"cost_usd": 9.80, "calls": 1, "unpriced_calls": 0},
    )

    with pytest.raises(BudgetExceeded, match=r"\$9\.8000.*\$10\.0000"):
        enforce_metered_budget(
            max_cost_usd=10.0,
            since="2026-08-09T00:00:00Z",
            reserve_usd=0.25,
        )


def test_metered_budget_allows_a_call_with_reserved_room(monkeypatch):
    monkeypatch.setattr(
        "eval.run_contracts.totals",
        lambda **_: {"cost_usd": 9.70, "calls": 1, "unpriced_calls": 0},
    )

    assert enforce_metered_budget(
        max_cost_usd=10.0,
        since="2026-08-09T00:00:00Z",
        reserve_usd=0.25,
    ) == 9.70


def test_codex_skill_is_installed_under_the_disposable_process_home(tmp_path):
    codex_home = tmp_path / ".codex"
    (codex_home / "skills").mkdir(parents=True)

    installed = install_codex_skill(SKILL_SRC, codex_home)

    assert installed == tmp_path / ".agents" / "skills" / "miniproject"
    link = codex_home / "skills" / "miniproject"
    assert link.is_symlink()
    assert link.resolve() == installed.resolve()


def test_behavioral_docs_explain_budget_and_subject_home_isolation():
    text = (REPO / "docs" / "behavioral-testing.md").read_text().lower()
    for required in (
        "--max-metered-cost",
        "--budget-since",
        "junie usage",
        "isolate both `home` and `codex_home`",
    ):
        assert required in text
