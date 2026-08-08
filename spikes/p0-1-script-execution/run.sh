#!/usr/bin/env bash
# P0.1 — Do bundled scripts/ execute under Codex?
#
# Installs the probe skill the way install.sh is designed to: canonical copy in
# ~/.agents/skills/, symlinked into the harness skills dir. Then asks the agent
# to run it and checks for a sentinel only real execution produces.
#
# Two variants, because the repo's portability constraint is SKILL.md +
# references/ + scripts/ with no harness-specific files:
#   A  portable subset only
#   B  portable subset + agents/openai.yaml (Codex-specific)
#
# Removes everything it created, including on failure.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/skill"
NAME="mp-probe"
AGENTS_DIR="$HOME/.agents/skills/$NAME"
CODEX_LINK="$HOME/.codex/skills/$NAME"
EVIDENCE="$HERE/evidence"
MODEL="${MP_PROBE_MODEL:-gpt-5.6-sol}"
EXPECTED_TOKEN="$(python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('$SRC/scripts/echo_check.py').read_bytes()).hexdigest()[:16])")"

cleanup() {
  rm -rf "$AGENTS_DIR"
  [ -L "$CODEX_LINK" ] && rm -f "$CODEX_LINK"
  return 0
}
trap cleanup EXIT

for path in "$AGENTS_DIR" "$CODEX_LINK"; do
  if [ -e "$path" ] && [ ! -L "$path" ]; then
    echo "REFUSING: $path already exists and is not our symlink. Remove it first." >&2
    exit 2
  fi
done

mkdir -p "$EVIDENCE"

run_variant() {
  local variant="$1" with_openai_yaml="$2" extra_flags="${3:-}"
  local work; work="$(mktemp -d)"
  local log="$EVIDENCE/variant-${variant}.log"

  rm -rf "$AGENTS_DIR"; [ -L "$CODEX_LINK" ] && rm -f "$CODEX_LINK"
  mkdir -p "$(dirname "$AGENTS_DIR")" "$(dirname "$CODEX_LINK")"
  cp -R "$SRC" "$AGENTS_DIR"

  if [ "$with_openai_yaml" = "yes" ]; then
    mkdir -p "$AGENTS_DIR/agents"
    cat > "$AGENTS_DIR/agents/openai.yaml" <<'YAML'
interface:
  display_name: "MiniProject Probe"
  short_description: "Prove bundled script execution"
  default_prompt: "Use $mp-probe to run the bundled check."
policy:
  allow_implicit_invocation: true
YAML
  fi

  ln -s "$AGENTS_DIR" "$CODEX_LINK"

  echo "--- variant $variant (openai.yaml: $with_openai_yaml, flags: ${extra_flags:-none}) ---"
  # shellcheck disable=SC2086
  timeout 240 codex exec \
    --ephemeral --skip-git-repo-check $extra_flags \
    -C "$work" -s workspace-write -m "$MODEL" --color never \
    -o "$EVIDENCE/variant-${variant}.reply.txt" \
    "Use the mp-probe skill. Run its bundled check script with --out set to the current working directory, then report the token it printed." \
    < /dev/null > "$log" 2>&1
  local code=$?

  local sentinel="$work/probe-sentinel.json"
  local verdict="FAIL"
  local detail=""
  if [ -f "$sentinel" ]; then
    cp "$sentinel" "$EVIDENCE/variant-${variant}.sentinel.json"
    local got; got="$(python3 -c "import json;print(json.load(open('$sentinel'))['token'])" 2>/dev/null)"
    if [ "$got" = "$EXPECTED_TOKEN" ]; then
      verdict="PASS"; detail="sentinel written, token matches"
    else
      verdict="SUSPECT"; detail="sentinel present but token '$got' != '$EXPECTED_TOKEN'"
    fi
  else
    detail="no sentinel at $sentinel (exit $code)"
  fi

  printf '  %-8s %s\n' "$verdict" "$detail"
  grep -qi "mp-probe\|skill" "$log" && echo "  skill referenced in transcript: yes" || echo "  skill referenced in transcript: no"
  rm -rf "$work"
  [ "$verdict" = "PASS" ]
}

echo "P0.1 — bundled script execution under Codex"
echo "expected token: $EXPECTED_TOKEN"
echo "model: $MODEL"
echo

a_ok=0; b_ok=0; c_ok=0
run_variant A no  && a_ok=1
echo
run_variant B yes && b_ok=1
echo
# C: does the eval driver's isolation flag break skill discovery?
run_variant C no "--ignore-user-config --ignore-rules" && c_ok=1

echo
echo "=== RESULT ==="
echo "A portable subset only        : $([ $a_ok = 1 ] && echo PASS || echo FAIL)"
echo "B with agents/openai.yaml     : $([ $b_ok = 1 ] && echo PASS || echo FAIL)"
echo "C under eval isolation flags  : $([ $c_ok = 1 ] && echo PASS || echo FAIL)"
echo "evidence: $EVIDENCE"
[ $a_ok = 1 ] && [ $c_ok = 1 ]
