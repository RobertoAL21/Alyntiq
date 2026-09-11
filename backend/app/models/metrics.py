from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None

    def as_dict(self) -> dict[str, float | None]:
        return asdict(self)


def calculate_binary_metrics(
    target: pd.Series, probabilities: np.ndarray
) -> BinaryClassificationMetrics:
    """Calculate Phase 5 classification metrics without hiding undefined ROC-AUC values."""
    predictions = probabilities >= 0.5
    roc_auc = float(roc_auc_score(target, probabilities)) if target.nunique() == 2 else None
    return BinaryClassificationMetrics(
        accuracy=float(accuracy_score(target, predictions)),
        precision=float(precision_score(target, predictions, zero_division=0)),
        recall=float(recall_score(target, predictions, zero_division=0)),
        f1=float(f1_score(target, predictions, zero_division=0)),
        roc_auc=roc_auc,
    )
