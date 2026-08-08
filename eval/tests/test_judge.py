"""Step 2 gate: the judge returns valid JSON on a hand-written pair.

The judge runs in an EMPTY working directory. A judge that can read the skill it
grades against credits intent instead of behavior, so the isolation is enforced
by the command, not by asking the model nicely.
"""
import json
from pathlib import Path

import pytest

from eval.judge import (
    Verdict,
    build_judge_command,
    load_verdict_schema,
    parse_verdict,
    render_judge_prompt,
)


def test_verdict_schema_file_is_valid_json_and_constrains_verdict():
    schema = load_verdict_schema()
    assert schema["required"] == ["verdict", "reason"]
    assert schema["properties"]["verdict"]["enum"] == ["PASS", "FAIL"]
    assert schema["additionalProperties"] is False


def test_parse_verdict_accepts_a_well_formed_pass():
    v = parse_verdict('{"verdict":"PASS","reason":"proposes a name with a reason"}')
    assert v == Verdict(verdict="PASS", reason="proposes a name with a reason")
    assert v.passed


def test_parse_verdict_accepts_a_well_formed_fail():
    assert not parse_verdict('{"verdict":"FAIL","reason":"asked an open question"}').passed


def test_parse_verdict_rejects_non_json():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_verdict("Sure! The verdict is PASS.")


def test_parse_verdict_rejects_missing_field():
    with pytest.raises(ValueError, match="missing required field"):
        parse_verdict('{"verdict":"PASS"}')


def test_parse_verdict_rejects_unknown_verdict_value():
    with pytest.raises(ValueError, match="not a valid verdict"):
        parse_verdict('{"verdict":"MAYBE","reason":"unsure"}')


def test_parse_verdict_tolerates_surrounding_whitespace():
    assert parse_verdict('  {"verdict":"PASS","reason":"ok"}\n').passed


def test_judge_command_uses_an_empty_read_only_workdir(tmp_path):
    cmd = build_judge_command(
        workdir=tmp_path, prompt="criterion...", model="gpt-5.6-sol",
        schema_path=Path("/tmp/verdict.schema.json"), out_file=Path("/tmp/v.json"),
    )
    assert cmd[cmd.index("-s") + 1] == "read-only", "judge must never write"
    assert cmd[cmd.index("-C") + 1] == str(tmp_path)
    assert cmd[cmd.index("--output-schema") + 1] == "/tmp/verdict.schema.json"


def test_judge_command_carries_isolation_flags(tmp_path):
    cmd = build_judge_command(
        workdir=tmp_path, prompt="c", model="m",
        schema_path=Path("/s.json"), out_file=Path("/o.json"),
    )
    for flag in ("--ephemeral", "--ignore-user-config", "--skip-git-repo-check"):
        assert flag in cmd


def test_judge_prompt_contains_criterion_and_output_but_not_the_skill():
    prompt = render_judge_prompt(
        criterion="Gives a time-box, contains no effort estimate.",
        subject_output="I'd time-box this to one day.",
    )
    assert "Gives a time-box" in prompt
    assert "I'd time-box this to one day." in prompt
    assert "SKILL.md" not in prompt


@pytest.mark.integration
def test_judge_returns_pass_on_a_matching_pair():
    from eval.judge import judge

    v = judge(
        criterion="Does the text propose a specific answer with a reason, rather than asking an open question?",
        subject_output="I'd suggest naming it users, because it is the plural of the entity it holds.",
        model="gpt-5.6-sol",
        timeout_s=120,
    )
    assert v.passed, v.reason


@pytest.mark.integration
def test_judge_returns_fail_on_a_non_matching_pair():
    """The negative half. A judge that only ever returns PASS is measuring nothing."""
    from eval.judge import judge

    v = judge(
        criterion="Does the text propose a specific answer with a reason, rather than asking an open question?",
        subject_output="What do you think we should call it? I'm open to suggestions.",
        model="gpt-5.6-sol",
        timeout_s=120,
    )
    assert not v.passed, v.reason
