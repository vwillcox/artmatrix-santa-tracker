#!/usr/bin/env bash
# Takes screenshots of the plugin from the board, safely.
#
#   cap/run.sh FIRST LAST     shots FIRST up to (not including) LAST, from cap.py's list
#
# The plugin runs from this computer over USB: nothing is written to the board's
# storage, and the pictures are saved here in cap/out. Whatever happens, the board is
# then reset, and this waits for its web page to answer, so it is never left stopped.
cd "$(dirname "$0")/.."
echo "$1 $2" > cap/which.txt

timeout 60 uvx mpremote connect /dev/ttyACM0 mount . exec "exec(open('/remote/cap/${CAP:-cap.py}').read())" 2>&1 | grep -v "^Local directory" | tail -40
echo "capture exit: ${PIPESTATUS[0]}"

timeout 30 uvx mpremote connect /dev/ttyACM0 reset > /dev/null 2>&1
echo "reset exit: $?"

if curl -s -o /dev/null --max-time 3 --retry 15 --retry-delay 2 --retry-all-errors http://10.0.0.51/plugins.json; then
  echo "board healthy: web page is up"
else
  echo "BOARD DID NOT COME BACK"
  exit 1
fi
