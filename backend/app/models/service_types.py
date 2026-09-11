from dataclasses import dataclass

from app.models.metrics import BinaryClassificationMetrics


@dataclass(frozen=True)
class FoldResult:
    number: int
    train_rows: int
    test_rows: int
    metrics: BinaryClassificationMetrics


@dataclass(frozen=True)
class BaselineRunResult:
    model_name: str
    model_version: str
    parameters: dict[str, str | int | float | bool]
    row_count: int
    folds: tuple[FoldResult, ...]
    average_metrics: dict[str, float | None]
