"""Upload Kobo photos to Drive (one folder per Store ID); skip already-uploaded."""
import io
import json
import os
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

from kobo_sync.kobo_api import download_attachment

SCOPES = ["https://www.googleapis.com/auth/drive"]
PHOTO_STEM = {"Front_Mer": "front", "Doc": "doc", "Qr": "qr"}
BUDGET_SECONDS = 270.0   # stop starting new uploads after ~4.5 min per run


def drive_client(sa_json):
    """Build a Drive client. A service account has NO storage quota and cannot
    own uploaded files in a personal My Drive (403 storageQuotaExceeded), so if
    OAuth user credentials are configured we upload as that user (their 15GB
    quota); otherwise fall back to the service account (works only on a Shared
    Drive). Sheets I/O stays on the service account elsewhere."""
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    if client_id:
        from google.oauth2.credentials import Credentials as UserCredentials
        creds = UserCredentials(
            None,
            refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
            client_id=client_id,
            client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
    else:
        creds = Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _folder(svc, parent_id, name, cache):
    if name in cache:
        return cache[name]
    q = (f"'{parent_id}' in parents and name='{name}' and "
         "mimeType='application/vnd.google-apps.folder' and trashed=false")
    found = svc.files().list(q=q, fields="files(id)", supportsAllDrives=True,
                             includeItemsFromAllDrives=True).execute().get("files", [])
    fid = found[0]["id"] if found else svc.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id", supportsAllDrives=True).execute()["id"]
    cache[name] = fid
    return fid


def _match_attachment(rec, field, val):
    atts = rec.get("_attachments") or []
    for a in atts:
        xp = str(a.get("question_xpath") or a.get("question") or "")
        if xp.split("/")[-1] == field:
            return a
    base = str(val).split("/")[-1]
    for a in atts:
        fn = str(a.get("filename") or a.get("media_file_basename") or "").split("/")[-1]
        if fn and fn == base:
            return a
    return None


def upload_photos(svc, root_id, token, items, photo_fields, uploaded_keys, *, start, budget=BUDGET_SECONDS):
    """Upload new photos. Returns (new_media_rows, urls, pending_keys)."""
    new_rows, urls, pending = [], {}, set()
    cache = {}
    stopped = False
    errs = []
    for it in items:
        rec = it["rec"]
        for f in photo_fields:
            val = rec.get(f)
            if not val or not str(val).strip():
                continue
            key = f"{it['uuid']}|{f}"
            if key in uploaded_keys:
                continue
            if stopped or (time.time() - start) > budget:
                stopped = True
                pending.add(key)
                continue
            # A Drive/quota/network error on one photo must NOT abort the whole
            # sync: mark it pending (it retries next run) and keep going. Spec:
            # "รูปอัปไม่สำเร็จ = mark ລໍຖ້າອັບໂຫລດ ไม่บล็อก".
            try:
                att = _match_attachment(rec, f, val)
                dl = att and (att.get("download_url") or att.get("download_large_url"))
                data = download_attachment(token, dl) if dl else None
                if not data:
                    pending.add(key)
                    continue
                ext = (str(val).rsplit(".", 1)[-1] or "jpg").lower()[:4]
                fname = f"{PHOTO_STEM.get(f, f.lower())}.{ext}"
                fid = _folder(svc, root_id, it["store_id"], cache)
                media = MediaIoBaseUpload(io.BytesIO(data), mimetype="image/jpeg", resumable=False)
                created = svc.files().create(
                    body={"name": fname, "parents": [fid]},
                    media_body=media, fields="id, webViewLink",
                    supportsAllDrives=True).execute()
                url = created.get("webViewLink", "")
                urls[key] = url
                new_rows.append([it["uuid"], f, it["store_id"], created["id"], url])
            except Exception as e:   # noqa: BLE001 - keep the sync alive
                pending.add(key)
                errs.append(str(e))
    if errs:
        print(f"photo upload: {len(errs)} failed, kept pending. first error: {errs[0][:240]}")
    return new_rows, urls, pending
