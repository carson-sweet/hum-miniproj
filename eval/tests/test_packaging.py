from pathlib import Path
import tomllib


REPO = Path(__file__).resolve().parents[2]


def test_editable_install_has_an_explicit_package_boundary():
    config = tomllib.loads((REPO / "pyproject.toml").read_text())
    discovery = config["tool"]["setuptools"]["packages"]["find"]

    assert discovery["include"] == ["eval*"]
