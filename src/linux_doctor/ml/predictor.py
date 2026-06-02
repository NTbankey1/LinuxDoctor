"""
Inference module — loads from-scratch trained model and predicts issue domain.

Uses pickle-serialized models trained by trainer.py (no sklearn dependency).
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from linux_doctor.infrastructure.logger import log
from linux_doctor.ml.text_engine import preprocess
from linux_doctor.ml.tfidf_engine import TFIDFVectorizer

MODEL_DIR = Path("models")
BEST_MODEL_PATH = MODEL_DIR / "best_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"

# Confidence threshold — below this, fallback to keyword routing
CONFIDENCE_THRESHOLD = 0.30


@dataclass(frozen=True)
class Prediction:
    """Result of a classification inference."""

    domain: str
    confidence: float
    all_scores: dict[str, float]
    method: str  # "ml_classifier" or "keyword_fallback"


class IssueClassifier:
    """
    Loads the best trained model (from scratch) and performs inference.

    Supports Naive Bayes, Logistic Regression, and Linear SVM.
    All serialized via pickle — no sklearn dependency at inference time.
    """

    def __init__(
        self,
        model_path: Path = BEST_MODEL_PATH,
        vectorizer_path: Path = VECTORIZER_PATH,
    ) -> None:
        """Load model and vectorizer from disk."""
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at '{model_path}'.\n"
                "Run: uv run python -m linux_doctor.ml.trainer"
            )
        if not vectorizer_path.exists():
            raise FileNotFoundError(f"Vectorizer not found at '{vectorizer_path}'.")

        with open(model_path, "rb") as f:
            self._model = pickle.load(f)
        with open(vectorizer_path, "rb") as f:
            self._vectorizer: TFIDFVectorizer = pickle.load(f)

        self._classes: list[str] = self._model.classes_
        log.debug(f"Classifier ready. Classes: {self._classes}")

    def predict(self, user_input: str) -> Prediction:
        """
        Predict the issue domain from a raw user input string.

        Args:
            user_input: Natural language description of the Linux issue.

        Returns:
            Prediction with domain, confidence, and all scores.
        """
        tokens = preprocess(user_input)
        X = self._vectorizer.transform([tokens])  # shape: (1, V)

        # Get probabilities (all models expose predict_proba)
        probs: np.ndarray = self._model.predict_proba(X)[0]  # shape: (n_classes,)
        all_scores = {
            cls: round(float(p), 4)
            for cls, p in sorted(
                zip(self._classes, probs, strict=False), key=lambda x: -x[1]
            )
        }
        best_domain = max(all_scores, key=all_scores.__getitem__)
        confidence = all_scores[best_domain]

        return Prediction(
            domain=best_domain,
            confidence=confidence,
            all_scores=all_scores,
            method="ml_classifier",
        )
