"""Download the sync Sheet (master/data) + all Drive photos to a local folder.

Run periodically so an independent copy lives OFF Google:
  python -m kobo_sync.backup_local
Env: SHEET_ID, GOOGLE_SA_JSON, DRIVE_FOLDER_ID (optional), BACKUP_DIR (default ./backup)
"""
import csv
import io
import json
import os
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]


def write_csv(path, rows):
    """rows = list of lists (incl. header). Write UTF-8 CSV (BOM for Excel)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)


def backup_sheets(sh, out_dir, tabs=("master", "data")):
    import gspread
    for tab in tabs:
        try:
            ws = sh.worksheet(tab)
        except gspread.WorksheetNotFound:
            continue
        write_csv(Path(out_dir) / "sheets" / f"{tab}.csv", ws.get_all_values())


def _download(svc, file_id, path):
    from googleapiclient.http import MediaIoBaseDownload
    if path.exists():
        return                       # skip already-downloaded (idempotent)
    path.parent.mkdir(parents=True, exist_ok=True)
    dl = MediaIoBaseDownload(io.FileIO(str(path), "wb"), svc.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = dl.next_chunk()


def _walk(svc, folder_id, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    page = None
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType)", pageToken=page).execute()
        for f in resp.get("files", []):
            if f["mimeType"] == "application/vnd.google-apps.folder":
                _walk(svc, f["id"], dest / f["name"])
            else:
                _download(svc, f["id"], dest / f["name"])
        page = resp.get("nextPageToken")
        if not page:
            break


def main():
    out = Path(os.environ.get("BACKUP_DIR", "backup"))
    sa = os.environ["GOOGLE_SA_JSON"]
    from google.oauth2.service_account import Credentials
    import gspread
    creds = Credentials.from_service_account_info(json.loads(sa), scopes=SCOPES)
    sh = gspread.authorize(creds).open_by_key(os.environ["SHEET_ID"])
    backup_sheets(sh, out)
    print(f"sheets -> {out / 'sheets'}")
    folder = os.environ.get("DRIVE_FOLDER_ID", "")
    if folder:
        from googleapiclient.discovery import build
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)
        _walk(svc, folder, out / "photos")
        print(f"photos -> {out / 'photos'}")
    print("backup done")


if __name__ == "__main__":
    main()
