#!/usr/bin/env bash
# Sign + notarize KIBA.app so macOS shows NO "unidentified developer" warning.
#
# PREREQUISITES (one-time):
#   1. Apple Developer Program ($99/yr): https://developer.apple.com/programs/
#   2. A "Developer ID Application" certificate in your login keychain
#      (Xcode → Settings → Accounts → Manage Certificates → + → Developer ID Application).
#   3. An app-specific password: https://appleid.apple.com → Sign-In & Security.
#
# USAGE:
#   bash packaging/macos/build-app.sh                       # build dist/KIBA.app first
#   export SIGN_APP_ID="Developer ID Application: Your Name (TEAMID)"
#   export APPLE_ID="you@example.com"
#   export TEAM_ID="TEAMID"
#   export APP_PASSWORD="abcd-efgh-ijkl-mnop"
#   bash packaging/macos/sign-and-notarize-app.sh           # signs + notarizes dist/KIBA.app
#
# Result: a stapled, notarized KIBA.app that opens with no Gatekeeper warning anywhere.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="${1:-$ROOT/dist/KIBA.app}"

[ -d "$APP" ] || { echo "Not found: $APP — build it first: bash packaging/macos/build-app.sh"; exit 1; }
: "${SIGN_APP_ID:?set SIGN_APP_ID to your 'Developer ID Application: …' identity}"
: "${APPLE_ID:?set APPLE_ID}"
: "${TEAM_ID:?set TEAM_ID}"
: "${APP_PASSWORD:?set APP_PASSWORD (app-specific password)}"

echo "→ signing (hardened runtime)…"
codesign --force --deep --options runtime --timestamp --sign "$SIGN_APP_ID" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "→ zipping for notarization…"
ZIP="$(dirname "$APP")/KIBA-notarize.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"

echo "→ submitting to Apple notary (waits for the result)…"
xcrun notarytool submit "$ZIP" \
  --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --password "$APP_PASSWORD" --wait

echo "→ stapling the notarization ticket…"
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
rm -f "$ZIP"

echo "✅ $APP is signed + notarized — opens with no warning. Re-copy it to the Desktop / ship it."
