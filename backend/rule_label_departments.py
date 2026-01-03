# rule_label_departments_v2.py
import pandas as pd
import re
import os
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

INPUT = "petition_dataset.csv"
OUTPUT = "petition_dataset_with_dept.csv"

# ============================
# 1. MASSIVE KEYWORD BANK
# ============================
DEPT_KEYWORDS = {
    "water": [
        "water", "pipe", "pipeline", "leak", "leakage", "tank", "borewell",
        "drinking", "supply", "contaminated", "sewage", "overflow", 
        "motor room", "valve", "rusty water", "muddy water"
    ],
    "electricity": [
        "electric", "power", "current", "meter", "transformer", "voltage",
        "short circuit", "wire", "line", "pole", "fuse", "eb", "tneb",
        "load shedding", "overload", "spark", "shock"
    ],
    "roads": [
        "road", "street", "pothole", "traffic", "bridge", "footpath",
        "speedbreaker", "accident", "jamming", "bad road", "damaged road",
        "construction debris", "crossing", "signal", "zebra crossing"
    ],
    "sanitation": [
        "garbage", "waste", "dustbin", "cleaning", "sanitation",
        "drainage", "sewage", "mosquito", "blockage", "toilet",
        "dirty water", "foul smell", "public toilet", "waste collection"
    ],
    "civil": [
        "construction", "building", "permission", "land", "encroachment",
        "approval", "cement", "compound wall", "tiles", "civil work",
        "illegal construction", "foundation", "structure", "pillar"
    ],
    "crime": [
        "theft", "robbery", "assault", "fraud", "police", "harassment",
        "kidnap", "threat", "illegal", "missing person", "violence",
        "abuse", "scam", "cheating", "drugs", "murder"
    ],
}

# Add multilingual triggers (Tamil + common mistakes)
MULTILINGUAL = {
    "water": ["தண்ணீர்", "குழாய்", "சேறு", "குடிநீர்"],
    "electricity": ["மின்சாரம்", "EB", "டி.என்.இ.பி"],
    "roads": ["சாலை", "ரோடு", "போக்குவரத்து"],
    "sanitation": ["குப்பை", "அழுக்கு", "டிரெயினேஜ்"],
    "civil": ["கட்டிடம்", "அனுமதி", "கட்டுமானம்"],
    "crime": ["கொள்ளை", "மிரட்டல்", "தாக்குதல்", "போலீஸ்"],
}

# Merge multilingual keywords
for dept, words in MULTILINGUAL.items():
    DEPT_KEYWORDS[dept].extend(words)

def clean(t):
    t = str(t).lower()
    t = re.sub(r"[^a-zA-Z0-9\s\u0B80-\u0BFF]", " ", t)  # Keep Tamil chars
    return re.sub(r"\s+", " ", t).strip()

def keyword_score(text):
    scores = {}
    for dept, kws in DEPT_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in text:
                score += 2 if len(kw.split()) > 1 else 1
        scores[dept] = score
    return scores

def fallback_similarity(df_texts, target_text):
    """Assign dept using TF-IDF similarity to previously labeled items"""
    tfidf = TfidfVectorizer(max_features=5000)
    X = tfidf.fit_transform(df_texts)
    vec = tfidf.transform([target_text])
    sims = cosine_similarity(vec, X)[0]

    top_idx = sims.argmax()
    return top_idx

def main():
    df = pd.read_csv(INPUT)
    df["clean"] = df["text"].astype(str).apply(clean)

    # Step 1: Assign based on keywords
    assigned = []
    for txt in df["clean"]:
        scores = keyword_score(txt)
        best_dept = max(scores, key=scores.get)
        if scores[best_dept] >= 1:  # Good hit
            assigned.append(best_dept)
        else:
            assigned.append("unknown")

    df["department"] = assigned

    # Step 2: Fallback using similarity (for 'unknown')
    known_df = df[df["department"] != "unknown"]
    unknown_df = df[df["department"] == "unknown"]

    if not known_df.empty:
        known_texts = known_df["clean"].tolist()
        known_labels = known_df["department"].tolist()

        for idx, row in unknown_df.iterrows():
            best_idx = fallback_similarity(known_texts, row["clean"])
            df.at[idx, "department"] = known_labels[best_idx]

    # Step 3: Final fallback — assign most common class (won't be needed)
    if df["department"].isna().sum() > 0:
        most_common = df["department"].mode()[0]
        df["department"] = df["department"].fillna(most_common)

    print("\nFINAL Department Distribution:")
    print(Counter(df["department"]))

    df.drop(columns=["clean"], inplace=True)
    df.to_csv(OUTPUT, index=False)
    print("\nSaved:", OUTPUT)

if __name__ == "__main__":
    main()
