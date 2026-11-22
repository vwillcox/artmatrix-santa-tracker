#!/usr/bin/env bash
# Renders the films in Blender and packs them into santa_tracker/.
#
# Usage: tools/build.sh [scene ...]   (default: all of them, the globe and the sleigh)
# Needs Blender 5 and uv. Frames are kept in build/, which can be deleted afterwards.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# drop is his visit; visit is an older film of it (down the chimney), not in the plugin now
FILMS=(pole checking workshop practice loading takeoff flying drop morning)
WANTED=("$@")
[ $# -eq 0 ] && WANTED=("${FILMS[@]}" globe sprite)
PACK=(uv run -q --with pillow --with numpy tools/pack.py)

mkdir -p build santa_tracker/clips
for scene in "${WANTED[@]}"; do
  echo "== $scene"
  if [ "$scene" = globe ] && [ ! -f tools/data/earth.png ]; then
    uv run -q --with pillow --with numpy tools/earth.py tools/data/earth.png
  fi
  rm -rf "build/$scene"
  blender -b -P tools/scenes.py -- "$scene" "build/$scene" | grep -E "frames$|Error|Traceback" || true
  case "$scene" in
    globe) "${PACK[@]}" globe build/globe santa_tracker/clips/globe.clip ;;
    sprite) "${PACK[@]}" sprite build/sprite santa_tracker/sleigh.png
            "${PACK[@]}" sprite build/sprite santa_tracker/sleigh_small.png --wide 21 ;;
    *) "${PACK[@]}" clip "build/$scene" "santa_tracker/clips/$scene.clip" ;;
  esac
done
