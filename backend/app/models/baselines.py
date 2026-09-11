from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


class RandomBaselineClassifier:
    """Predict a reproducible random probability for each observation."""

    def __init__(self, random_state: int) -> None:
        self._random_state = random_state

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "RandomBaselineClassifier":
        return self

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        probabilities = np.random.default_rng(self._random_state).random(len(features))
        return np.column_stack((1 - probabilities, probabilities))


class MajorityClassClassifier:
    """Always predict the most common class observed in the training window."""

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "MajorityClassClassifier":
        self._positive_class = bool(target.mean() >= 0.5)
        return self

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        probability = float(self._positive_class)
        probabilities = np.full(len(features), probability)
        return np.column_stack((1 - probabilities, probabilities))


@dataclass(frozen=True)
class BaselineDefinition:
    name: str
    parameters: dict[str, str | int | float | bool]
    factory: Callable[[int], object]


def baseline_definitions() -> tuple[BaselineDefinition, ...]:
    """Return the fixed, intentionally simple models required for Phase 5."""
    return (
        BaselineDefinition(
            name="random",
            parameters={"random_state": "per-fold"},
            factory=lambda random_state: RandomBaselineClassifier(random_state),
        ),
        BaselineDefinition(
            name="majority_class",
            parameters={},
            factory=lambda random_state: MajorityClassClassifier(),
        ),
        BaselineDefinition(
            name="logistic_regression",
            parameters={"max_iter": 1_000, "random_state": "per-fold"},
            factory=lambda random_state: make_pipeline(
                StandardScaler(), LogisticRegression(max_iter=1_000, random_state=random_state)
            ),
        ),
        BaselineDefinition(
            name="decision_tree",
            parameters={"random_state": "per-fold"},
            factory=lambda random_state: DecisionTreeClassifier(random_state=random_state),
        ),
    )
