import argparse
import json

import pandas as pd

from app.drift import DriftConfig, DriftDetectionError, DriftDetectionService
from app.regimes.types import MarketRegime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare a training reference sample with a later sample for drift"
    )
    parser.add_argument("--reference-features", required=True)
    parser.add_argument("--current-features", required=True)
    parser.add_argument(
        "--feature-columns",
        required=True,
        help="Comma-separated model feature columns to compare in both CSV files",
    )
    parser.add_argument("--reference-predictions")
    parser.add_argument("--current-predictions")
    parser.add_argument("--prediction-column", default="prediction")
    parser.add_argument("--reference-volatility")
    parser.add_argument("--current-volatility")
    parser.add_argument("--volatility-column", default="volatility")
    parser.add_argument("--reference-regimes")
    parser.add_argument("--current-regimes")
    parser.add_argument("--regime-column", default="market_regime")
    parser.add_argument("--distribution-bins", default=10, type=int)
    parser.add_argument("--feature-psi-threshold", default=0.2, type=float)
    parser.add_argument("--prediction-psi-threshold", default=0.2, type=float)
    parser.add_argument("--volatility-relative-change-threshold", default=0.3, type=float)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    feature_columns = tuple(
        column.strip() for column in arguments.feature_columns.split(",") if column.strip()
    )
    if not feature_columns:
        raise SystemExit("Drift detection failed: --feature-columns must not be empty")
    try:
        report = DriftDetectionService(
            DriftConfig(
                distribution_bins=arguments.distribution_bins,
                feature_psi_threshold=arguments.feature_psi_threshold,
                prediction_psi_threshold=arguments.prediction_psi_threshold,
                volatility_relative_change_threshold=arguments.volatility_relative_change_threshold,
            )
        ).evaluate(
            reference_features=_read_columns(arguments.reference_features, feature_columns),
            current_features=_read_columns(arguments.current_features, feature_columns),
            reference_predictions=_optional_series(
                arguments.reference_predictions, arguments.prediction_column
            ),
            current_predictions=_optional_series(
                arguments.current_predictions, arguments.prediction_column
            ),
            reference_volatility=_optional_series(
                arguments.reference_volatility, arguments.volatility_column
            ),
            current_volatility=_optional_series(
                arguments.current_volatility, arguments.volatility_column
            ),
            reference_regimes=_optional_regimes(
                arguments.reference_regimes, arguments.regime_column
            ),
            current_regimes=_optional_regimes(arguments.current_regimes, arguments.regime_column),
        )
    except (DriftDetectionError, OSError, ValueError) as error:
        raise SystemExit(f"Drift detection failed: {error}") from error

    print(
        json.dumps(
            {
                "feature_distributions": [
                    {
                        "name": item.name,
                        "population_stability_index": item.population_stability_index,
                        "drifted": item.drifted,
                    }
                    for item in report.feature_distributions
                ],
                "prediction_distribution": _distribution_output(report.prediction_distribution),
                "volatility": _volatility_output(report.volatility),
                "market_regime": _regime_output(report.market_regime),
                "alerts": [
                    {
                        "kind": alert.kind.value,
                        "subject": alert.subject,
                        "value": alert.value,
                        "threshold": alert.threshold,
                    }
                    for alert in report.alerts
                ],
            }
        )
    )
    return 0


def _read_columns(path: str, columns: tuple[str, ...]) -> pd.DataFrame:
    return pd.read_csv(path, usecols=list(columns)).loc[:, columns]


def _optional_series(path: str | None, column: str) -> pd.Series | None:
    if path is None:
        return None
    return pd.read_csv(path, usecols=[column])[column]


def _optional_regimes(path: str | None, column: str) -> tuple[MarketRegime, ...] | None:
    if path is None:
        return None
    return tuple(MarketRegime(value) for value in _optional_series(path, column).tolist())


def _distribution_output(item: object) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "population_stability_index": item.population_stability_index,
        "drifted": item.drifted,
    }


def _volatility_output(item: object) -> dict[str, object] | None:
    if item is None:
        return None
    return {"relative_change": item.relative_change, "drifted": item.drifted}


def _regime_output(item: object) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "reference_regime": item.reference_regime.value,
        "current_regime": item.current_regime.value,
        "changed": item.changed,
    }


if __name__ == "__main__":
    raise SystemExit(main())
