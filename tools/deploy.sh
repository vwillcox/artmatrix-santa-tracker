#!/usr/bin/env bash
# Copies the plugin (3 MB, a few minutes) onto an Art Matrix over USB, into /lib/plugins/santa_tracker, and
# resets it. The firmware finds the new folder at boot and adds it switched off:
# switch it on from the settings page at http://<name>.local.
#
# Usage: tools/deploy.sh [serial-port]   (default: /dev/ttyACM0)
# Needs mpremote (pip install mpremote), or MPREMOTE pointing at one.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-/dev/ttyACM0}"
MPREMOTE="${MPREMOTE:-mpremote}"
TARGET=":/lib/plugins/santa_tracker"

cd "$ROOT/santa_tracker"

# What package.json lists is what an install from the catalogue would put there.
mapfile -t FILES < <(python3 -c 'import json; [print(src) for _, src in json.load(open("package.json"))["urls"]]')

echo "Copying santa_tracker to $PORT ..."
"$MPREMOTE" connect "$PORT" fs mkdir "$TARGET" 2>/dev/null || true
"$MPREMOTE" connect "$PORT" fs mkdir "$TARGET/clips" 2>/dev/null || true
for file in package.json "${FILES[@]}"; do
  echo "  $file"
  "$MPREMOTE" connect "$PORT" fs cp "$file" "$TARGET/$file"
done

echo "Resetting ..."
"$MPREMOTE" connect "$PORT" reset
echo "Done."
