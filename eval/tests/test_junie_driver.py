"""Junie command construction and home isolation; no model calls."""
from pathlib import Path
import subprocess

import pytest

from eval.drivers.junie import JunieDriver


@pytest.fixture
def driver(tmp_path):
    return JunieDriver(junie_home=tmp_path / "home", skill_root=tmp_path / "skills")


def test_refuses_the_real_junie_home():
    with pytest.raises(ValueError, match="real ~/.junie"):
        JunieDriver(junie_home=Path.home() / ".junie", skill_root=Path("/tmp/skills"))


def test_isolated_run_requires_explicit_api_key(driver, monkeypatch):
    monkeypatch.delenv("JUNIE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JUNIE_API_KEY"):
        driver.subprocess_env()


def test_environment_redirects_all_junie_state(driver, monkeypatch):
    monkeypatch.setenv("JUNIE_API_KEY", "test-only")
    env = driver.subprocess_env()
    assert env["JUNIE_HOME"] == str(driver.junie_home)
    assert env["JUNIE_LOG_DIR"] == str(driver.junie_home / "logs")


def test_initial_command_disables_default_discovery(driver, tmp_path):
    cmd = driver.build_command(fixture=tmp_path, prompt="one", model="m")
    for flag in (
        "--skill-default-locations=false",
        "--config-default-locations=false",
        "--model-default-locations=false",
        "--mcp-default-locations=false",
        "--command-default-location=false",
        "--agent-default-location=false",
    ):
        assert flag in cmd
    assert "--resume" not in cmd
    assert cmd[cmd.index("--agent-mode") + 1] == "chat"
    assert cmd[-2:] == ["--task", "one"]


def test_resume_targets_recorded_session(driver, tmp_path):
    cmd = driver.build_command(
        fixture=tmp_path, prompt="two", model="m", session_id="session-123",
    )
    assert cmd[cmd.index("--session-id") + 1] == "session-123"
    assert "--resume" in cmd


def test_stream_parser_extracts_result_and_rejectable_errors():
    parsed = JunieDriver.parse_stream("\n".join([
        '{"type":"session","sessionId":"session-123"}',
        '{"type":"step","name":"Read skill","details":"mp-classify"}',
        '{"type":"result","result":"MiniProject"}',
        '{"type":"error","message":"auth missing"}',
    ]))
    assert parsed["session_id"] == "session-123"
    assert parsed["final_message"] == "MiniProject"
    assert parsed["diagnostics"] == [{"name": "Read skill", "details": "mp-classify"}]
    assert parsed["errors"] == ["auth missing"]


def test_stream_parser_extracts_provider_usage_rows():
    parsed = JunieDriver.parse_stream(
        '{"type":"result","result":"ok","errorCode":['
        '{"model":"gpt-5.6-luna","calls":2,"cost":0.004,'
        '"inputTokens":10,"cacheInputTokens":100,"cacheCreateTokens":20,'
        '"outputTokens":30}]}'
    )
    assert parsed["usage_rows"] == [
        {
            "model": "gpt-5.6-luna",
            "calls": 2,
            "cost": 0.004,
            "input_tokens": 130,
            "cached_input_tokens": 100,
            "output_tokens": 30,
        }
    ]


def test_single_turn_subject_returns_harness_agnostic_result(
    driver, monkeypatch, tmp_path
):
    monkeypatch.setenv("JUNIE_API_KEY", "test-only")
    stream = "\x1b[1mTASK RESULT\x1b[0m\n\x1b[38;5;247mChore fast lane\x1b[0m\n"
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stream, ""),
    )

    result = driver.run_subject(
        fixture=tmp_path,
        prompt="classify",
        model="gpt-5.6-luna",
        writable=False,
        timeout_s=30,
    )

    assert result.final_message == "Chore fast lane"
    assert result.session_id is None
    assert result.exit_code == 0
    assert result.model == "gpt-5.6-luna"


def test_single_turn_command_uses_scoreable_text_output(driver, tmp_path):
    cmd = driver.build_subject_command(
        fixture=tmp_path, prompt="classify", model="m"
    )
    assert cmd[cmd.index("--output-format") + 1] == "text"


def test_text_parser_returns_only_the_task_result():
    stream = (
        "Authenticated successfully\n"
        "\x1b[1mRead skill\x1b[0m\nminiproject\n"
        "\x1b[1mTASK RESULT\x1b[0m\n"
        "\x1b[38;5;247m### Summary\x1b[0m\n"
        "\x1b[38;5;247m- Chore fast lane\x1b[0m\n"
    )
    assert JunieDriver.parse_text_result(stream) == "### Summary\n- Chore fast lane"
