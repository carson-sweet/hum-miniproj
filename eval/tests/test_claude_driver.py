import json
from pathlib import Path

import pytest

from eval.drivers.claude import ClaudeDriver


@pytest.fixture
def driver(tmp_path):
    skill = tmp_path / "skills" / "miniproject"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: miniproject\n---\n")
    return ClaudeDriver(skill_dir=skill)


def test_container_command_mounts_only_fixture_and_skill(driver, tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    cmd = driver.build_subject_command(
        fixture=fixture,
        prompt="classify this",
        model="haiku",
        writable=False,
    )

    assert cmd[:3] == ["docker", "run", "--rm"]
    joined = " ".join(cmd)
    assert f"{fixture.resolve()}:/workspace:ro" in joined
    assert f"{driver.skill_dir.resolve()}:/root/.claude/skills/miniproject:ro" in joined
    assert str(Path.home() / ".claude") not in joined
    assert "--no-session-persistence" in cmd
    assert "CLAUDE_CODE_OAUTH_TOKEN" in cmd


def test_writable_subject_only_changes_the_fixture_mount(driver, tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    cmd = driver.build_subject_command(
        fixture=fixture, prompt="write it", model="haiku", writable=True,
    )
    assert f"{fixture.resolve()}:/workspace:rw" in " ".join(cmd)
    assert f"{driver.skill_dir.resolve()}:/root/.claude/skills/miniproject:ro" in " ".join(cmd)


def test_container_command_passes_capture_environment(driver, tmp_path, monkeypatch):
    monkeypatch.setenv("MINIPROJECT_REGISTER", "improvement-register.jsonl")
    monkeypatch.setenv("MINIPROJECT_SOURCE_SESSION", "capture-contract-001")
    fixture = tmp_path / "fixture"
    fixture.mkdir()

    cmd = driver.build_subject_command(
        fixture=fixture, prompt="capture it", model="haiku", writable=True,
    )

    assert "MINIPROJECT_REGISTER" in cmd
    assert "MINIPROJECT_SOURCE_SESSION" in cmd


def test_driver_requires_process_only_oauth_token(driver, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="CLAUDE_CODE_OAUTH_TOKEN"):
        driver.subprocess_env()


def test_result_parser_extracts_message_model_session_and_usage(driver):
    raw = json.dumps(
        {
            "result": "Chore fast lane",
            "session_id": "session-1",
            "usage": {
                "input_tokens": 10,
                "cache_read_input_tokens": 100,
                "cache_creation_input_tokens": 20,
                "output_tokens": 5,
            },
            "modelUsage": {
                "claude-haiku-4-5-20251001": {
                    "canonicalModel": "claude-haiku-4-5",
                    "inputTokens": 10,
                    "cacheReadInputTokens": 100,
                    "cacheCreationInputTokens": 20,
                    "outputTokens": 5,
                    "costUSD": 0.0123,
                }
            },
        }
    )

    parsed = driver.parse_result(raw, requested_model="haiku")

    assert parsed["final_message"] == "Chore fast lane"
    assert parsed["session_id"] == "session-1"
    assert parsed["model"] == "claude-haiku-4-5"
    assert parsed["usage"].input_tokens == 130
    assert parsed["usage"].cached_input_tokens == 100
    assert parsed["usage"].output_tokens == 5
    assert parsed["usage_rows"] == [
        {
            "model": "claude-haiku-4-5",
            "usage": parsed["usage"],
            "cost": 0.0123,
        }
    ]


def test_result_parser_rejects_non_json(driver):
    with pytest.raises(ValueError, match="valid JSON"):
        driver.parse_result("not-json", requested_model="haiku")
