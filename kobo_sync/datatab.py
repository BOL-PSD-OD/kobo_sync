"""Build the human-readable, Lao-decoded `data` tab rows (upsert by uuid).

Header = keys/derived + every answer question (decoded to its Lao label, *_oth
merged) in form order + lat/lon + photo link columns. Mirrors the retired
Apps Script `data` tab but driven by the resolved form (FormInfo).
"""

# Lao status labels (mirror store-dashboard/lib/decode.py STATUS_LABELS).
STATUS_LABELS = {
    "domestic": "ໃນ · ມີ QR",
    "both_using": "ໃນ+ນອກ · ໃຊ້ພາຍໃນ",
    "foreign_using": "ນອກ · ໃຊ້ພາຍໃນ",
    "both_int": "ໃນ+ນອກ · ບໍ່ໃຊ້ · ສົນໃຈ",
    "foreign_int": "ນອກ · ບໍ່ໃຊ້ · ສົນໃຈ",
    "notool_int": "ບໍ່ມີເຄື່ອງມື · ສົນໃຈ",
    "both_unint": "ໃນ+ນອກ · ບໍ່ໃຊ້ · ບໍ່ສົນໃຈ",
    "foreign_unint": "ນອກ · ບໍ່ໃຊ້ · ບໍ່ສົນໃຈ",
    "notool_unint": "ບໍ່ມີເຄື່ອງມື · ບໍ່ສົນໃຈ",
    "unknown": "ບໍ່ລະບຸ",
}

PENDING = "ລໍຖ້າອັບໂຫລດ"    # photo exists in Kobo but not yet copied to Drive
VIEW = "ເບິ່ງຮູບ"            # link text for an uploaded photo


def _fmt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def _decode_cell(rec, name, info):
    meta = info.qmeta.get(name, {"select": None, "list": None})
    lst = info.choices.get(meta.get("list"), {})
    if meta.get("select") == "multiple":
        raw = _fmt(rec.get(name))
        base = ", ".join(lst.get(c, c) for c in raw.split()) if raw else ""
    elif meta.get("select") == "one":
        code = _fmt(rec.get(name))
        base = (lst.get(code, code) if code else "")
    else:
        base = _fmt(rec.get(name)) or ""
    oth = _fmt(rec.get(name + "_oth"))
    if oth:
        base = f"{base} — {oth}" if base else oth
    return base


def data_header(info):
    return (["store_id", "status", "is_duplicate", "submission_time", "uuid"]
            + list(info.answer_cols) + ["lat", "lon"] + list(info.photo_fields))


def _latlon(rec):
    raw = _fmt(rec.get("geopoint"))
    if raw:
        p = raw.split()
        if len(p) >= 2:
            return p[0], p[1]
    g = rec.get("_geolocation")
    if isinstance(g, list) and len(g) >= 2 and g[0] is not None and g[1] is not None:
        return str(g[0]), str(g[1])
    return "", ""


def data_rows(items, info, media_urls):
    """media_urls: {uuid|field: url}. Returns list of cell-lists matching data_header()."""
    rows = []
    for it in items:
        rec = it["rec"]
        line = [it["store_id"], STATUS_LABELS.get(it["status"], it["status"]),
                "YES" if it["is_duplicate"] else "", it["submission_time"], it["uuid"]]
        line += [_decode_cell(rec, name, info) for name in info.answer_cols]
        lat, lon = _latlon(rec)
        line += [lat, lon]
        for fld in info.photo_fields:
            key = f"{it['uuid']}|{fld}"
            if media_urls.get(key):
                line.append(f'=HYPERLINK("{media_urls[key]}","{VIEW}")')
            elif _fmt(rec.get(fld)):
                line.append(PENDING)
            else:
                line.append("")
        rows.append(line)
    return rows
