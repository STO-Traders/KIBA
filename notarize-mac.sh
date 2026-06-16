#!/usr/bin/env bash
# Build a SIGNED + NOTARIZED macOS installer package (.pkg) for Kiba so users get
# NO "unidentified developer" warning.
#
# PREREQUISITES (one-time):
#   1. Enroll in the Apple Developer Program ($99/yr): https://developer.apple.com/programs/
#   2. Install a "Developer ID Installer" certificate in your login keychain
#      (Xcode → Settings → Accounts → Manage Certificates → + → Developer ID Installer).
#   3. Create an app-specific password: https://appleid.apple.com → Sign-In & Security.
#
# USAGE:
#   export SIGN_INSTALLER_ID="Developer ID Installer: Your Name (TEAMID)"
#   export APPLE_ID="you@example.com"
#   export TEAM_ID="TEAMID"
#   export APP_PASSWORD="abcd-efgh-ijkl-mnop"   # the app-specific password
#   ./notarize-mac.sh
#
# Result: Kiba-Installer.pkg  — double-clickable, notarized, no Gatekeeper warning.
set -euo pipefail

: "${SIGN_INSTALLER_ID:?set SIGN_INSTALLER_ID}"
: "${APPLE_ID:?set APPLE_ID}"
: "${TEAM_ID:?set TEAM_ID}"
: "${APP_PASSWORD:?set APP_PASSWORD}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD="$(mktemp -d)"
ROOT="$BUILD/root/usr/local/kiba"
SCRIPTS="$BUILD/scripts"
mkdir -p "$ROOT" "$SCRIPTS"

echo "Staging payload …"
# copy the project (minus venv/git/caches) into the pkg payload
rsync -a --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
      --exclude '*.pyc' --exclude '*.egg-info' ./ "$ROOT/"

# postinstall runs the normal installer as the logged-in user
cat > "$SCRIPTS/postinstall" <<'POST'
#!/bin/bash
USER_HOME=$(eval echo "~$USER")
cp -R /usr/local/kiba "$USER_HOME/Kiba"
chown -R "$USER" "$USER_HOME/Kiba"
sudo -u "$USER" bash "$USER_HOME/Kiba/install.sh" || true
exit 0
POST
chmod +x "$SCRIPTS/postinstall"

echo "Building component package …"
pkgbuild --root "$BUILD/root" \
         --scripts "$SCRIPTS" \
         --identifier "com.stotraders.kiba" \
         --version "0.1.0" \
         --install-location "/" \
         "$BUILD/Kiba-unsigned.pkg"

echo "Signing with $SIGN_INSTALLER_ID …"
productsign --sign "$SIGN_INSTALLER_ID" "$BUILD/Kiba-unsigned.pkg" "Kiba-Installer.pkg"

echo "Submitting to Apple notary service (this can take a few minutes) …"
xcrun notarytool submit "Kiba-Installer.pkg" \
  --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --password "$APP_PASSWORD" --wait

echo "Stapling the notarization ticket …"
xcrun stapler staple "Kiba-Installer.pkg"

rm -rf "$BUILD"
echo "✅ Done: Kiba-Installer.pkg (signed + notarized)"
