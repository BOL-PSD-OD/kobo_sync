"""Resolve logical field -> Kobo question name from the live form (resilient).

Status-critical and categorical fields are matched by their stable choice-LIST
name, not by question number, so a form renumber (e.g. S3_Q7 -> S3_Q4) cannot
silently break status/KPI logic. REQUIRED fields raise (fail loud, never guess).
Text fields (no list) and the three same-list `psp` questions are matched by
name / form order.
"""

# logical -> the unique choice list it must come from
LIST_FIELDS = {
    "biz_type": "biz_type",
    "shop_name": "shop_name",
    "acquirer": "acquirer",        # status-critical
    "use_domestic": "YN_Use",      # status-critical
    "interested": "int",           # status-critical
    "qr": "QR",
    "payment": "Payment",
    "network": "Network",
    "why": "why",
    "revenue": "profit",
}
REQUIRED = {"biz_type", "shop_name", "acquirer", "use_domestic", "interested"}

# logical -> question name (text fields have no list to match on)
TEXT_FIELDS = {
    "district": "S3.1_Q1",
    "village": "S3.1_Q2",
    "owner_name": "S3.1_Q3",
    "nationality": "S3.1_Q4",
    "phone": "S3.1_Q5",
}


def _survey(form):
    return (form.get("content") or {}).get("survey") or []


def _qname(q):
    return q.get("name") or q.get("$autoname")


def _qlist(q):
    ln = q.get("select_from_list_name")
    if ln:
        return ln
    t = str(q.get("type", ""))
    if t.startswith(("select_one ", "select_multiple ")):
        return t.split(" ", 1)[1]
    return None


def resolve_fields(form):
    """Return {logical: question_name | [names] | None}. Raise ValueError if a
    REQUIRED field cannot be resolved to exactly one question."""
    survey = _survey(form)
    out = {}
    for logical, list_name in LIST_FIELDS.items():
        hits = [_qname(q) for q in survey if _qlist(q) == list_name and _qname(q)]
        if len(hits) == 1:
            out[logical] = hits[0]
        elif logical in REQUIRED:
            raise ValueError(
                f"field '{logical}': expected exactly 1 question with list "
                f"'{list_name}', found {len(hits)}: {hits}")
        else:
            out[logical] = None
    out["awareness"] = [_qname(q) for q in survey if _qlist(q) == "learn" and _qname(q)]
    out["psp"] = [_qname(q) for q in survey if _qlist(q) == "psp" and _qname(q)]
    names = {_qname(q) for q in survey}
    for logical, qn in TEXT_FIELDS.items():
        out[logical] = qn if qn in names else None
    return out
