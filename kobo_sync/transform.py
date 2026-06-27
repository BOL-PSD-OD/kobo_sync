"""Kobo form JSON + API records -> master 'items' (id, status, dedup).

Reuses the tested store_master logic; only the Kobo-API-shape glue lives here.
Fields are resolved from the form by stable list-name (see store_master.fields).
"""
from dataclasses import dataclass, field

from store_master.ids import IdAssigner
from store_master.status import derive_status
from store_master.dedup import flag_duplicates
from store_master.fields import resolve_fields

NON_ANSWER_TYPES = {
    "note", "calculate", "begin_group", "end_group", "begin_repeat",
    "end_repeat", "start", "end", "today", "start-geopoint", "geopoint",
    "image", "audio", "video", "file", "background_audio", "username",
    "deviceid", "phonenumber", "simserial", "subscriberid",
}


@dataclass
class FormInfo:
    catalog: dict = field(default_factory=dict)      # code -> {name, biz_type}
    choices: dict = field(default_factory=dict)      # list_name -> {code: label}
    photo_fields: list = field(default_factory=list)
    fields: dict = field(default_factory=dict)       # logical -> question name(s)
    qmeta: dict = field(default_factory=dict)        # name -> {select, list, label}
    answer_cols: list = field(default_factory=list)  # ordered answer question names


def _first_label(label):
    if isinstance(label, list):
        for x in label:
            if x:
                return str(x)
        return ""
    return str(label) if label else ""


def _base_type(t):
    return str(t or "").split(" ")[0]


def _qlist(q):
    ln = q.get("select_from_list_name")
    if ln:
        return ln
    t = str(q.get("type", ""))
    if t.startswith(("select_one ", "select_multiple ")):
        return t.split(" ", 1)[1]
    return None


def parse_form(form):
    content = form.get("content", {})
    info = FormInfo()
    for ch in content.get("choices", []):
        ln = ch.get("list_name")
        nm = ch.get("name", ch.get("$autovalue"))
        if ln is None or nm is None:
            continue
        info.choices.setdefault(ln, {})[str(nm)] = _first_label(ch.get("label")) or str(nm)
        if ln == "shop_name" and str(nm) != "other_shop":
            info.catalog[str(nm)] = {"name": _first_label(ch.get("label")),
                                     "biz_type": str(ch.get("biz_type") or "")}
    for q in content.get("survey", []):
        name = q.get("name") or q.get("$autoname")
        if not name:
            continue
        bt = _base_type(q.get("type"))
        if bt == "image":
            info.photo_fields.append(name)
        select = "multiple" if str(q.get("type", "")).startswith("select_multiple") else (
            "one" if str(q.get("type", "")).startswith("select_one") else None)
        info.qmeta[name] = {"select": select, "list": _qlist(q),
                            "label": _first_label(q.get("label"))}
        if bt not in NON_ANSWER_TYPES and not name.endswith("_oth"):
            info.answer_cols.append(name)
    info.fields = resolve_fields(form)
    return info


def _norm(rec):
    return {k.split("/")[-1]: v for k, v in rec.items()}


def _fmt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def _codeset(rec, q):
    raw = _fmt(rec.get(q)) if q else None
    return set(raw.split()) if raw else set()


def build_items(records, info: FormInfo, prior_ids=None):
    f = info.fields
    assigner = IdAssigner(info.catalog.keys(), prior_ids)
    items = []
    for raw in records:
        rec = _norm(raw)
        uuid = _fmt(rec.get("_uuid")) or _fmt(rec.get("_id"))
        code = _fmt(rec.get(f["shop_name"]))
        is_catalog = bool(code) and code != "other_shop"
        biz = _fmt(rec.get(f["biz_type"])) or ""
        store_id = assigner.resolve(uuid, code or "", biz)
        name = info.catalog.get(code, {}).get("name", "") if is_catalog else (
            _fmt(rec.get(f["shop_name"] + "_oth")) or "")
        status = derive_status(_codeset(rec, f["acquirer"]), _codeset(rec, f.get("qr")),
                               _fmt(rec.get(f["use_domestic"])), _fmt(rec.get(f["interested"])))
        district = _fmt(rec.get(f["district"])) if f.get("district") else None
        items.append({
            "uuid": uuid, "kid": _fmt(rec.get("_id")), "store_id": store_id,
            "shop_name": name, "biz_type": biz, "district": district or "",
            "status": status, "is_catalog": is_catalog,
            "submission_time": _fmt(rec.get("_submission_time")) or "",
            "rec": rec,
        })
    flagged = flag_duplicates(items)
    for i, it in enumerate(items):
        it["is_duplicate"] = i in flagged
    return items
