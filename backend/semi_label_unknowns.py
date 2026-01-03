# semi_label_unknowns.py
import pandas as pd
import os
import re
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score
from collections import Counter
import joblib

INPUT = "petition_dataset_with_dept.csv"
AUTO_OUT = "petition_dataset_auto_labeled.csv"   # dataset with high-confidence auto labels filled
REVIEW_OUT = "petition_dataset_to_review.csv"    # low-confidence predictions to manually review
MODEL_FILE = "models/dept_calibrated.joblib"
CONF_THRESHOLD = 0.85  # change if you want stricter/looser auto-labeling

os.makedirs("models", exist_ok=True)

def clean_text(s):
    if pd.isna(s): return ""
    s = str(s).lower()
    s = re.sub(r"http\S+"," ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def build_model():
    # TF-IDF (word uni+bi grams) + LinearSVC wrapped in CalibratedClassifierCV for probabilities
    tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1,2), analyzer='word')
    svc = LinearSVC(class_weight='balanced', max_iter=10000)
    calibrated = CalibratedClassifierCV(svc, cv=3)  # calibrate for predict_proba
    pipe = Pipeline([('tfidf', tfidf), ('clf', calibrated)])
    return pipe

def main():
    df = pd.read_csv(INPUT)
    if "department" not in df.columns:
        raise SystemExit("Input CSV must contain a 'department' column (even with 'unknown').")
    print("Loaded:", INPUT, "rows:", len(df))
    df['text_clean'] = df['text'].apply(clean_text)

    # split labeled vs unknown
    labeled = df[df['department'].notna() & (df['department'] != 'unknown')].copy()
    unknown = df[df['department'].isna() | (df['department']=='unknown')].copy()

    print("Labeled rows:", len(labeled), "Unknown rows:", len(unknown))
    print("Labeled distribution:", Counter(labeled['department']))

    if len(labeled) < 50:
        raise SystemExit("Too few labeled rows to train a reasonable model. Please label more manually.")

    # Train model on labeled data
    X = labeled['text_clean'].values
    y = labeled['department'].values

    model = build_model()
    print("Training department model on labeled data...")
    model.fit(X, y)

    # optional: quick CV estimate
    try:
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy', n_jobs=1)
        print("3-fold CV accuracy (dept):", scores.mean(), "±", scores.std())
    except Exception as e:
        print("CV skipped:", e)

    # predict on unknowns
    if len(unknown) > 0:
        unknown_texts = unknown['text_clean'].values
        probs = model.predict_proba(unknown_texts)
        preds = model.classes_[probs.argmax(axis=1)]
        max_probs = probs.max(axis=1)

        unknown = unknown.reset_index(drop=True)
        unknown['pred_dept'] = preds
        unknown['pred_conf'] = max_probs

        # split high-confidence vs low
        high_conf = unknown[unknown['pred_conf'] >= CONF_THRESHOLD].copy()
        low_conf = unknown[unknown['pred_conf'] < CONF_THRESHOLD].copy()

        print("High-confidence auto-labels:", len(high_conf))
        print("Low-confidence to review:", len(low_conf))

        # create auto-labeled dataset: labeled + high_conf (fill department)
        auto_fill = pd.concat([labeled, high_conf.assign(department=high_conf['pred_dept'])], ignore_index=True)
        auto_fill = auto_fill.drop(columns=['text_clean'], errors='ignore')
        auto_fill.to_csv(AUTO_OUT, index=False)
        print("Saved auto-labeled dataset to:", AUTO_OUT)

        # save to-review file containing low_conf and their model preds+conf for manual checking
        to_review = low_conf[['text','pred_dept','pred_conf']].copy()
        to_review.to_csv(REVIEW_OUT, index=False)
        print("Saved low-confidence items to review to:", REVIEW_OUT)

    else:
        print("No unknown rows found. Saving cleaned labeled dataset.")
        labeled.drop(columns=['text_clean'], errors='ignore').to_csv(AUTO_OUT, index=False)
        print("Saved:", AUTO_OUT)

    # save model
    joblib.dump(model, MODEL_FILE)
    print("Saved department model to:", MODEL_FILE)

if __name__ == "__main__":
    main()
