"""Shared constants for the store-master engine."""

# Business type (form question S3_Q1 choice name) -> Store ID prefix.
PREFIX_BY_BIZ = {
    "tour": "T",
    "hotel": "H",
    "restaurant": "R",
    "spa": "M",
    "souvenir": "G",
    "night_market": "N",
    "oth_biz": "O",
}

# Logical field name -> form field name (matched against export columns by suffix).
FIELD_TO_FORM = {
    "biz_type": "S3_Q1",
    "biz_type_other": "S3_Q1_oth",
    "shop_name": "S3_Q2",
    "shop_name_other": "S3_Q2_oth",
    "district": "S3_Q3",
    "village": "S3_Q4",
    "acquirer": "S3_Q7",
    "qr": "S3_Q9",
    "use_domestic": "S3_Q12",
    "interested": "S3_Q15",
    "uuid": "_uuid",
}

# 9 derived statuses (+ "unknown" fallback), in form-path order. See status.py.
STATUSES = (
    "both_using", "both_int", "both_unint",            # 1-3: domestic + foreign
    "foreign_using", "foreign_int", "foreign_unint",   # 4-6: foreign only
    "domestic",                                        # 7:   domestic only
    "notool_int", "notool_unint",                      # 8-9: no payment tool
    "unknown",
)
