from pathlib import Path
import re

import yaml


REPO = Path(__file__).resolve().parents[2]
STORIES = REPO / "docs" / "product" / "hum-miniproj-user-stories-draft-v1.0-20260808.md"
COVERAGE = REPO / "eval" / "user_story_coverage.yaml"


def test_every_user_story_has_implementation_and_executable_acceptance_coverage():
    story_ids = set(re.findall(r"^### (US-[A-Z]+-\d+):", STORIES.read_text(), re.MULTILINE))
    coverage = yaml.safe_load(COVERAGE.read_text())

    assert set(coverage) == story_ids
    for story_id, record in coverage.items():
        assert record["status"] == "implemented", story_id
        assert record["implementation"], story_id
        assert record["acceptance_tests"], story_id
        for rel in record["implementation"] + record["acceptance_tests"]:
            assert (REPO / rel).is_file(), f"{story_id}: missing {rel}"
