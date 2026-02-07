#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADDONS_DIR="$HOME/Library/Application Support/Blender/5.0/scripts/addons"
TARGET="$ADDONS_DIR/blendermania-addon"

mkdir -p "$ADDONS_DIR"

if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
  echo "Refusing to overwrite non-symlink: $TARGET"
  exit 1
fi

ln -sfn "$SCRIPT_DIR" "$TARGET"
echo "Symlinked addon to: $TARGET"
