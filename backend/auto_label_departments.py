# auto_label_departments.py
import re
import pandas as pd
from collections import Counter

CSV_IN = "petition_dataset.csv"
CSV_OUT = "petition_dataset_with_dept.csv"

# Simple keyword mapping - extend as needed
DEPT_KEYWORDS = {
    "water": [
        r"\bwater\b", r"\bdrinking water\b", r"\bwater supply\b", r"\bcontaminat", r"\bwell\b",
        r"\bpipe\b", r"\bsewage\b", r"\bleakage\b"
    ],
    "electricity": [
        r"\belectricit", r"\bpower\b", r"\btransformer\b", r"\bmeter\b", r"\bvoltage\b",
        r"\bshort circuit\b", r"\bload shedding\b", r"\bpower cut\b"
    ],
    "roads": [
        r"\broad\b", r"\bhighway\b", r"\bpothole\b", r"\bbridge\b", r"\baccident\b", r"\btraffic\b"
    ],
    "sanitation": [
        r"\bgarbage\b", r"\btrash\b", r"\bwaste\b", r"\bsanitation\b", r"\bsewer\b", r"\bmuck\b"
    ],
    "civil": [
        r"\bbuilding\b", r"\bpermit\b", r"\bconstruction\b", r"\bland\b", r"\bapproval\b"
    ],
    "crime": [
        r"\btheft\b", r"\brobbery\b", r"\bcrime\b", r"\bassault\b", r"\bpolice\b", r"\bstolen\b"
    ]
}

def detect_department(text):
    t = str(text).lower()
    # check each department; return first match (more specific rules can be added)
    for dept, patterns in DEPT_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, t):
                return dept
    return "unknown"

def main():
    df = pd.read_csv(CSV_IN)
    print("Loaded:", CSV_IN, "rows:", len(df))
    if "text" not in df.columns and "Text" not in df.columns:
        raise SystemExit("CSV must contain a 'text' column")

    text_col = "text" if "text" in df.columns else [c for c in df.columns if c.lower()=="text"][0]

    df["department"] = df[text_col].apply(detect_department)
    # Make department lower-case & strip
    df["department"] = df["department"].astype(str).str.lower().str.strip()

    print("Department distribution:")
    print(Counter(df["department"]))
    df.to_csv(CSV_OUT, index=False)
    print("Saved:", CSV_OUT)

if __name__ == "__main__":
    main()
