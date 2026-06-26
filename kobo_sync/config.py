"""Sync settings read from environment variables (GitHub Actions / local)."""
from dataclasses import dataclass

DEFAULT_SERVER = "https://kf.kobotoolbox.org"


@dataclass
class Settings:
    token: str = ""
    asset_uid: str = ""
    server: str = DEFAULT_SERVER
    sheet_id: str = ""
    drive_folder_id: str = ""
    archive_mode: str = "off"          # off | dry_run | delete  (SAFE default)
    archive_after_days: int = 30       # only delete submissions older than this
    delete_cap: int = 300              # max deletions per run

    @classmethod
    def from_env(cls, env):
        def g(k, d=""):
            v = env.get(k)
            return d if v is None else str(v)
        return cls(
            token=g("KOBO_TOKEN"),
            asset_uid=g("KOBO_ASSET_UID"),
            server=(g("KOBO_SERVER") or DEFAULT_SERVER).rstrip("/"),
            sheet_id=g("SHEET_ID"),
            drive_folder_id=g("DRIVE_FOLDER_ID"),
            archive_mode=g("ARCHIVE_MODE", "off").lower().strip(),
            archive_after_days=int(g("ARCHIVE_AFTER_DAYS", "30") or 30),
            delete_cap=int(g("DELETE_CAP", "300") or 300),
        )
