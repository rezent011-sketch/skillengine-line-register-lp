#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$(cd "$ROOT/../assets" && pwd)"
CHROME="${CHROME:-/usr/bin/google-chrome-stable}"

render() {
  local name="$1"
  local html="$ROOT/${name}.html"
  local dest="$OUT/section-${name}.png"
  local tmp
  tmp="$(mktemp --suffix=.png)"
  "$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-sandbox \
    --hide-scrollbars \
    --force-device-scale-factor=1 \
    --window-size=1080,1920 \
    --virtual-time-budget=8000 \
    --screenshot="$tmp" \
    "file://${html}"
  python3 - "$tmp" "$dest" <<'PY'
import sys
from pathlib import Path
src, dest = sys.argv[1], sys.argv[2]
try:
    from PIL import Image
    im = Image.open(src)
    if im.size != (1080, 1920):
        im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
    im.convert("RGB").save(dest, "PNG", optimize=True)
except Exception:
    Path(dest).write_bytes(Path(src).read_bytes())
PY
  rm -f "$tmp"
  echo "wrote $dest"
}

mkdir -p "$OUT"
for name in hero value-consult value-earn value-zero quotes cta; do
  render "$name"
done
