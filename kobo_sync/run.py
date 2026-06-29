"""Orchestrate one sync round.

  python -m kobo_sync.run --fake kobo_sync/fake.json   # offline (no network/creds)
  python -m kobo_sync.run                               # live (env vars required)
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from kobo_sync.config import Settings
from kobo_sync.transform import parse_form, build_items
from kobo_sync import archive, monitor

MASTER_HEADER = ["store_id", "status", "shop_name", "biz_type", "district",
                 "is_duplicate", "uuid", "submission_time"]
RAW_HEADER = ["uuid", "store_id", "submission_time", "raw_json"]


def _master_rows(items):
    return [{"store_id": it["store_id"], "status": it["status"], "shop_name": it["shop_name"],
             "biz_type": it["biz_type"], "district": it["district"],
             "is_duplicate": "YES" if it["is_duplicate"] else "", "uuid": it["uuid"],
             "submission_time": it["submission_time"]} for it in items]


def _raw_rows(items):
    return [{"uuid": it["uuid"], "store_id": it["store_id"],
             "submission_time": it["submission_time"],
             "raw_json": json.dumps(it["rec"], ensure_ascii=False)} for it in items]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fake")
    args = ap.parse_args(argv)
    start = time.time()
    now = datetime.now(timezone.utc).timestamp()
    run_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    s = Settings.from_env(os.environ)

    if args.fake:
        blob = json.loads(open(args.fake, encoding="utf-8").read())
        form, records = blob["form"], blob["records"]
        prior, uploaded_keys = {}, set()
    else:
        from kobo_sync import kobo_api, sheets
        form = kobo_api.fetch_form(s)
        records = kobo_api.fetch_submissions(s)
        sa = os.environ.get("GOOGLE_SA_JSON", "")
        sh = sheets.open_sheet(s.sheet_id, sa)
        prior = sheets.read_prior_ids(sh)
        uploaded_keys, _media_urls_prior = sheets.read_uploaded_media(sh)

    info = parse_form(form)
    items = build_items(records, info, prior_ids=prior)
    print(f"fetched={len(records)} items={len(items)} photo_fields={info.photo_fields}")
    print("by status:", {st: sum(1 for it in items if it['status'] == st) for st in
                         sorted({it['status'] for it in items})})

    pending = set()
    uploaded_new = 0
    deleted = 0
    mode = s.archive_mode
    if args.fake:
        print("FAKE mode: skipping Sheet/Drive writes and deletion.")
    else:
        from kobo_sync import drive, kobo_api, datatab, psp_export
        # photos
        new_urls = {}
        svc = drive.drive_client(sa) if s.drive_folder_id else None
        if svc:
            new_rows, new_urls, pending = drive.upload_photos(
                svc, s.drive_folder_id, s.token, items, info.photo_fields, uploaded_keys, start=start)
            sheets.append_media(sh, new_rows)
            uploaded_keys |= set(new_urls)
            uploaded_new = len(new_rows)
        # sheets
        sheets.upsert(sheets._ws(sh, "master", MASTER_HEADER), MASTER_HEADER, _master_rows(items), "uuid")
        sheets.upsert(sheets._ws(sh, "_raw", RAW_HEADER), RAW_HEADER, _raw_rows(items), "uuid")
        sheets.write_form(sh, json.dumps(form, ensure_ascii=False))
        # decoded human-readable 'data' tab (links every photo already in Drive)
        media_urls = {**_media_urls_prior, **new_urls}
        sheets.write_data(sh, datatab.data_header(info), datatab.data_rows(items, info, media_urls))
        # psp_export tab: 18 cols ready to copy into the PSP follow-up form sheet
        sheets.upsert(sheets._ws(sh, "psp_export", psp_export.PSP_HEADER),
                      psp_export.PSP_HEADER, psp_export.psp_rows(items, info), "store_id")
        # archive (guarded; off by default)
        chosen = []
        if mode in ("dry_run", "delete"):
            chosen = archive.select_for_deletion(items, info.photo_fields, uploaded_keys,
                                                 now=now, after_days=s.archive_after_days, cap=s.delete_cap)
            if mode == "delete":
                for it in chosen:
                    if kobo_api.delete_submission(s, it["kid"]):
                        deleted += 1
        print(f"archive mode={mode} candidates={len(chosen)} deleted={deleted}")
        row = monitor.build_status_row(run_iso=run_iso, fetched=len(records),
                                       uploaded_new=uploaded_new, pending=len(pending),
                                       deleted=deleted, mode=mode)
        sheets.write_status(sh, monitor.STATUS_HEADER, row)
    print(f"done in {time.time()-start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
