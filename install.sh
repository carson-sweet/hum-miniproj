#!/usr/bin/env bash
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$ROOT/skills/miniproject"
SKILL_NAME="miniproject"
OWNER_MARKER_NAME=".miniproject.hum-miniproj-owned"
OWNER_VALUE="hum-miniproj:v1"
INSTALL_HOME="${HOME:?HOME must be set}"
MODE="install"

usage() {
  echo "usage: $0 [--home ABSOLUTE_PATH] [--uninstall]" >&2
}

refuse() {
  echo "REFUSING: $*" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --home)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      INSTALL_HOME="$2"
      shift 2
      ;;
    --uninstall)
      MODE="uninstall"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

case "$INSTALL_HOME" in
  /*) ;;
  *) refuse "--home must be an absolute path" ;;
esac
[ "$INSTALL_HOME" != "/" ] || refuse "--home may not be /"

CANONICAL="$INSTALL_HOME/.agents/skills/$SKILL_NAME"
OWNER_MARKER="$INSTALL_HOME/.agents/skills/$OWNER_MARKER_NAME"
CODEX_LINK="$INSTALL_HOME/.codex/skills/$SKILL_NAME"
JUNIE_LINK="$INSTALL_HOME/.junie/skills/$SKILL_NAME"
CLAUDE_LINK="$INSTALL_HOME/.claude/skills/$SKILL_NAME"
LINKS="$CODEX_LINK
$JUNIE_LINK
$CLAUDE_LINK"

is_owned_canonical() {
  [ -d "$CANONICAL" ] &&
    [ ! -L "$CANONICAL" ] &&
    [ -f "$OWNER_MARKER" ] &&
    [ "$(sed -n '1p' "$OWNER_MARKER")" = "$OWNER_VALUE" ]
}

check_links() {
  echo "$LINKS" | while IFS= read -r link; do
    if [ -L "$link" ]; then
      [ "$(readlink "$link")" = "$CANONICAL" ] ||
        refuse "$link is a symlink not owned by this installer"
    elif [ -e "$link" ]; then
      refuse "$link already exists and is not an owned symlink"
    fi
  done
}

check_links

if [ "$MODE" = "uninstall" ]; then
  if [ -e "$CANONICAL" ] || [ -L "$CANONICAL" ]; then
    is_owned_canonical || refuse "$CANONICAL is not owned by this installer"
  fi

  echo "$LINKS" | while IFS= read -r link; do
    [ -L "$link" ] && rm -f "$link"
  done
  if is_owned_canonical; then
    rm -rf "$CANONICAL"
    rm -f "$OWNER_MARKER"
  fi
  echo "uninstalled $SKILL_NAME from $INSTALL_HOME"
  exit 0
fi

[ -f "$SOURCE/SKILL.md" ] || refuse "source skill is missing: $SOURCE/SKILL.md"
if [ -e "$CANONICAL" ] || [ -L "$CANONICAL" ]; then
  is_owned_canonical || refuse "$CANONICAL already exists and is not owned by this installer"
fi

AGENTS_PARENT="$INSTALL_HOME/.agents/skills"
mkdir -p "$AGENTS_PARENT"
STAGE="$(mktemp -d "$AGENTS_PARENT/.miniproject-stage.XXXXXX")"
BACKUP=""

cleanup() {
  [ -n "$STAGE" ] && [ -d "$STAGE" ] && rm -rf "$STAGE"
  [ -n "$BACKUP" ] && [ -d "$BACKUP" ] && rm -rf "$BACKUP"
  return 0
}
trap cleanup EXIT

cp -R "$SOURCE/." "$STAGE/"

if is_owned_canonical; then
  BACKUP="$(mktemp -d "$AGENTS_PARENT/.miniproject-backup.XXXXXX")"
  rmdir "$BACKUP"
  mv "$CANONICAL" "$BACKUP"
fi
mv "$STAGE" "$CANONICAL"
STAGE=""
printf '%s\n' "$OWNER_VALUE" > "$OWNER_MARKER"

echo "$LINKS" | while IFS= read -r link; do
  mkdir -p "$(dirname "$link")"
  [ -L "$link" ] || ln -s "$CANONICAL" "$link"
done

if [ -n "$BACKUP" ] && [ -d "$BACKUP" ]; then
  rm -rf "$BACKUP"
  BACKUP=""
fi

echo "installed $SKILL_NAME for Codex, Junie, and Claude under $INSTALL_HOME"
