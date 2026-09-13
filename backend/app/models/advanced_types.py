from dataclasses import dataclass

from app.models.service_types import FoldResult


@dataclass(frozen=True)
class OptimizationTrial:
    number: int
    value: float
    parameters: dict[str, int | float | str]


@dataclass(frozen=True)
class OptimizationResult:
    best_parameters: dict[str, int | float | str]
    best_validation_roc_auc: float
    trials: tuple[OptimizationTrial, ...]


@dataclass(frozen=True)
class AdvancedModelRunResult:
    model_name: str
    model_version: str
    row_count: int
    optimization: OptimizationResult
    holdout: FoldResult
    feature_importance: dict[str, float]


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    model_name: str
    holdout_roc_auc: float | None
    holdout_accuracy: float
