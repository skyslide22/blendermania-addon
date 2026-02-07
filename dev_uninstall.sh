#!/bin/bash
set -euo pipefail

ADDONS_DIR="$HOME/Library/Application Support/Blender/5.0/scripts/addons"
TARGET="$ADDONS_DIR/blendermania-addon"

if [ -L "$TARGET" ]; then
  rm "$TARGET"
  echo "Removed symlink: $TARGET"
  exit 0
fi

if [ -e "$TARGET" ]; then
  echo "Target exists and is not a symlink: $TARGET"
  exit 1
fi

echo "No symlink found at: $TARGET"
