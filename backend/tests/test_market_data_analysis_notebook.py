import json
from pathlib import Path


def test_market_data_analysis_notebook_covers_phase_two_scope() -> None:
    notebook_path = Path(__file__).parents[2] / "notebooks/exploration/market_data_analysis.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])

    for required_term in (
        "simple_returns",
        "log_returns",
        "rolling_volatility",
        "drawdowns",
        "return_correlation",
        "rolling_spy_correlation",
        "autocorrelation_lag_1",
        "moving_average_20",
        "regime_summary",
    ):
        assert required_term in source
