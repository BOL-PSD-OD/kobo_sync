"""One-time helper: obtain a Google OAuth refresh token for Drive photo uploads.

Why: a service account has no Drive storage quota and cannot own files in a
personal "My Drive" (403 storageQuotaExceeded). Uploading as YOU (your 15GB)
fixes that. This runs locally, opens a browser to consent once, and prints the
three values to paste into GitHub Secrets.

Setup (Google Cloud Console, one time):
  1. console.cloud.google.com -> create/pick a project -> enable "Google Drive API".
  2. APIs & Services -> OAuth consent screen -> External -> add yourself as a Test user.
  3. Credentials -> Create credentials -> OAuth client ID -> type "Desktop app"
     -> Download JSON, save it next to this script as client_secret.json.

Run (in the project venv):
  pip install google-auth-oauthlib
  python -m kobo_sync.get_oauth_token client_secret.json

Then add to GitHub Secrets (repo kobo_sync):
  GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REFRESH_TOKEN
"""
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main(argv):
    secret = argv[1] if len(argv) > 1 else "client_secret.json"
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(secret, SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh_token is returned.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print("\n=== COPY THESE INTO GITHUB SECRETS (repo kobo_sync) ===")
    print("GOOGLE_OAUTH_CLIENT_ID     =", creds.client_id)
    print("GOOGLE_OAUTH_CLIENT_SECRET =", creds.client_secret)
    print("GOOGLE_OAUTH_REFRESH_TOKEN =", creds.refresh_token)
    if not creds.refresh_token:
        print("\nWARNING: no refresh_token returned. Revoke prior access at "
              "myaccount.google.com/permissions and re-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
