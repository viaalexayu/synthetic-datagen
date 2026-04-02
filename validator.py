# validator.py

import re

VALID_CATEGORIES = ["origin_change", "prepend", "forged_as_path", "typo"]

REQUIRED_COLUMNS = [
    "category", "title", "hj_as", "hj_pfx", "vt_as", "vt_pfx",
    "propagation", "is_moas", "moas_duration", "is_submoas",
    "submoas_duration", "diff_cider", "global_hege_freq_hijacked",
    "global_hege_freq_normal", "local_hege_hijacker",
    "local_hege_freq_hijacked", "local_hege_freq_normal",
    "edit_distance", "prepending", "local_similarity",
    "local_hege_freq", "global_hege_freq", "local_union", "hege_score"
]

def fix_row(row):
    """
    Auto-fixes common issues in AI-generated rows
    before validation runs. Converts types, clamps
    values, fills missing fields with safe defaults.
    """

    # fix vt_as — must be integer, LLaMA sometimes returns float
    if "vt_as" in row:
        try:
            row["vt_as"] = int(float(row["vt_as"]))
        except (ValueError, TypeError):
            row["vt_as"] = 0

    # fix is_moas and is_submoas — must be 0 or 1
    for flag in ["is_moas", "is_submoas"]:
        if flag in row:
            try:
                row[flag] = int(float(row[flag]))
                if row[flag] not in [0, 1]:
                    row[flag] = 0
            except (ValueError, TypeError):
                row[flag] = 0

    # fix edit_distance — must be integer 1 to 4
    if "edit_distance" in row:
        try:
            ed = int(float(row["edit_distance"]))
            row["edit_distance"] = max(1, min(4, ed))
        except (ValueError, TypeError):
            row["edit_distance"] = 1

    # fix propagation — clamp to 0.0-1.0
    if "propagation" in row:
        try:
            p = float(row["propagation"])
            row["propagation"] = max(0.0, min(1.0, p))
        except (ValueError, TypeError):
            row["propagation"] = 0.0

    # fix all other float columns — clamp to 0.0-1.0
    float_cols = [
        "global_hege_freq_hijacked", "global_hege_freq_normal",
        "local_hege_hijacker", "local_hege_freq_hijacked",
        "local_hege_freq_normal", "prepending", "local_similarity",
        "local_hege_freq", "global_hege_freq", "local_union"
    ]
    for col in float_cols:
        if col in row and row[col] is not None:
            try:
                row[col] = float(row[col])
            except (ValueError, TypeError):
                row[col] = 0.0

    # fill any missing nullable columns with None
    nullable = ["moas_duration", "submoas_duration", "diff_cider"]
    for col in nullable:
        if col not in row:
            row[col] = None

    # fill missing hege_score with empty dict string
    if "hege_score" not in row or row["hege_score"] is None:
        row["hege_score"] = "{}"

    return row


def validate_row(row, original_df):
    # auto-fix before validating
    row = fix_row(row)

    # Rule 1 — all required columns present
    for col in REQUIRED_COLUMNS:
        if col not in row:
            return False, f"missing column: {col}"

    # Rule 2 — valid category
    if row.get("category") not in VALID_CATEGORIES:
        return False, f"invalid category: {row.get('category')}"

    # Rule 3 — valid IP prefix format e.g. 192.168.1.0/24
    ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$")
    if not ip_pattern.match(str(row.get("hj_pfx", ""))):
        return False, f"bad IP format: {row.get('hj_pfx')}"

    # Rule 4 — propagation between 0 and 1
    try:
        p = float(row.get("propagation", -1))
        if not (0.0 <= p <= 1.0):
            return False, "propagation out of range"
    except (ValueError, TypeError):
        return False, "propagation not a number"

    # Rule 5 — is_moas must be 0 or 1
    if int(row.get("is_moas", -1)) not in [0, 1]:
        return False, "is_moas must be 0 or 1"

    # Rule 6 — edit_distance must be 1 to 4
    if int(row.get("edit_distance", 0)) not in [1, 2, 3, 4]:
        return False, "edit_distance must be 1-4"

    # Rule 7 — no duplicate titles
    if row.get("title", "") in original_df["title"].values:
        return False, f"duplicate title: {row.get('title')}"

    return True, row