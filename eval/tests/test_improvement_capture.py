import json
import ast
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "miniproject" / "scripts"
APPEND = SCRIPTS / "register_append.py"
VERIFY = SCRIPTS / "register_verify.py"
SEED = REPO / "skills" / "miniproject" / "references" / "improvement-seed.jsonl"


def run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
    )


def test_append_writes_one_schema_valid_live_entry(tmp_path):
    register = tmp_path / "register.jsonl"

    result = run(
        APPEND,
        "--register",
        register,
        "--type",
        "correction",
        "--learning",
        "Technical-layer bundles must be rejected.",
        "--harness",
        "codex",
        "--skill",
        "skills/miniproject/SKILL.md",
        "--source-session",
        "session-live-001",
        "--weight",
        "2",
    )

    assert result.returncode == 0, result.stderr
    entries = [json.loads(line) for line in register.read_text().splitlines()]
    assert len(entries) == 1
    entry = entries[0]
    assert set(entry) == {
        "id",
        "date",
        "harness",
        "skill",
        "type",
        "learning",
        "source_session",
        "weight",
    }
    assert entry["id"].startswith("lr-")
    assert entry["date"] == entry["date"][:10]
    assert entry["source_session"] == "session-live-001"
    assert entry["weight"] == 2.0


def test_append_rejects_invalid_input_without_touching_register(tmp_path):
    register = tmp_path / "register.jsonl"
    original = '{"not":"a valid register entry"}\n'
    register.write_text(original)

    result = run(
        APPEND,
        "--register",
        register,
        "--type",
        "confirmation",
        "--learning",
        "A valid-looking new learning",
        "--harness",
        "junie",
        "--skill",
        "skills/miniproject/SKILL.md",
        "--source-session",
        "session-live-002",
    )

    assert result.returncode == 2
    assert "invalid existing register" in result.stderr.lower()
    assert register.read_text() == original


def test_verify_requires_an_entry_from_the_current_session(tmp_path):
    register = tmp_path / "register.jsonl"
    appended = run(
        APPEND,
        "--register",
        register,
        "--type",
        "confirmation",
        "--learning",
        "The workflow completed successfully.",
        "--harness",
        "claude",
        "--skill",
        "skills/miniproject/SKILL.md",
        "--source-session",
        "an-earlier-session",
    )
    assert appended.returncode == 0, appended.stderr

    stale = run(
        VERIFY,
        "--register",
        register,
        "--source-session",
        "current-session",
    )
    current = run(
        VERIFY,
        "--register",
        register,
        "--source-session",
        "an-earlier-session",
        "--require-live",
    )

    assert stale.returncode == 1
    assert "current-session" in stale.stderr
    assert current.returncode == 0, current.stderr


def test_seed_import_uses_the_single_register_writer_and_does_not_count_as_live(tmp_path):
    register = tmp_path / "register.jsonl"

    imported = run(APPEND, "--register", register, "--import-seed", SEED)
    assert imported.returncode == 0, imported.stderr
    entries = [json.loads(line) for line in register.read_text().splitlines()]
    assert len(entries) >= 6
    assert all(entry["source_session"].startswith("seed:") for entry in entries)

    valid_register = run(VERIFY, "--register", register)
    live_register = run(VERIFY, "--register", register, "--require-live")
    assert valid_register.returncode == 0, valid_register.stderr
    assert live_register.returncode == 1
    assert "live" in live_register.stderr.lower()


def test_seed_import_ignores_a_live_session_environment_default(tmp_path):
    register = tmp_path / "register.jsonl"
    environment = os.environ.copy()
    environment["MINIPROJECT_SOURCE_SESSION"] = "live-session-from-harness"

    result = subprocess.run(
        [sys.executable, str(APPEND), "--register", str(register), "--import-seed", str(SEED)],
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert len(register.read_text().splitlines()) >= 6


def test_register_schema_names_append_as_its_only_writer():
    schema = json.loads(
        (REPO / "skills" / "miniproject" / "references" / "improvement-register.schema.json").read_text()
    )

    assert schema["x-writer"] == "scripts/register_append.py"
    assert schema["additionalProperties"] is False


def test_no_other_skill_script_opens_a_file_in_append_mode():
    append_mode_scripts = set()
    for path in SCRIPTS.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            mode = None
            if isinstance(node.func, ast.Attribute) and node.func.attr == "open" and node.args:
                mode = node.args[0]
            elif isinstance(node.func, ast.Name) and node.func.id == "open":
                if len(node.args) > 1:
                    mode = node.args[1]
                for keyword in node.keywords:
                    if keyword.arg == "mode":
                        mode = keyword.value
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and "a" in mode.value:
                append_mode_scripts.add(path.name)

    assert append_mode_scripts == {"register_append.py"}
