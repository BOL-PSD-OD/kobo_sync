"""Build the single-row '_status' monitor summary (pure)."""

STATUS_HEADER = ["last_run", "kobo_fetched", "photos_uploaded_this_run",
                 "photos_pending", "deleted_this_run", "archive_mode", "caught_up"]


def build_status_row(*, run_iso, fetched, uploaded_new, pending, deleted, mode):
    return {
        "last_run": run_iso,
        "kobo_fetched": fetched,
        "photos_uploaded_this_run": uploaded_new,
        "photos_pending": pending,
        "deleted_this_run": deleted,
        "archive_mode": mode,
        "caught_up": "YES" if pending == 0 else "NO",
    }
