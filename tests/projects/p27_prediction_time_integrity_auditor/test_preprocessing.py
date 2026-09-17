from __future__ import annotations

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.preprocessing import (
    column_groups,
    histogram_preprocessor,
    logistic_preprocessor,
    pipeline_b_features,
    pipeline_c_features,
)


def test_pipeline_b_removes_duration_but_remains_partial() -> None:
    features = pipeline_b_features()

    assert "duration" not in features
    assert "campaign" in features
    assert len(features) == 19


def test_pipeline_c_contains_only_prediction_time_safe_features() -> None:
    features = pipeline_c_features()

    assert "duration" not in features
    assert "campaign" not in features
    assert len(features) == 18


def test_column_groups_are_complete_and_disjoint() -> None:
    features = pipeline_c_features()

    numeric, categorical = column_groups(features)

    assert set(numeric).isdisjoint(categorical)

    assert set(numeric) | set(categorical) == set(features)


def test_both_preprocessors_build() -> None:
    features = pipeline_c_features()

    logistic = logistic_preprocessor(features)

    histogram = histogram_preprocessor(features)

    logistic_params = logistic.get_params(deep=False)

    histogram_params = histogram.get_params(deep=False)

    assert logistic_params["remainder"] == "drop"

    assert histogram_params["remainder"] == "drop"

    assert histogram_params["sparse_threshold"] == 0.0
