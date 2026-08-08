#!/usr/bin/env python3
"""Reject constructs that tie the MiniProject skill to one agent harness."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PORTABLE_ROOTS = {"references", "scripts"}
COMPATIBLE_LICENSES = {
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "ISC",
    "MIT",
}


@dataclass(frozen=True, order=True)
class Violation:
    path: str
    line: int
    code: str
    message: str


LINE_RULES = (
    (
        "bang-preamble",
        re.compile(r"^\s*!(?!\[)"),
        "bang preambles are harness-specific",
    ),
    (
        "plugin-root",
        re.compile(r"\$\{?[A-Z][A-Z0-9_]*PLUGIN_ROOT\}?"),
        "plugin-root variables are harness-specific",
    ),
    (
        "interactive-tool",
        re.compile(r"\b(?:AskUserQuestion|ask_user_question|request_user_input)\b", re.I),
        "interactive-question tools are not portable",
    ),
    (
        "cross-skill",
        re.compile(
            r"\b(?i:call|invoke|run|use)\s+(?i:the\s+)?"
            r"(?:[a-z0-9_-]+:[a-z0-9_-]+|\$[a-z][a-z0-9_-]*)\b",
        ),
        "cross-skill invocation is not portable",
    ),
    (
        "verbatim-import",
        re.compile(
            r"\b(?:(?:copied|imported)\s+verbatim|verbatim\s+(?:block|copy|import))\b",
            re.I,
        ),
        "verbatim imports require provenance review and are not allowed in the skill",
    ),
)

SPDX = re.compile(r"SPDX-License-Identifier:\s*(.+?)\s*$")
SPDX_OPERATORS = {"AND", "OR", "WITH"}


def _portable_path(relative: Path) -> bool:
    return relative == Path("SKILL.md") or (
        bool(relative.parts) and relative.parts[0] in PORTABLE_ROOTS
    )


def _scan_text(relative: Path, text: str) -> Iterable[Violation]:
    path = relative.as_posix()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for code, pattern, message in LINE_RULES:
            if pattern.search(line):
                yield Violation(path, line_number, code, message)

        match = SPDX.search(line)
        identifiers = []
        if match:
            identifiers = [
                token
                for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*", match.group(1))
                if token not in SPDX_OPERATORS
            ]
        incompatible = [
            identifier
            for identifier in identifiers
            if identifier not in COMPATIBLE_LICENSES
        ]
        if incompatible:
            yield Violation(
                path,
                line_number,
                "incompatible-license",
                f"SPDX license {incompatible[0]!r} is not compatible with this Apache-2.0 project",
            )


def lint_skill(skill_dir: Path) -> list[Violation]:
    """Return every portability violation under *skill_dir*."""
    skill_dir = Path(skill_dir)
    violations: list[Violation] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        violations.append(
            Violation("SKILL.md", 1, "missing-skill-file", "portable skill requires SKILL.md")
        )

    if not skill_dir.is_dir():
        return violations

    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        relative_text = relative.as_posix()

        if path.is_symlink():
            violations.append(
                Violation(relative_text, 1, "symlink", "skill source must not contain symlinks")
            )
            continue

        if not _portable_path(relative):
            violations.append(
                Violation(
                    relative_text,
                    1,
                    "nonportable-path",
                    "only SKILL.md, references/, and scripts/ are portable",
                )
            )
            continue

        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            violations.append(
                Violation(relative_text, 1, "non-text-file", "portable skill files must be UTF-8 text")
            )
            continue
        violations.extend(_scan_text(relative, text))

    return sorted(set(violations))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "skill_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "skills" / "miniproject",
    )
    args = parser.parse_args(argv)

    violations = lint_skill(args.skill_dir)
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: "
            f"{violation.code}: {violation.message}"
        )
    if violations:
        return 1
    print(f"portable: {args.skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
