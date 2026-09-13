from collections.abc import Callable
from dataclasses import dataclass

from lightgbm import LGBMClassifier
from optuna.trial import Trial
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


@dataclass(frozen=True)
class AdvancedModelDefinition:
    """A reproducible advanced tree-model family and its Optuna search space."""

    name: str
    suggest_parameters: Callable[[Trial], dict[str, int | float | str]]
    factory: Callable[[dict[str, int | float | str], int], object]


def advanced_model_definitions() -> tuple[AdvancedModelDefinition, ...]:
    """Return the three tree-based model families within the Phase 6 scope."""
    return (
        AdvancedModelDefinition(
            name="random_forest",
            suggest_parameters=_suggest_random_forest_parameters,
            factory=_create_random_forest,
        ),
        AdvancedModelDefinition(
            name="xgboost",
            suggest_parameters=_suggest_xgboost_parameters,
            factory=_create_xgboost,
        ),
        AdvancedModelDefinition(
            name="lightgbm",
            suggest_parameters=_suggest_lightgbm_parameters,
            factory=_create_lightgbm,
        ),
    )


def _suggest_random_forest_parameters(trial: Trial) -> dict[str, int | float | str]:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2"]),
    }


def _create_random_forest(
    parameters: dict[str, int | float | str], random_state: int
) -> RandomForestClassifier:
    return RandomForestClassifier(**parameters, n_jobs=1, random_state=random_state)


def _suggest_xgboost_parameters(trial: Trial) -> dict[str, int | float | str]:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
    }


def _create_xgboost(parameters: dict[str, int | float | str], random_state: int) -> XGBClassifier:
    return XGBClassifier(
        **parameters,
        eval_metric="logloss",
        n_jobs=1,
        random_state=random_state,
        tree_method="hist",
    )


def _suggest_lightgbm_parameters(trial: Trial) -> dict[str, int | float | str]:
    max_depth = trial.suggest_int("max_depth", 3, 10)
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
        "num_leaves": trial.suggest_int("num_leaves", 7, min(63, 2**max_depth)),
        "max_depth": max_depth,
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 50),
    }


def _create_lightgbm(parameters: dict[str, int | float | str], random_state: int) -> LGBMClassifier:
    return LGBMClassifier(
        **parameters,
        n_jobs=1,
        random_state=random_state,
        verbosity=-1,
    )
