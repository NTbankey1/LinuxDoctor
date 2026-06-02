"""
Evaluation Framework — Phase 6.

Computes Accuracy, Precision, Recall, F1-Score, and Confusion Matrix
from scratch without sklearn.metrics.

Formulas:
    Accuracy    = (TP + TN) / Total
                = Σ correct_predictions / m

    Precision_c = TP_c / (TP_c + FP_c)
    Recall_c    = TP_c / (TP_c + FN_c)
    F1_c        = 2 × (P_c × R_c) / (P_c + R_c)

    Macro-F1    = (1/|C|) × Σ F1_c
    Weighted-F1 = Σ (support_c / m) × F1_c
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class ClassMetrics:
    """Per-class evaluation metrics."""
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvaluationReport:
    """Full classification evaluation report."""
    accuracy: float
    per_class: list[ClassMetrics]
    macro_f1: float
    weighted_f1: float
    confusion_matrix: np.ndarray
    class_order: list[str]

    def print(self) -> None:
        """Print a formatted classification report to stdout."""
        print(f"\n{'='*62}")
        print(f"{'CLASSIFICATION REPORT':^62}")
        print(f"{'='*62}")
        print(f"{'Class':<15} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>8}")
        print(f"{'-'*62}")
        for cm in self.per_class:
            print(
                f"{cm.label:<15} {cm.precision:>10.4f} {cm.recall:>10.4f}"
                f" {cm.f1:>10.4f} {cm.support:>8}"
            )
        print(f"{'-'*62}")
        print(f"{'Accuracy':<15} {'':>10} {'':>10} {self.accuracy:>10.4f} {sum(c.support for c in self.per_class):>8}")
        print(f"{'Macro F1':<15} {'':>10} {'':>10} {self.macro_f1:>10.4f}")
        print(f"{'Weighted F1':<15} {'':>10} {'':>10} {self.weighted_f1:>10.4f}")
        print(f"{'='*62}\n")

        print("Confusion Matrix (row=true, col=pred):")
        print(f"{'':>12}", end="")
        for c in self.class_order:
            print(f"{c[:8]:>10}", end="")
        print()
        for i, c in enumerate(self.class_order):
            print(f"{c[:10]:<12}", end="")
            for j in range(len(self.class_order)):
                print(f"{int(self.confusion_matrix[i, j]):>10}", end="")
            print()
        print()


class Evaluator:
    """
    Computes classification metrics from scratch.

    Usage:
        evaluator = Evaluator()
        report = evaluator.evaluate(y_true, y_pred)
        report.print()
    """

    def evaluate(self, y_true: list[str], y_pred: list[str]) -> EvaluationReport:
        """
        Compute full evaluation report.

        Args:
            y_true: Ground truth labels.
            y_pred: Predicted labels.

        Returns:
            EvaluationReport with all metrics.
        """
        assert len(y_true) == len(y_pred), "Length mismatch between y_true and y_pred"

        classes = sorted(set(y_true) | set(y_pred))
        n_classes = len(classes)
        cls_to_idx = {c: i for i, c in enumerate(classes)}

        # Build confusion matrix: M[i][j] = true=i, pred=j
        m = len(y_true)
        cm = np.zeros((n_classes, n_classes), dtype=np.int64)
        correct = 0
        for true, pred in zip(y_true, y_pred, strict=False):
            i = cls_to_idx[true]
            j = cls_to_idx[pred]
            cm[i, j] += 1
            if true == pred:
                correct += 1

        accuracy = correct / m

        # Per-class metrics
        per_class: list[ClassMetrics] = []
        for i, cls in enumerate(classes):
            tp = int(cm[i, i])
            fp = int(cm[:, i].sum()) - tp   # all predicted as i - correctly predicted i
            fn = int(cm[i, :].sum()) - tp   # all true i - correctly predicted i
            support = int(cm[i, :].sum())

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1        = (2 * precision * recall / (precision + recall)
                         if (precision + recall) > 0 else 0.0)

            per_class.append(ClassMetrics(
                label=cls,
                precision=precision,
                recall=recall,
                f1=f1,
                support=support,
            ))

        total = sum(c.support for c in per_class)
        macro_f1 = sum(c.f1 for c in per_class) / n_classes
        weighted_f1 = sum(c.f1 * c.support for c in per_class) / total if total > 0 else 0.0

        return EvaluationReport(
            accuracy=accuracy,
            per_class=per_class,
            macro_f1=macro_f1,
            weighted_f1=weighted_f1,
            confusion_matrix=cm,
            class_order=classes,
        )
