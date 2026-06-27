"""Shared constants for the store-master engine (LPB form, 2026-06-27 revision)."""

# Business type (form question S3_Q1 choice name) -> Store ID prefix.
# Prefixes verified against the form's shop_name catalog (715 shops).
PREFIX_BY_BIZ = {
    "tour": "T",
    "hotel": "H",
    "restaurant": "R",
    "guesthouse": "G",
    "karaoke": "K",
    "pub": "P",
    "nightclub": "N",
    "oth_biz": "O",
}

# Logical field name -> form field name (matched against export columns by suffix).
# New-form numbering: acquirer/qr/use_domestic/interested moved; district/village
# became free-text S3.1_Q1/Q2.
FIELD_TO_FORM = {
    "biz_type": "S3_Q1",
    "biz_type_other": "S3_Q1_oth",
    "shop_name": "S3_Q2",
    "shop_name_other": "S3_Q2_oth",
    "district": "S3.1_Q1",
    "village": "S3.1_Q2",
    "acquirer": "S3_Q4",
    "qr": "S3_Q6",
    "use_domestic": "S3_Q9",
    "interested": "S3_Q12",
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
