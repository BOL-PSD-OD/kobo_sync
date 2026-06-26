"""Load the predefined shop catalog (tour/hotel) from the XLSForm choices."""

import openpyxl


def load_catalog(form_xlsx_path):
    """Return {code: {"name": str, "biz_type": str}} for shop_name choices,
    excluding the 'other_shop' catch-all. Read-only; never writes."""
    wb = openpyxl.load_workbook(form_xlsx_path, read_only=True, data_only=True)
    ws = wb["choices"]
    it = ws.iter_rows(values_only=True)
    header = ["" if v is None else str(v) for v in next(it)]
    ix = {h: i for i, h in enumerate(header)}

    def cell(vals, col):
        i = ix.get(col)
        if i is None or i >= len(vals) or vals[i] is None:
            return ""
        return str(vals[i]).strip()

    catalog = {}
    for row in it:
        vals = list(row)
        if cell(vals, "list_name") != "shop_name":
            continue
        code = cell(vals, "name")
        if not code or code == "other_shop":
            continue
        catalog[code] = {"name": cell(vals, "label"), "biz_type": cell(vals, "biz_type")}
    return catalog
