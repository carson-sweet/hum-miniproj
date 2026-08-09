import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "miniproject" / "scripts"
ANALYZE = SCRIPTS / "analyze_improvements.py"
PROPOSE = SCRIPTS / "propose_improvement.py"
APPROVE = SCRIPTS / "record_improvement_approval.py"
VERSION = SCRIPTS / "record_instruction_version.py"
VALIDATE = SCRIPTS / "validate_improvement_cycle.py"
SEED = REPO / "skills" / "miniproject" / "references" / "improvement-seed.jsonl"
ORACLE = REPO / "eval" / "fixtures" / "improvement-seed-clusters.json"


def run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pattern_detector_recovers_withheld_seed_clusters(tmp_path):
    raw_entries = [json.loads(line) for line in SEED.read_text().splitlines() if line.strip()]
    assert all("cluster" not in entry for entry in raw_entries)
    output = tmp_path / "analysis.json"

    result = run(
        ANALYZE,
        "--register",
        SEED,
        "--output",
        output,
        "--min-occurrences",
        "2",
    )

    assert result.returncode == 0, result.stderr
    actual = {
        pattern["pattern_id"]: sorted(pattern["entry_ids"])
        for pattern in json.loads(output.read_text())["patterns"]
    }
    expected = json.loads(ORACLE.read_text())["clusters"]
    assert actual == expected


def test_proposal_is_a_reversible_diff_and_never_mutates_instruction(tmp_path):
    analysis = tmp_path / "analysis.json"
    instruction = tmp_path / "SKILL.md"
    candidate = tmp_path / "candidate.md"
    proposal = tmp_path / "proposal.json"
    instruction.write_text("Keep technical-layer bundles.\n")
    candidate.write_text("Reject technical-layer-only bundles.\n")
    original = instruction.read_bytes()
    write_json(
        analysis,
        {
            "schema_version": 1,
            "patterns": [
                {
                    "pattern_id": "pattern-correction-skill",
                    "type": "correction",
                    "target": "SKILL.md",
                    "count": 2,
                    "weight": 2.0,
                    "entry_ids": ["lr-1", "lr-2"],
                    "learnings": ["Reject technical layers", "Bundle end to end"],
                }
            ],
        },
    )

    result = run(
        PROPOSE,
        "--analysis",
        analysis,
        "--pattern-id",
        "pattern-correction-skill",
        "--target",
        "SKILL.md",
        "--instruction",
        instruction,
        "--candidate",
        candidate,
        "--output",
        proposal,
    )

    assert result.returncode == 0, result.stderr
    assert instruction.read_bytes() == original
    data = json.loads(proposal.read_text())
    assert data["status"] == "proposed"
    assert data["base_sha256"] == hashlib.sha256(original).hexdigest()
    assert data["candidate_sha256"] == sha256(candidate)
    assert "-Keep technical-layer bundles." in data["diff"]
    assert "+Reject technical-layer-only bundles." in data["diff"]
    assert data["reverse_diff"]


def make_cycle(tmp_path: Path, *, production_outcome: bool = True) -> tuple[Path, dict]:
    instruction = tmp_path / "SKILL.md"
    candidate = tmp_path / "candidate.md"
    instruction.write_text("Keep technical-layer bundles.\n")
    candidate.write_text("Reject technical-layer-only bundles.\n")
    analysis = tmp_path / "analysis.json"
    write_json(
        analysis,
        {
            "schema_version": 1,
            "patterns": [
                {
                    "pattern_id": "pattern-correction-skill",
                    "type": "correction",
                    "target": "SKILL.md",
                    "count": 2,
                    "weight": 2.0,
                    "entry_ids": ["lr-1", "lr-2"],
                    "learnings": ["Reject technical layers", "Bundle end to end"],
                }
            ],
        },
    )
    proposal = tmp_path / "proposal.json"
    proposed = run(
        PROPOSE,
        "--analysis",
        analysis,
        "--pattern-id",
        "pattern-correction-skill",
        "--target",
        "SKILL.md",
        "--instruction",
        instruction,
        "--candidate",
        candidate,
        "--output",
        proposal,
    )
    assert proposed.returncode == 0, proposed.stderr
    proposal_data = json.loads(proposal.read_text())

    approval = tmp_path / "approval.json"
    approved = run(
        APPROVE,
        "--proposal",
        proposal,
        "--decision",
        "approved",
        "--approved-by",
        "Human Owner",
        "--human-confirmed",
        "--output",
        approval,
    )
    assert approved.returncode == 0, approved.stderr

    contract = tmp_path / "target-contract.json"
    write_json(
        contract,
        {
            "id": "MP-IMPROVEMENT-001",
            "assert": {
                "type": "artifact" if production_outcome else "response",
                "checks": [{"kind": "exists", "path": "result.json"}],
            },
            "negative_control": {
                "expect": "FAIL",
                "mutate": {
                    "file": "SKILL.md",
                    "op": "replace",
                    "pattern": "Reject technical-layer-only bundles.",
                    "value": "Keep technical-layer bundles.",
                },
            },
        },
    )
    scores = {
        "targeted": {"before": {"passed": 3, "total": 5}, "after": {"passed": 5, "total": 5}},
        "held_out": {"before": {"passed": 8, "total": 10}, "after": {"passed": 9, "total": 10}},
    }
    version = tmp_path / "instruction-version.json"
    write_json(
        version,
        {
            "schema_version": 1,
            "version_id": "skill-v2",
            "target": "SKILL.md",
            "content_sha256": proposal_data["candidate_sha256"],
            "previous_content_sha256": proposal_data["base_sha256"],
            "scores": scores,
        },
    )
    cycle = tmp_path / "cycle.json"
    cycle_data = {
        "schema_version": 1,
        "cycle_id": "cycle-001",
        "proposal": proposal.name,
        "approval": approval.name,
        "contract": contract.name,
        "instruction_version": version.name,
        "production_outcome": production_outcome,
        "scores": scores,
    }
    write_json(cycle, cycle_data)
    return cycle, cycle_data


def test_approval_recorder_requires_explicit_human_confirmation(tmp_path):
    cycle, cycle_data = make_cycle(tmp_path)
    proposal = tmp_path / cycle_data["proposal"]
    output = tmp_path / "unconfirmed-approval.json"

    result = run(
        APPROVE,
        "--proposal",
        proposal,
        "--decision",
        "approved",
        "--approved-by",
        "Human Owner",
        "--output",
        output,
    )

    assert result.returncode == 2
    assert not output.exists()
    assert "explicit human approval" in result.stderr.lower()


def test_instruction_version_recorder_carries_scores_and_revert_binding(tmp_path):
    cycle, cycle_data = make_cycle(tmp_path)
    proposal = tmp_path / cycle_data["proposal"]
    output = tmp_path / "recorded-version.json"

    result = run(
        VERSION,
        "--proposal",
        proposal,
        "--version-id",
        "skill-v2-recorded",
        "--targeted-before",
        "3/5",
        "--targeted-after",
        "5/5",
        "--held-out-before",
        "8/10",
        "--held-out-after",
        "9/10",
        "--output",
        output,
    )

    assert result.returncode == 0, result.stderr
    proposal_data = json.loads(proposal.read_text())
    version = json.loads(output.read_text())
    assert version["content_sha256"] == proposal_data["candidate_sha256"]
    assert version["previous_content_sha256"] == proposal_data["base_sha256"]
    assert version["scores"] == cycle_data["scores"]


def validate_cycle(tmp_path: Path, cycle: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    output = tmp_path / "cycle-result.json"
    result = run(VALIDATE, "--cycle", cycle, "--output", output)
    return result, json.loads(output.read_text())


def test_complete_approved_cycle_passes_with_target_gain_and_no_held_out_regression(tmp_path):
    cycle, _ = make_cycle(tmp_path)

    result, verdict = validate_cycle(tmp_path, cycle)

    assert result.returncode == 0, result.stderr
    assert verdict["status"] == "valid"
    assert verdict["findings"] == []


def test_cycle_fails_closed_without_matching_human_approval(tmp_path):
    cycle, cycle_data = make_cycle(tmp_path)
    cycle_data["approval"] = "missing-approval.json"
    write_json(cycle, cycle_data)

    result, verdict = validate_cycle(tmp_path, cycle)

    assert result.returncode == 1
    assert verdict["status"] == "invalid"
    assert "approval" in {finding["criterion"] for finding in verdict["findings"]}


def test_cycle_rejects_held_out_regression(tmp_path):
    cycle, cycle_data = make_cycle(tmp_path)
    cycle_data["scores"]["held_out"]["after"] = {"passed": 7, "total": 10}
    write_json(cycle, cycle_data)
    version = tmp_path / cycle_data["instruction_version"]
    version_data = json.loads(version.read_text())
    version_data["scores"] = cycle_data["scores"]
    write_json(version, version_data)

    result, verdict = validate_cycle(tmp_path, cycle)

    assert result.returncode == 1
    assert any(finding["code"] == "held-out-regression" for finding in verdict["findings"])


def test_production_outcome_requires_an_artifact_contract(tmp_path):
    cycle, _ = make_cycle(tmp_path, production_outcome=False)
    cycle_data = json.loads(cycle.read_text())
    cycle_data["production_outcome"] = True
    write_json(cycle, cycle_data)

    result, verdict = validate_cycle(tmp_path, cycle)

    assert result.returncode == 1
    assert any(finding["code"] == "artifact-contract-required" for finding in verdict["findings"])


def test_cycle_rejects_stale_or_unbound_version_metadata(tmp_path):
    cycle, cycle_data = make_cycle(tmp_path)
    version = tmp_path / cycle_data["instruction_version"]
    version_data = json.loads(version.read_text())
    version_data["previous_content_sha256"] = "0" * 64
    write_json(version, version_data)

    result, verdict = validate_cycle(tmp_path, cycle)

    assert result.returncode == 1
    assert any(finding["code"] == "version-hash-mismatch" for finding in verdict["findings"])


def test_committed_fixed_cycle_fixture_matches_the_validator_oracle(tmp_path):
    cycle = REPO / "fixtures" / "improvement-loop" / "fixed-cycle" / "cycle.json"
    output = tmp_path / "result.json"

    result = run(VALIDATE, "--cycle", cycle, "--output", output)

    assert result.returncode == 0, result.stderr
    verdict = json.loads(output.read_text())
    assert verdict == {
        "checked": ["proposal", "approval", "contract", "scores", "instruction_version"],
        "cycle_id": "cycle-fixed-001",
        "findings": [],
        "schema_version": 1,
        "status": "valid",
    }
