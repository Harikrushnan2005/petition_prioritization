

import os
import re
import joblib
import traceback
from collections import Counter

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

SEED = 42

# -------------------------
# Hard-coded CSV path (exact path you provided)
# -------------------------
CSV_PATH = r"C:\Users\HARIKRUSHNAN T\Downloads\petition_all_d_l\backend\petition_dataset_with_dept.csv"
MODELS_DIR = r"C:\Users\HARIKRUSHNAN T\Downloads\petition_all_d_l\backend\models"

# -------------------------
# Text cleaning and leakage removal
# -------------------------
def clean_text(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).lower()
    s = re.sub(r"http\S+", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def remove_label_leakage(series_text: pd.Series, tokens: list):
    # Remove whole-word tokens from text to avoid leakage.
    unique_tokens = sorted({str(t).lower().strip() for t in tokens if str(t).strip()}, key=len, reverse=True)
    if not unique_tokens:
        return series_text
    pattern = r"\b(" + "|".join(re.escape(tok) for tok in unique_tokens) + r")\b"
    cleaned = []
    for t in series_text:
        t = clean_text(t)
        t = re.sub(pattern, " ", t, flags=re.IGNORECASE)
        t = re.sub(r"\s+", " ", t).strip()
        cleaned.append(t)
    return pd.Series(cleaned)

# -------------------------
# Pipelines
# -------------------------
def build_dept_pipeline():
    # Note: SelectKBest removed to avoid k > n_features warnings.
    return Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=5000, min_df=1, stop_words='english')),
        ('clf', CalibratedClassifierCV(LinearSVC(class_weight='balanced', max_iter=5000, random_state=SEED), cv=3))
    ])

def build_priority_pipeline():
    return Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=4000, min_df=1, stop_words='english')),
        ('clf', CalibratedClassifierCV(LogisticRegression(class_weight='balanced', max_iter=5000, random_state=SEED), cv=3))
    ])

# -------------------------
# Helpers
# -------------------------
def safe_cv_splits(series, max_splits=5):
    counts = series.value_counts()
    if len(counts) == 0:
        return 2
    min_count = int(counts.min())
    n = min(max_splits, min_count)
    if n < 2:
        n = 2
    return n

# -------------------------
# Main flow
# -------------------------
def load_and_prepare(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Loaded dataset: {csv_path} rows: {len(df)} columns: {list(df.columns)}")

    # Normalize expected column names:
    cols_lower = [c.lower() for c in df.columns]
    col_map = {}
    if 'text' in cols_lower:
        col_map[df.columns[cols_lower.index('text')]] = 'text'
    # Department column may be called 'department' or 'dept'
    if 'department' in cols_lower:
        col_map[df.columns[cols_lower.index('department')]] = 'department'
    if 'dept' in cols_lower and 'department' not in col_map.values():
        col_map[df.columns[cols_lower.index('dept')]] = 'department'
    # Priority column could be named 'label' in your file; we map it to 'priority' internally
    if 'priority' in cols_lower:
        col_map[df.columns[cols_lower.index('priority')]] = 'priority'
    elif 'label' in cols_lower:
        col_map[df.columns[cols_lower.index('label')]] = 'priority'
    elif 'class' in cols_lower:
        col_map[df.columns[cols_lower.index('class')]] = 'priority'

    df = df.rename(columns=col_map)

    # Validate required columns exist after rename
    if not {'text', 'department', 'priority'}.issubset(set(df.columns)):
        raise ValueError("CSV must contain columns for text, department, and priority (or label). Please ensure file has these headers.")

    # Keep only the three columns
    df = df[['text','department','priority']].copy()

    # Deduplicate exact texts
    before = len(df)
    df = df.drop_duplicates(subset=['text']).reset_index(drop=True)
    after = len(df)
    print(f"Deduplicated exact texts: removed {before-after} duplicates. Remaining: {after}")

    # Clean & normalize
    df['text_clean'] = df['text'].astype(str).apply(clean_text)
    df['department'] = df['department'].astype(str).str.lower().str.strip()
    df['priority'] = df['priority'].astype(str).str.lower().str.strip()

    # Remove leakage tokens from text (first priority words then department words)
    print("Removing priority/department words from text to prevent leakage...")
    df['text_noleak'] = remove_label_leakage(df['text_clean'], df['priority'].unique().tolist())
    df['text_noleak'] = remove_label_leakage(df['text_noleak'], df['department'].unique().tolist())

    print("Class counts (priority):", Counter(df['priority']))
    print("Class counts (department):", Counter(df['department']))
    return df

def train_and_evaluate(df, models_dir, n_jobs=1):
    X = df['text_noleak'].values
    y_dept = df['department'].values
    y_prio = df['priority'].values

    dept_cv = safe_cv_splits(df['department'])
    prio_cv = safe_cv_splits(df['priority'])
    print(f"Using dept_cv={dept_cv}, prio_cv={prio_cv}")

    skf_dept = StratifiedKFold(n_splits=dept_cv, shuffle=True, random_state=SEED)
    skf_prio = StratifiedKFold(n_splits=prio_cv, shuffle=True, random_state=SEED)

    dept_pipe = build_dept_pipeline()
    prio_pipe = build_priority_pipeline()

    # Cross-validate (single-process default for reliability)
    print("\n=== Department classifier: CV ===")
    dept_scores = cross_val_score(dept_pipe, X, y_dept, cv=skf_dept, scoring='accuracy', n_jobs=n_jobs)
    print("CV accuracy scores:", np.round(dept_scores, 4))
    print("CV mean accuracy:", float(np.round(dept_scores.mean(), 4)))

    dept_preds = cross_val_predict(dept_pipe, X, y_dept, cv=skf_dept, n_jobs=n_jobs)
    print("\nDepartment classification report (CV predictions):")
    print(classification_report(y_dept, dept_preds, digits=4))
    print("Department confusion matrix:")
    print(confusion_matrix(y_dept, dept_preds, labels=np.unique(y_dept)))

    print("\n=== Priority classifier: CV ===")
    prio_scores = cross_val_score(prio_pipe, X, y_prio, cv=skf_prio, scoring='accuracy', n_jobs=n_jobs)
    print("CV accuracy scores:", np.round(prio_scores, 4))
    print("CV mean accuracy:", float(np.round(prio_scores.mean(), 4)))

    prio_preds = cross_val_predict(prio_pipe, X, y_prio, cv=skf_prio, n_jobs=n_jobs)
    print("\nPriority classification report (CV predictions):")
    print(classification_report(y_prio, prio_preds, digits=4))
    print("Priority confusion matrix:")
    print(confusion_matrix(y_prio, prio_preds, labels=np.unique(y_prio)))

    # GridSearch for department (safe defaults)
    print("\nRunning small GridSearch for department (safe)...")
    dept_param_grid = {
        'tfidf__max_features': [2000, 5000],
        'tfidf__ngram_range': [(1,1), (1,2)],
        'clf__estimator__C': [0.5, 1.0, 2.0]
    }
    try:
        gs_dept = GridSearchCV(dept_pipe, dept_param_grid, cv=min(3, dept_cv), n_jobs=n_jobs, scoring='accuracy', verbose=0)
        gs_dept.fit(X, y_dept)
        best_dept = gs_dept.best_estimator_
        print("Dept best params:", gs_dept.best_params_)
    except Exception:
        print("Dept GridSearch failed; falling back to default pipeline. Trace:")
        traceback.print_exc()
        best_dept = dept_pipe
        best_dept.fit(X, y_dept)

    print("Running small GridSearch for priority (safe)...")
    prio_param_grid = {
        'tfidf__max_features': [2000, 4000],
        'tfidf__ngram_range': [(1,1), (1,2)]
    }
    try:
        gs_prio = GridSearchCV(prio_pipe, prio_param_grid, cv=min(3, prio_cv), n_jobs=n_jobs, scoring='accuracy', verbose=0)
        gs_prio.fit(X, y_prio)
        best_prio = gs_prio.best_estimator_
        print("Priority best params:", gs_prio.best_params_)
    except Exception:
        print("Priority GridSearch failed; falling back to default pipeline. Trace:")
        traceback.print_exc()
        best_prio = prio_pipe
        best_prio.fit(X, y_prio)

    # Final evaluation on the full dataset (optimistic)
    print("\nFinal evaluation on full training set (may be optimistic):")
    dept_train_pred = best_dept.predict(X)
    prio_train_pred = best_prio.predict(X)

    print("Department accuracy (train):", accuracy_score(y_dept, dept_train_pred))
    print(classification_report(y_dept, dept_train_pred, digits=4))

    print("Priority accuracy (train):", accuracy_score(y_prio, prio_train_pred))
    print(classification_report(y_prio, prio_train_pred, digits=4))

    # Save models (use priority in filename)
    os.makedirs(models_dir, exist_ok=True)
    dept_file = os.path.join(models_dir, 'dept_pipeline.joblib')
    prio_file = os.path.join(models_dir, 'priority_pipeline.joblib')
    joblib.dump(best_dept, dept_file)
    joblib.dump(best_prio, prio_file)
    print(f"\nSaved Department pipeline to: {dept_file}")
    print(f"Saved Priority pipeline to: {prio_file}")

    summary = {
        'dept_cv_mean': float(np.round(dept_scores.mean(), 4)),
        'priority_cv_mean': float(np.round(prio_scores.mean(), 4)),
        'dept_train_acc': float(accuracy_score(y_dept, dept_train_pred)),
        'priority_train_acc': float(accuracy_score(y_prio, prio_train_pred))
    }
    return summary, dept_file, prio_file

# -------------------------
# Entrypoint
# -------------------------
if __name__ == '__main__':
    df = load_and_prepare(CSV_PATH)

    if df['priority'].nunique() < 2 or df['department'].nunique() < 2:
        raise ValueError("Need at least 2 classes in both priority and department for training.")

    print(f"Min samples per class - priority: {df['priority'].value_counts().min()}, department: {df['department'].value_counts().min()}")

    summary, dept_path, prio_path = train_and_evaluate(df, MODELS_DIR, n_jobs=1)
    print("\nTraining summary:", summary)
    print("Saved models:", dept_path, prio_path)
