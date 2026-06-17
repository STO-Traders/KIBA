#!/usr/bin/env bash
# Build KIBA.app — a double-clickable macOS desktop app that opens KIBA in Terminal.
# Output: dist/KIBA.app  (and, with --desktop, a copy on your Desktop).
#
#   bash packaging/macos/build-app.sh            # build into dist/
#   bash packaging/macos/build-app.sh --desktop  # also copy to ~/Desktop
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOGO="$ROOT/assets/KIBAlogo.png"
OUT="$ROOT/dist/KIBA.app"

rm -rf "$OUT"; mkdir -p "$OUT/Contents/MacOS" "$OUT/Contents/Resources"

# Icon (.icns) from the logo
ICONSET="$(mktemp -d)/KIBA.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" "$LOGO" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  d=$((s * 2)); sips -z "$d" "$d" "$LOGO" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$OUT/Contents/Resources/KIBA.icns"

cat > "$OUT/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>KIBA</string>
<key>CFBundleDisplayName</key><string>KIBA</string>
<key>CFBundleIdentifier</key><string>com.stotraders.kiba</string>
<key>CFBundleVersion</key><string>0.1.0</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleExecutable</key><string>KIBA</string>
<key>CFBundleIconFile</key><string>KIBA.icns</string>
<key>LSMinimumSystemVersion</key><string>10.13</string>
</dict></plist>
PLIST

cat > "$OUT/Contents/MacOS/KIBA" <<'SH'
#!/bin/bash
# Open Terminal running KIBA. Prefers the personal trader launcher if it exists.
TRADER="$HOME/Documents/Kiba/kiba-trader.command"
if [ -f "$TRADER" ]; then
  open "$TRADER"
else
  BIN="$HOME/Documents/Kiba/.venv/bin/kiba"; [ -x "$BIN" ] || BIN="kiba"
  osascript -e 'tell application "Terminal" to activate' \
            -e "tell application \"Terminal\" to do script \"exec '$BIN' --stream\""
fi
SH
chmod +x "$OUT/Contents/MacOS/KIBA"

echo "✅ Built $OUT"
if [ "${1:-}" = "--desktop" ]; then
  rm -rf "$HOME/Desktop/KIBA.app"
  cp -R "$OUT" "$HOME/Desktop/KIBA.app"
  echo "✅ Copied to ~/Desktop/KIBA.app"
fi
