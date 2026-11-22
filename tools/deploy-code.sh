#!/usr/bin/env bash
# Copies the plugin's small files (code, map, towns, route, sleigh, settings page, manifest: about
# 900 kB, a couple of minutes) to the board, leaving the films already there alone. Then ALWAYS resets the
# board and waits for its web page, so it is never left stopped.
#
# Usage: tools/deploy-code.sh [board-address]   (default: 10.0.0.51)
cd "$(dirname "$0")/../santa_tracker"
BOARD="${1:-10.0.0.51}"
TARGET=":/lib/plugins/santa_tracker"

# FILES="__init__.py package.json" tools/deploy-code.sh copies just those
for file in ${FILES:-land.bin towns.bin route.bin route.txt sleigh.png sleigh_small.png __init__.py config.html package.json thumbnail.png}; do
  if timeout 240 uvx mpremote connect /dev/ttyACM0 fs cp "$file" "$TARGET/$file" > /dev/null 2>&1; then
    echo "copied $file"
  else
    echo "FAILED to copy $file"
  fi
done

timeout 30 uvx mpremote connect /dev/ttyACM0 reset > /dev/null 2>&1
echo "reset exit: $?"

if curl -s -o /dev/null --max-time 3 --retry 15 --retry-delay 2 --retry-all-errors "http://$BOARD/plugins.json"; then
  echo "board healthy: web page is up"
else
  echo "BOARD DID NOT COME BACK"
  exit 1
fi
