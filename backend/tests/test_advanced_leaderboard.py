from app.models.advanced_service import build_leaderboard
from app.models.advanced_types import AdvancedModelRunResult, OptimizationResult, OptimizationTrial
from app.models.metrics import BinaryClassificationMetrics
from app.models.service_types import FoldResult


def make_run(model_name: str, roc_auc: float, accuracy: float) -> AdvancedModelRunResult:
    return AdvancedModelRunResult(
        model_name=model_name,
        model_version="advanced-v1",
        row_count=100,
        optimization=OptimizationResult(
            best_parameters={"max_depth": 3},
            best_validation_roc_auc=0.5,
            trials=(OptimizationTrial(0, 0.5, {"max_depth": 3}),),
        ),
        holdout=FoldResult(
            number=3,
            train_rows=60,
            test_rows=30,
            metrics=BinaryClassificationMetrics(accuracy, accuracy, accuracy, accuracy, roc_auc),
        ),
        feature_importance={"feature_one": 1.0},
    )


def test_leaderboard_ranks_by_untouched_holdout_roc_auc() -> None:
    leaderboard = build_leaderboard(
        (
            make_run("random_forest", roc_auc=0.51, accuracy=0.5),
            make_run("xgboost", roc_auc=0.55, accuracy=0.49),
            make_run("lightgbm", roc_auc=0.53, accuracy=0.6),
        )
    )

    assert [entry.model_name for entry in leaderboard] == ["xgboost", "lightgbm", "random_forest"]
    assert [entry.rank for entry in leaderboard] == [1, 2, 3]
