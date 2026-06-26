"""Turn mapped submissions into master rows: id, name, status, dup flag."""

from store_master.ids import IdAssigner
from store_master.status import derive_status
from store_master.dedup import flag_duplicates


def build_master_rows(subs, catalog, prior_assignments=None):
    """subs: list of logical answer dicts (see rowmap.map_row output).
    catalog: {code: {name, biz_type}}. Returns list of master-row dicts."""
    assigner = IdAssigner(catalog.keys(), prior_assignments)
    rows = []
    for s in subs:
        code = s.get("shop_name") or ""
        is_catalog = bool(code) and code != "other_shop"
        store_id = assigner.resolve(s.get("uuid"), code, s.get("biz_type"))
        if is_catalog:
            name = catalog.get(code, {}).get("name", "")
        else:
            name = s.get("shop_name_other", "")
        rows.append({
            "store_id": store_id,
            "shop_name": name,
            "biz_type": s.get("biz_type", ""),
            "district": s.get("district", ""),
            "status": derive_status(
                s.get("acquirer"), s.get("qr"),
                s.get("use_domestic"), s.get("interested"),
            ),
            "is_catalog": is_catalog,
            "uuid": s.get("uuid"),
        })

    flagged = flag_duplicates(rows)
    for i, row in enumerate(rows):
        row["is_duplicate"] = i in flagged
    return rows
