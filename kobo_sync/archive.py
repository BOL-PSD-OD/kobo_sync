"""Pure rules deciding which submissions are safe to delete from Kobo.

A submission is a delete candidate ONLY if ALL hold:
  - it has a Kobo numeric id and an assigned Store ID;
  - every image field that has a value is already uploaded to Drive;
  - it is older than `after_days`;
and we never exceed `cap` per run. Mirrors Code.gs runArchive_ guards.
"""
from datetime import datetime, timezone

DAY_SECONDS = 86400.0


def photo_complete(item, photo_fields, uploaded_keys):
    """True unless some image field has a value but is not in `uploaded_keys`
    (a set of 'uuid|field' strings)."""
    rec = item.get("rec", {})
    for f in photo_fields:
        val = rec.get(f)
        if val and str(val).strip() and f"{item['uuid']}|{f}" not in uploaded_keys:
            return False
    return True


def _age_seconds(sub_time, now):
    try:
        ts = datetime.fromisoformat(str(sub_time).replace("Z", "")).replace(tzinfo=timezone.utc)
        return now - ts.timestamp()
    except (ValueError, AttributeError):
        return -1.0    # unparseable -> treat as "too new" (never delete)


def select_for_deletion(items, photo_fields, uploaded_keys, *, now,
                        after_days, cap=300, day_seconds=DAY_SECONDS):
    out = []
    threshold = after_days * day_seconds
    for it in items:
        if len(out) >= cap:
            break
        if not it.get("kid") or not it.get("store_id"):
            continue
        if not photo_complete(it, photo_fields, uploaded_keys):
            continue
        if _age_seconds(it.get("submission_time"), now) < threshold:
            continue
        out.append(it)
    return out
