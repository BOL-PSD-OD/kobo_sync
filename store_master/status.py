"""Derive the store status (9 states) from payment answers.

Mirrors docs/store-survey-overview.md section 4. Status is driven by
S3_Q7 (acquirer) x S3_Q12 (use_domestic) x S3_Q15 (interested).

S3_Q7 (acquirer) codes: "1" domestic ("QR in"), "2" foreign ("QR out"),
"3" no payment tool ("not QR in"). NOTE: the legacy/deployed form emits "0"
for foreign instead of "2"; both are accepted. S3_Q9 (qr) is collected as
detail data but no longer affects the status.
"""

# The three states that mean "already in the domestic system" (KPI success).
IN_SYSTEM = ("domestic", "both_using", "foreign_using")


def derive_status(acquirer, qr, use_domestic, interested):
    """Return one of 9 status keys, or "unknown" when nothing is selected.

    acquirer: iterable of S3_Q7 codes ("1" domestic, "2" foreign, "3" none).
    use_domestic: S3_Q12 "1"/"0"/None  -- "1" = uses domestic ("Correct").
    interested:   S3_Q15 "1"/"0"/None  -- "1" = interested.
    qr: S3_Q9 codes -- accepted for the data model, not used for status.

    both (1+2):   Correct -> both_using   | int -> both_int    | unint -> both_unint
    foreign (2):  Correct -> foreign_using | int -> foreign_int | unint -> foreign_unint
    domestic (1): -> domestic
    no tool (3):  int -> notool_int | unint -> notool_unint
    """
    acquirer = set(acquirer or [])
    dom = "1" in acquirer                        # "QR in"  (domestic acquirer)
    foreign = "2" in acquirer or "0" in acquirer  # "QR out" ("2" new / "0" legacy)
    notool = "3" in acquirer                     # "not QR in" (no payment tool)

    if dom and foreign:
        if use_domestic == "1":
            return "both_using"
        return "both_int" if interested == "1" else "both_unint"
    if foreign:
        if use_domestic == "1":
            return "foreign_using"
        return "foreign_int" if interested == "1" else "foreign_unint"
    if dom:
        return "domestic"
    if notool:
        return "notool_int" if interested == "1" else "notool_unint"
    return "unknown"
