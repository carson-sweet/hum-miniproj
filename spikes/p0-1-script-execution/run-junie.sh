#!/usr/bin/env bash
# P0.1 under Junie. Transcription of the invocation verified by hand 2026-08-08.
#
# Junie needs no install/symlink dance: --skill-location points at any folder of
# skill directories, so the probe touches neither ~/.junie/skills nor the repo.
# Requires a one-time `junie` interactive auth (token lives in the macOS Keychain).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${MP_PROBE_MODEL:-gpt-5.6-sol}"
EXPECTED="$(python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('$HERE/skill/scripts/echo_check.py').read_bytes()).hexdigest()[:16])")"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/skills" "$TMP/work"
cp -R "$HERE/skill" "$TMP/skills/mp-probe"

echo "P0.1 under Junie — expected token: $EXPECTED"
timeout 300 junie \
  --project "$TMP/work" \
  --skill-location "$TMP/skills" \
  --model "$MODEL" \
  --skip-update-check \
  --task "Use the mp-probe skill. Run its bundled check script with --out set to the current working directory, then report the token it printed." \
  < /dev/null 2>&1 | tail -20

SENTINEL="$TMP/work/probe-sentinel.json"
if [ -f "$SENTINEL" ]; then
  GOT="$(python3 -c "import json;print(json.load(open('$SENTINEL'))['token'])" 2>/dev/null)"
  [ "$GOT" = "$EXPECTED" ] && { echo "PASS — sentinel written, token matches"; exit 0; }
  echo "SUSPECT — sentinel present, token '$GOT' != '$EXPECTED'"; exit 1
fi
echo "FAIL — no sentinel"; exit 1
