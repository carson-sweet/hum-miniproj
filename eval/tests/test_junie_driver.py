"""Junie command construction and home isolation; no model calls."""
from pathlib import Path

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
