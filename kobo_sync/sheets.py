"""Google Sheets I/O via a service account: read prior IDs, upsert tabs."""
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]


def open_sheet(sheet_id, sa_json):
    creds = Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(sheet_id)


def _ws(sh, title, header):
    """Get-or-create a worksheet and make sure row 1 is `header`."""
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=100, cols=max(10, len(header)))
    ws.update([header], "1:1")
    return ws


def read_prior_ids(sh):
    """{uuid: store_id} from the existing 'master' tab, or {} if absent."""
    try:
        rows = sh.worksheet("master").get_all_records()
    except gspread.WorksheetNotFound:
        return {}
    return {str(r["uuid"]): str(r["store_id"]) for r in rows if r.get("uuid") and r.get("store_id")}


def read_uploaded_media(sh):
    """(set of 'uuid|field', {key: url}) already in the '_media' tab."""
    try:
        rows = sh.worksheet("_media").get_all_records()
    except gspread.WorksheetNotFound:
        return set(), {}
    keys, urls = set(), {}
    for r in rows:
        k = f"{r.get('uuid')}|{r.get('field')}"
        keys.add(k)
        urls[k] = r.get("url", "")
    return keys, urls


def upsert(ws, header, rows, key_col):
    """Upsert `rows` (list of dicts) into `ws` matched on `key_col`; never deletes."""
    existing = {}
    values = ws.get_all_values()
    if len(values) > 1:
        idx = header.index(key_col)
        for i, r in enumerate(values[1:], start=2):
            if idx < len(r) and r[idx]:
                existing[r[idx]] = i
    appends = []
    for row in rows:
        line = [row.get(h, "") for h in header]
        key = str(row.get(key_col, ""))
        if key and key in existing:
            ws.update([line], f"A{existing[key]}")
        else:
            appends.append(line)
    if appends:
        ws.append_rows(appends, value_input_option="RAW")


def write_status(sh, header, row):
    ws = _ws(sh, "_status", header)
    ws.update([[row.get(h, "") for h in header]], "2:2")


def append_media(sh, new_rows):
    ws = _ws(sh, "_media", ["uuid", "field", "store_id", "file_id", "url"])
    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")
