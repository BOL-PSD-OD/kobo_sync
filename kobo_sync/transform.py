"""Kobo form JSON + API records -> master 'items' (id, status, dedup).

Reuses the tested store_master logic; only the Kobo-API-shape glue lives here.
"""
from dataclasses import dataclass, field

from store_master.ids import IdAssigner
from store_master.status import derive_status
from store_master.dedup import flag_duplicates


@dataclass
class FormInfo:
    catalog: dict = field(default_factory=dict)   # code -> {name, biz_type}
    choices: dict = field(default_factory=dict)   # list_name -> {code: label}
    photo_fields: list = field(default_factory=list)


def _first_label(label):
    if isinstance(label, list):
        for x in label:
            if x:
                return str(x)
        return ""
    return str(label) if label else ""


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
        if name and str(q.get("type", "")).split(" ")[0] == "image":
            info.photo_fields.append(name)
    return info


def _norm(rec):
    return {k.split("/")[-1]: v for k, v in rec.items()}


def _fmt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def _codeset(rec, q):
    raw = _fmt(rec.get(q))
    return set(raw.split()) if raw else set()


def build_items(records, info: FormInfo, prior_ids=None):
    assigner = IdAssigner(info.catalog.keys(), prior_ids)
    items = []
    for raw in records:
        rec = _norm(raw)
        uuid = _fmt(rec.get("_uuid")) or _fmt(rec.get("_id"))
        code = _fmt(rec.get("S3_Q2"))
        is_catalog = bool(code) and code != "other_shop"
        biz = _fmt(rec.get("S3_Q1")) or ""
        store_id = assigner.resolve(uuid, code or "", biz)
        name = info.catalog.get(code, {}).get("name", "") if is_catalog else (_fmt(rec.get("S3_Q2_oth")) or "")
        status = derive_status(_codeset(rec, "S3_Q7"), _codeset(rec, "S3_Q9"),
                               _fmt(rec.get("S3_Q12")), _fmt(rec.get("S3_Q15")))
        items.append({
            "uuid": uuid, "kid": _fmt(rec.get("_id")), "store_id": store_id,
            "shop_name": name, "biz_type": biz, "district": _fmt(rec.get("S3_Q3")) or "",
            "status": status, "is_catalog": is_catalog,
            "submission_time": _fmt(rec.get("_submission_time")) or "",
            "rec": rec,
        })
    flagged = flag_duplicates(items)   # uses store_id/shop_name/district/is_catalog
    for i, it in enumerate(items):
        it["is_duplicate"] = i in flagged
    return items
