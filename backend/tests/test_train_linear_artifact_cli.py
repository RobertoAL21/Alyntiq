import pytest

from scripts.train_linear_artifact import build_parser


def test_linear_artifact_cli_requires_model_cutoff_and_path() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])

    arguments = parser.parse_args(
        [
            "--model-version",
            "linear-v1",
            "--training-end",
            "2024-12-31",
            "--artifact-path",
            "/tmp/linear-v1.json",
        ]
    )

    assert arguments.model_version == "linear-v1"
    assert arguments.training_end == "2024-12-31"
