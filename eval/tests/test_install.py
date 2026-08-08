from pathlib import Path
import subprocess

from scripts.lint_portable import lint_skill


REPO = Path(__file__).resolve().parents[2]
INSTALLER = REPO / "install.sh"
SKILL_NAME = "miniproject"


def run_installer(home: Path, *args: str):
    return subprocess.run(
        ["bash", str(INSTALLER), "--home", str(home), *args],
        cwd=REPO,
        text=True,
        capture_output=True,
    )


def installed_paths(home: Path):
    canonical = home / ".agents" / "skills" / SKILL_NAME
    links = [
        home / ".codex" / "skills" / SKILL_NAME,
        home / ".junie" / "skills" / SKILL_NAME,
        home / ".claude" / "skills" / SKILL_NAME,
    ]
    return canonical, links


def test_install_creates_canonical_copy_and_three_harness_links(tmp_path):
    home = tmp_path / "home"

    result = run_installer(home)

    assert result.returncode == 0, result.stderr
    canonical, links = installed_paths(home)
    assert (canonical / "SKILL.md").read_text() == (
        REPO / "skills" / SKILL_NAME / "SKILL.md"
    ).read_text()
    assert lint_skill(canonical) == [], "installed copy must preserve the portable subset"
    for link in links:
        assert link.is_symlink(), f"missing harness link: {link}"
        assert link.resolve() == canonical.resolve()


def test_install_is_idempotent(tmp_path):
    home = tmp_path / "home"
    first = run_installer(home)
    second = run_installer(home)

    assert first.returncode == second.returncode == 0
    canonical, links = installed_paths(home)
    assert canonical.is_dir()
    assert all(link.is_symlink() for link in links)


def test_uninstall_removes_only_owned_skill_paths(tmp_path):
    home = tmp_path / "home"
    assert run_installer(home).returncode == 0
    unrelated = home / ".agents" / "skills" / "keep-me"
    unrelated.mkdir(parents=True)

    result = run_installer(home, "--uninstall")

    assert result.returncode == 0, result.stderr
    canonical, links = installed_paths(home)
    assert not canonical.exists()
    assert all(not link.exists() and not link.is_symlink() for link in links)
    assert unrelated.is_dir()


def test_refuses_unowned_canonical_directory(tmp_path):
    home = tmp_path / "home"
    canonical, _ = installed_paths(home)
    canonical.mkdir(parents=True)
    user_file = canonical / "user.txt"
    user_file.write_text("preserve me\n")

    result = run_installer(home)

    assert result.returncode == 2
    assert user_file.read_text() == "preserve me\n"


def test_refuses_harness_collision_before_writing_anything(tmp_path):
    home = tmp_path / "home"
    canonical, links = installed_paths(home)
    collision = links[0]
    collision.mkdir(parents=True)
    user_file = collision / "user.txt"
    user_file.write_text("preserve me\n")

    result = run_installer(home)

    assert result.returncode == 2
    assert user_file.read_text() == "preserve me\n"
    assert not canonical.exists(), "preflight must finish before installation writes"
