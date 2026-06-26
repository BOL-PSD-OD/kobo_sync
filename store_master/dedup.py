"""Flag likely-duplicate submissions so a human can review/merge them."""

import re
import unicodedata
from collections import defaultdict


def _norm(s):
    s = unicodedata.normalize("NFC", s or "").strip().lower()
    return re.sub(r"\s+", " ", s)


def flag_duplicates(records):
    """records: list of dicts with keys store_id, shop_name, district, is_catalog.
    Return the set of indices that belong to a duplicate group.

    Two submissions are 'the same store' when:
      - both are catalog shops with the same store_id, OR
      - both are 'other' shops with the same normalised name AND same district.
    """
    groups = defaultdict(list)
    for i, rec in enumerate(records):
        if rec.get("is_catalog"):
            key = ("code", rec.get("store_id"))
        else:
            key = ("name", _norm(rec.get("shop_name")), rec.get("district"))
        groups[key].append(i)

    flagged = set()
    for idxs in groups.values():
        if len(idxs) > 1:
            flagged.update(idxs)
    return flagged
