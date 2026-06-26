"""Thin KoboToolbox REST layer: fetch form + submissions, delete one submission."""
import requests


def _headers(token):
    return {"Authorization": f"Token {token}"}


def fetch_form(s):
    r = requests.get(f"{s.server}/api/v2/assets/{s.asset_uid}.json",
                     headers=_headers(s.token), timeout=120)
    r.raise_for_status()
    return r.json()


def fetch_submissions(s):
    url = f"{s.server}/api/v2/assets/{s.asset_uid}/data.json?limit=10000"
    out = []
    while url:
        r = requests.get(url, headers=_headers(s.token), timeout=120)
        r.raise_for_status()
        page = r.json()
        out.extend(page.get("results", []))
        url = page.get("next")
    return out


def delete_submission(s, kid):
    """Delete ONE submission by numeric _id. IRREVERSIBLE. Returns True on success."""
    r = requests.delete(f"{s.server}/api/v2/assets/{s.asset_uid}/data/{kid}/",
                        headers=_headers(s.token), timeout=60)
    return r.status_code in (200, 202, 204)


def download_attachment(token, url):
    """Return raw bytes of a Kobo attachment, or None on failure."""
    r = requests.get(url, headers=_headers(token), timeout=120)
    return r.content if r.status_code < 300 else None
