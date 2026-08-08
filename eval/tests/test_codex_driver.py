"""Step 1 gate: probe() green, and the command carries the isolation flags.

Command construction is a pure function so the isolation guarantees from
docs/eval-codex-driver.md are assertable without spending a model call. Every
flag checked here is load-bearing; if one silently disappears, a result stops
meaning what the design says it means.
"""
import shutil
from pathlib import Path

import pytest

from eval.config import SUBJECT_MODEL
from eval.drivers.codex import CodexDriver


@pytest.fixture
def driver():
    return CodexDriver()


def cmd_for(driver, **kw):
    kw.setdefault("fixture", Path("/tmp/fx"))
    kw.setdefault("prompt", "do the thing")
    kw.setdefault("model", "gpt-5.6-sol")
    kw.setdefault("out_file", Path("/tmp/out.txt"))
    kw.setdefault("writable", False)
    return driver.build_subject_command(**kw)


def test_probe_reports_binary_and_version(driver):
    if shutil.which("codex") is None:
        pytest.skip("codex CLI not installed on this machine")
    result = driver.probe()
    assert result.ok, result.detail
    assert result.harness == "codex"
    assert result.version, "probe must capture a version for attribution"


def test_probe_reports_not_ok_when_binary_missing(driver, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    result = driver.probe()
    assert not result.ok
    assert "not found" in result.detail.lower()


def test_command_uses_exec_subcommand(driver):
    cmd = cmd_for(driver)
    assert cmd[0] == "codex"
    assert cmd[1] == "exec"


@pytest.mark.parametrize(
    "flag",
    ["--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check"],
)
def test_command_carries_isolation_flags(driver, flag):
    """Each flag maps to a stated isolation guarantee in the design doc."""
    assert flag in cmd_for(driver)


def test_command_defaults_to_read_only_sandbox(driver):
    cmd = cmd_for(driver, writable=False)
    assert "-s" in cmd
    assert cmd[cmd.index("-s") + 1] == "read-only"


def test_command_uses_workspace_write_when_artifacts_expected(driver):
    cmd = cmd_for(driver, writable=True)
    assert cmd[cmd.index("-s") + 1] == "workspace-write"


def test_command_pins_model(driver):
    """Literal on purpose: pinning must work for any model, not just the configured one."""
    cmd = cmd_for(driver, model="gpt-5.6-sol")
    assert cmd[cmd.index("-m") + 1] == "gpt-5.6-sol"


def test_command_scopes_working_root_to_fixture(driver):
    cmd = cmd_for(driver, fixture=Path("/tmp/fx"))
    assert cmd[cmd.index("-C") + 1] == "/tmp/fx"


def test_command_writes_final_message_to_file(driver):
    """Gotcha 2: the banner goes to stdout, the answer goes to -o."""
    cmd = cmd_for(driver, out_file=Path("/tmp/out.txt"))
    assert cmd[cmd.index("-o") + 1] == "/tmp/out.txt"


def test_command_disables_color(driver):
    assert cmd_for(driver)[cmd_for(driver).index("--color") + 1] == "never"


def test_prompt_is_last_argument(driver):
    assert cmd_for(driver, prompt="do the thing")[-1] == "do the thing"


def test_header_parsing_extracts_model_and_session():
    stdout = (
        "OpenAI Codex v0.145.0\n"
        "--------\n"
        "workdir: /tmp/fx\n"
        "model: gpt-5.6-sol\n"
        "provider: openai\n"
        "session id: 019fe178-a4a0-7280-a510-877788b6980e\n"
        "--------\n"
    )
    meta = CodexDriver.parse_header(stdout)
    assert meta["model"] == "gpt-5.6-sol"
    assert meta["session_id"] == "019fe178-a4a0-7280-a510-877788b6980e"


def test_header_parsing_survives_missing_fields():
    meta = CodexDriver.parse_header("no banner here")
    assert meta["model"] is None
    assert meta["session_id"] is None


@pytest.mark.integration
def test_subject_runs_and_writes_an_artifact(tmp_path):
    """End-to-end: a real subject writes a real file into a disposable workdir."""
    driver = CodexDriver()
    fixture = tmp_path / "fx"
    fixture.mkdir()
    (fixture / "notes.md").write_text("Open question: aggregate or per-segment?\n")

    result = driver.run_subject(
        fixture=fixture,
        prompt="Create a file named bundle.md in the working directory containing a '## Owner' heading.",
        model=SUBJECT_MODEL,
        writable=True,
        timeout_s=180,
    )

    assert result.exit_code == 0, result.stdout[-2000:]
    assert (fixture / "bundle.md").exists(), "subject did not produce the artifact"
    # session_id has no fallback, so it is the only field that actually proves the
    # banner was parsed. `model` falls back to the parameter and cannot fail here.
    assert result.session_id, "session id must be captured for attribution"
    assert result.model, "model must be captured for attribution"


def test_events_parsing_extracts_thread_id():
    """--json swaps the streams: stdout becomes JSONL and neither stream has a banner."""
    jsonl = (
        '{"type":"thread.started","thread_id":"019fe18b-e8a9-73e1-8d76-23de766d48c4"}\n'
        '{"type":"turn.started"}\n'
        '{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"ok"}}\n'
    )
    assert CodexDriver.parse_events(jsonl) == "019fe18b-e8a9-73e1-8d76-23de766d48c4"


def test_events_parsing_returns_none_on_banner_output():
    assert CodexDriver.parse_events("OpenAI Codex v0.145.0\nmodel: gpt-5.6-sol\n") is None


def test_events_parsing_survives_malformed_lines():
    assert CodexDriver.parse_events('{not json\n{"type":"thread.started","thread_id":"x"}\n') == "x"


def test_command_always_requests_json(driver, tmp_path):
    """--json is not optional: turn.completed carries the usage that meters the call.

    Replaces an earlier test asserting --json appeared only with events_file. That
    behaviour changed deliberately when token accounting was added; an unmetered
    call is now a defect, not a configuration.
    """
    assert "--json" in cmd_for(driver)
    assert "--json" in cmd_for(driver, events_file=tmp_path / "events.jsonl")


@pytest.mark.integration
def test_attribution_survives_json_mode(tmp_path):
    """The regression this path had no coverage for: --json removes the banner,
    so header parsing yields nothing and attribution must come from the events."""
    driver = CodexDriver()
    fixture = tmp_path / "fx"
    fixture.mkdir()
    events = tmp_path / "events.jsonl"

    result = driver.run_subject(
        fixture=fixture,
        prompt="Reply with the single word: ok",
        model=SUBJECT_MODEL,
        writable=False,
        timeout_s=120,
        events_file=events,
    )

    assert result.exit_code == 0, result.stdout[-2000:]
    assert result.session_id, "attribution lost in --json mode"
    assert events.exists() and events.read_text().strip(), "event stream not captured"
