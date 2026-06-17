# 🔏 Code-signing KIBA (remove the "unrecognized app" warnings)

Signing is cryptographically tied to **paid, identity-verified certificates** — there is no
free bypass (that's the point of it). Once you have the certs, both sides are turnkey:
Windows signs automatically in CI, macOS is one script.

## Windows — auto-sign `KIBA-Setup.exe` in CI
1. Buy an **Authenticode code-signing certificate** (Sectigo, DigiCert, SSL.com…). An **EV
   cert** gives *instant* SmartScreen trust; a standard (OV) cert builds reputation over time.
2. Export it as a **`.pfx`** (certificate + private key) with a password.
3. Base64-encode it: `base64 -i cert.pfx | pbcopy`
4. In GitHub → repo **Settings → Secrets and variables → Actions → New repository secret**:
   - `WINDOWS_CERT_BASE64` — the base64 string
   - `WINDOWS_CERT_PASSWORD` — the `.pfx` password
5. Cut a release: `git tag v0.2.0 && git push origin v0.2.0`.
   The workflow now **signs `KIBA-Setup.exe` automatically** (SHA-256 + RFC-3161 timestamp)
   and publishes the signed installer. No secret = it just builds unsigned, no error.

## macOS — sign + notarize `KIBA.app`
1. Join the **Apple Developer Program** ($99/yr) and install a **Developer ID Application**
   certificate (Xcode → Settings → Accounts → Manage Certificates → + → Developer ID Application).
2. Create an **app-specific password** at <https://appleid.apple.com> → Sign-In & Security.
3. Build, sign, notarize:
   ```bash
   bash packaging/macos/build-app.sh
   export SIGN_APP_ID="Developer ID Application: Your Name (TEAMID)"
   export APPLE_ID="you@example.com"
   export TEAM_ID="TEAMID"
   export APP_PASSWORD="abcd-efgh-ijkl-mnop"
   bash packaging/macos/sign-and-notarize-app.sh
   ```
   The result opens with **no Gatekeeper warning**, anywhere. (For a notarized `.pkg`
   installer instead of an app bundle, use `notarize-mac.sh`.)

## Free interim (no certificates)
- **macOS:** `xattr -dr com.apple.quarantine ~/Desktop/KIBA.app` clears the warning locally;
  recipients **right-click → Open** the first time.
- **Windows:** SmartScreen → **More info → Run anyway**. Unavoidable for an unsigned installer.
