import os

import pytest

from eval.env import load_local_value


def private_env_file(tmp_path, text: str):
    path = tmp_path / ".env.local"
    path.write_text(text)
    path.chmod(0o600)
    return path


def test_loads_only_requested_value(tmp_path, monkeypatch):
    monkeypatch.delenv("JUNIE_API_KEY", raising=False)
    path = private_env_file(tmp_path, "OTHER=ignored\nJUNIE_API_KEY='junie-test'\n")
    assert load_local_value(path, "JUNIE_API_KEY")
    assert os.environ["JUNIE_API_KEY"] == "junie-test"
    assert "OTHER" not in os.environ


def test_exported_value_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("JUNIE_API_KEY", "already-set")
    path = private_env_file(tmp_path, "JUNIE_API_KEY=from-file\n")
    assert not load_local_value(path, "JUNIE_API_KEY")
    assert os.environ["JUNIE_API_KEY"] == "already-set"


def test_blank_or_missing_value_is_not_loaded(tmp_path, monkeypatch):
    monkeypatch.delenv("JUNIE_API_KEY", raising=False)
    assert not load_local_value(tmp_path / "missing", "JUNIE_API_KEY")
    assert not load_local_value(
        private_env_file(tmp_path, "JUNIE_API_KEY=\n"), "JUNIE_API_KEY",
    )


def test_rejects_group_or_world_readable_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("JUNIE_API_KEY", raising=False)
    path = private_env_file(tmp_path, "JUNIE_API_KEY=secret\n")
    path.chmod(0o644)
    with pytest.raises(PermissionError, match="chmod 600"):
        load_local_value(path, "JUNIE_API_KEY")
