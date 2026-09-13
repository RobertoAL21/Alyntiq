import optuna
import pandas as pd

from app.models.advanced import AdvancedModelDefinition
from app.models.advanced_types import OptimizationResult, OptimizationTrial
from app.models.dataset import TrainingDataset
from app.models.metrics import calculate_binary_metrics
from app.models.validation import WalkForwardFold


class OptimizationError(ValueError):
    """Raised when temporal validation cannot score an advanced-model trial."""


def optimize_model(
    dataset: TrainingDataset,
    definition: AdvancedModelDefinition,
    validation_folds: list[WalkForwardFold],
    *,
    n_trials: int,
    random_state: int,
) -> OptimizationResult:
    """Optimize one model strictly on validation folds before its final holdout evaluation."""
    if n_trials < 1:
        raise OptimizationError("n_trials must be at least 1")
    if not validation_folds:
        raise OptimizationError("at least one validation fold is required for optimization")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=random_state)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    def objective(trial: optuna.trial.Trial) -> float:
        parameters = definition.suggest_parameters(trial)
        scores = []
        for fold in validation_folds:
            model = definition.factory(parameters, random_state + trial.number + fold.number)
            model.fit(
                dataset.features.iloc[fold.train_indices], dataset.target.iloc[fold.train_indices]
            )
            probabilities = model.predict_proba(dataset.features.iloc[fold.test_indices])[:, 1]
            metrics = calculate_binary_metrics(
                dataset.target.iloc[fold.test_indices], probabilities
            )
            if metrics.roc_auc is not None:
                scores.append(metrics.roc_auc)
        if not scores:
            raise OptimizationError("validation folds require both target classes for ROC-AUC")
        return float(pd.Series(scores).mean())

    study.optimize(objective, n_trials=n_trials)
    trials = tuple(
        OptimizationTrial(
            number=trial.number,
            value=float(trial.value),
            parameters={key: value for key, value in trial.params.items()},
        )
        for trial in study.trials
        if trial.value is not None
    )
    return OptimizationResult(
        best_parameters={key: value for key, value in study.best_params.items()},
        best_validation_roc_auc=float(study.best_value),
        trials=trials,
    )
