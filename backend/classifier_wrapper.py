# Add this to the bottom of ml_classifier.py (or put in a new file classifier_wrapper.py)

import os
import joblib
import numpy as np

# Adjust these paths if your models are saved elsewhere
DEFAULT_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DEPT_MODEL_NAME = "dept_pipeline.joblib"
PRIO_MODEL_NAME = "priority_pipeline.joblib"

class PetitionClassifier:
    """
    Lightweight wrapper that loads saved dept & priority pipelines and exposes
    a .classify(text) -> dict interface expected by app.py.
    """

    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or DEFAULT_MODELS_DIR
        self.dept_pipe = None
        self.prio_pipe = None
        self._load_models()

    def _model_path(self, filename):
        return os.path.join(self.models_dir, filename)

    def _load_models(self):
        dept_path = self._model_path(DEPT_MODEL_NAME)
        prio_path = self._model_path(PRIO_MODEL_NAME)

        if not os.path.exists(dept_path) or not os.path.exists(prio_path):
            raise FileNotFoundError(
                f"Model files not found. Expected:\n  {dept_path}\n  {prio_path}\n\n"
                "Please run your ml training script (ml_classifier.py) to generate models."
            )

        # Load joblib pipelines
        self.dept_pipe = joblib.load(dept_path)
        self.prio_pipe = joblib.load(prio_path)

    # If you used a preprocess function named clean_text in ml_classifier, reuse it.
    # Otherwise we provide a minimal consistent cleaning here.
    def _clean_text(self, s: str) -> str:
        if s is None:
            return ""
        try:
            # try to import clean_text from this module if present
            from ml_classifier import clean_text as shared_clean
            return shared_clean(s)
        except Exception:
            # fallback minimal cleaning
            import re
            s = str(s).lower()
            s = re.sub(r"http\S+", " ", s)
            s = re.sub(r"[^a-z0-9\s]", " ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

    def classify(self, text: str):
        """
        Returns a dict:
        {
          'department': <label>,
          'priority': <label>,
          'confidence': {'department': float, 'priority': float}
        }
        """
        cleaned = self._clean_text(text)

        # department prediction
        dept_pred = self.dept_pipe.predict([cleaned])[0]
        dept_conf = None
        try:
            dept_proba = self.dept_pipe.predict_proba([cleaned])[0]
            dept_conf = float(np.max(dept_proba))
        except Exception:
            # if predict_proba not available, try decision_function -> convert to pseudo-proba
            try:
                scores = self.dept_pipe.decision_function([cleaned])
                # if multiclass, decision_function returns (n_classes,) but scaling is arbitrary; fallback to 1.0
                dept_conf = float(np.max(scores)) if hasattr(scores, 'shape') else 1.0
            except Exception:
                dept_conf = 1.0

        # priority prediction
        prio_pred = self.prio_pipe.predict([cleaned])[0]
        prio_conf = None
        try:
            prio_proba = self.prio_pipe.predict_proba([cleaned])[0]
            prio_conf = float(np.max(prio_proba))
        except Exception:
            try:
                scores = self.prio_pipe.decision_function([cleaned])
                prio_conf = float(np.max(scores)) if hasattr(scores, 'shape') else 1.0
            except Exception:
                prio_conf = 1.0

        return {
            "department": str(dept_pred),
            "priority": str(prio_pred),
            "confidence": {
                "department": float(dept_conf),
                "priority": float(prio_conf)
            }
        }
