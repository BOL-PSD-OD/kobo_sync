"""Build the 'psp_export' tab: one row per store with exactly the 18 columns the
PSP follow-up Apps Script form expects, so it can be copied straight into that
form's sheet.

Purely additive — does not touch the existing master/data/_raw tabs. Field names
are taken from the resilient form resolver (info.fields), so a form renumber does
not silently break this. Columns the follow-up FORM fills (PSP assignment +
Status After / Take a Photo / last_result / saved_at / saved_by) are left blank
here as copy placeholders.
"""
from kobo_sync.datatab import _decode_cell, _latlon

PSP_HEADER = [
    "PSP", "store_id", "status", "biz_type", "shop_name", "district",
    "village", "owner_name", "nationality", "phone", "why_not",
    "lat", "lon", "Status After", "Take a Photo", "last_result",
    "saved_at", "saved_by",
]

# 9-state derived status -> short interest label for the follow-up sheet.
# Merchants already using a domestic PSP have no interest answer -> "ໃຊ້ແລ້ວ".
_INTEREST = {
    "both_int": "ສົນໃຈ", "foreign_int": "ສົນໃຈ", "notool_int": "ສົນໃຈ",
    "both_unint": "ບໍ່ສົນໃຈ", "foreign_unint": "ບໍ່ສົນໃຈ", "notool_unint": "ບໍ່ສົນໃຈ",
    "both_using": "ໃຊ້ແລ້ວ", "foreign_using": "ໃຊ້ແລ້ວ", "domestic": "ໃຊ້ແລ້ວ",
}


def _f(rec, info, logical):
    """Decode an optional logical field; blank if the form has no such question."""
    name = info.fields.get(logical)
    return _decode_cell(rec, name, info) if name else ""


def psp_rows(items, info):
    """All stores, rebuilt every sync. Returns list of dicts keyed by PSP_HEADER
    (ready for sheets.upsert with key_col='store_id')."""
    rows = []
    for it in items:
        rec = it["rec"]
        lat, lon = _latlon(rec)
        rows.append({
            "PSP": "",                                  # assigned manually
            "store_id": it["store_id"],
            "status": _INTEREST.get(it["status"], ""),  # short interest label
            "biz_type": _f(rec, info, "biz_type"),      # decoded to Lao
            "shop_name": it["shop_name"],
            "district": it["district"],
            "village": _f(rec, info, "village"),
            "owner_name": _f(rec, info, "owner_name"),
            "nationality": _f(rec, info, "nationality"),
            "phone": _f(rec, info, "phone"),
            "why_not": _f(rec, info, "why"),            # reason for not using PSP
            "lat": lat,
            "lon": lon,
            "Status After": "",                         # filled by the form
            "Take a Photo": "",
            "last_result": "",
            "saved_at": "",
            "saved_by": "",
        })
    return rows
