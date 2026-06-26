"""Map a raw Kobo export row (dict colname->value) to logical answers."""

from store_master.constants import FIELD_TO_FORM

MULTI_FIELDS = {"acquirer", "qr"}            # select_multiple
TEXT_FIELDS = {"biz_type", "biz_type_other", "shop_name", "shop_name_other",
               "district", "village"}
CODE_FIELDS = {"use_domestic", "interested", "uuid"}  # keep raw; None if absent


def _find_col(columns, form_field):
    """Return the export column whose last path segment == form_field, else None."""
    for c in columns:
        if c == form_field or c.split("/")[-1] == form_field:
            return c
    return None


def _multi(val):
    if val is None:
        return set()
    return set(str(val).split())


def map_row(row, columns):
    out = {}
    for logical, form_field in FIELD_TO_FORM.items():
        col = _find_col(columns, form_field)
        raw = row.get(col) if col is not None else None
        if logical in MULTI_FIELDS:
            out[logical] = _multi(raw)
        elif logical in TEXT_FIELDS:
            out[logical] = "" if raw is None else str(raw).strip()
        else:  # CODE_FIELDS: preserve None when the column is absent
            out[logical] = None if raw is None else str(raw).strip()
    return out
