"""Assign a stable Store ID to each submission.

Known shops (selected from the catalog) keep their catalog code (e.g. H011).
'other_shop' submissions get the next sequential number for their business
type's prefix, continuing after the catalog max. Assignment is idempotent by
Kobo `_uuid` so re-runs never renumber existing stores.
"""

import re

from store_master.constants import PREFIX_BY_BIZ


def _number_for(code, prefix):
    """Return the integer N if code == prefix + digits, else None."""
    m = re.fullmatch(re.escape(prefix) + r"(\d+)", code or "")
    return int(m.group(1)) if m else None


class IdAssigner:
    def __init__(self, catalog_codes, prior_assignments=None):
        self.assigned = dict(prior_assignments or {})  # uuid -> store_id
        self.counters = {p: 0 for p in PREFIX_BY_BIZ.values()}
        seed = list(catalog_codes) + list(self.assigned.values())
        for code in seed:
            for prefix in self.counters:
                n = _number_for(code, prefix)
                if n is not None and n > self.counters[prefix]:
                    self.counters[prefix] = n

    def resolve(self, uuid, shop_name_code, biz_type):
        if uuid in self.assigned:
            return self.assigned[uuid]
        if shop_name_code and shop_name_code != "other_shop":
            store_id = shop_name_code
        else:
            prefix = PREFIX_BY_BIZ.get(biz_type, "O")
            self.counters[prefix] = self.counters.get(prefix, 0) + 1
            store_id = "%s%03d" % (prefix, self.counters[prefix])
        self.assigned[uuid] = store_id
        return store_id
