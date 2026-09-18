"""Independent final-benchmark validation for Project 7."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final

STEP2_FINGERPRINT: Final = "87d57e0824657a5984a867ee3456b5a999e2bbac516f3b772b94a0e47a014abf"

STEP3_FINGERPRINT: Final = "99bfafda40ff9404cddbcc48b454708f2bc9efe3e8742b174471d3a6d6f2da84"

STEP4_FINGERPRINT: Final = "3c5911590409ef4de9beec2f7a960f951f4510b3ec5383b1381f5fc559044032"

EXPECTED_CASE_IDS: Final[tuple[str, ...]] = (
    "S1_CURRENT_CALL_DURATION",
    "S2_RANDOM_TEMPORAL_MIXING",
    "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
    "S4_DUPLICATE_OVERLAP",
    "S5_POST_OUTCOME_CONFIRMATION_PROXY",
)

EXPECTED_MODEL_IDS: Final[frozenset[str]] = frozenset(
    {
        "logistic_regression",
        "histogram_gradient_boosting",
    }
)

ALLOWED_CLAIM_LABELS: Final[frozenset[str]] = frozenset(
    {
        "MEASURED",
        "DERIVED",
        "CONTROLLED_INJECTION",
        "PROJECT_DEFINED_METRIC",
        "INTERPRETATION",
        "LIMITATION",
        "FUTURE_WORK",
        "PREVIEW_ONLY",
        "UNSUPPORTED",
    }
)

HIGHER_IS_BETTER: Final[frozenset[str]] = frozenset(
    {
        "roc_auc",
        "pr_auc",
        "top_decile_response_rate",
        "top_decile_lift",
        "conversions_per_1000",
    }
)

LOWER_IS_BETTER: Final[frozenset[str]] = frozenset(
    {
        "brier_score",
        "expected_calibration_error",
        "false_positive_contacts",
    }
)

DIRECT_COMPARE_METRICS: Final[tuple[str, ...]] = (
    "roc_auc",
    "pr_auc",
    "brier_score",
    "expected_calibration_error",
    "top_decile_response_rate",
    "top_decile_lift",
    "conversions_per_1000",
    "false_positive_contacts",
    "target_prevalence",
    "calibration_slope",
    "calibration_intercept",
)

REPORTED_EFFECT_KEYS: Final[dict[str, str]] = {
    "roc_auc": "roc_auc",
    "pr_auc": "pr_auc",
    "brier_score": "brier_score_raw_difference",
    "expected_calibration_error": ("expected_calibration_error_raw_difference"),
    "top_decile_lift": "top_decile_lift",
    "conversions_per_1000": "conversions_per_1000",
}


@dataclass(frozen=True, slots=True)
class MetricReconciliation:
    """One independently recomputed Step 3 metric effect."""

    case_id: str
    model_id: str
    metric: str
    safe_value: float
    leaked_value: float
    reported_effect: float
    recomputed_effect: float
    difference: float
    reconciled: bool

    def to_dict(
        self,
    ) -> dict[str, object]:
        """Serialize one reconciliation row."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class IndependentValidation:
    """Critical Step 5 independent-validation summary."""

    status: str
    scenario_count: int
    model_result_count: int
    reconciled_metric_effect_count: int
    metric_effect_mismatch_count: int
    safe_release_status: str
    no_false_pass: bool
    duplicate_train_test_overlap: int
    temporal_roc_auc_gap: float
    temporal_pr_auc_gap: float
    campaign_yield_overstatement_values: tuple[float, ...]

    def to_dict(
        self,
    ) -> dict[str, object]:
        """Serialize validation summary using JSON-native values."""

        return {
            "status": self.status,
            "scenario_count": self.scenario_count,
            "model_result_count": self.model_result_count,
            "reconciled_metric_effect_count": (self.reconciled_metric_effect_count),
            "metric_effect_mismatch_count": (self.metric_effect_mismatch_count),
            "safe_release_status": self.safe_release_status,
            "no_false_pass": self.no_false_pass,
            "duplicate_train_test_overlap": (self.duplicate_train_test_overlap),
            "temporal_roc_auc_gap": self.temporal_roc_auc_gap,
            "temporal_pr_auc_gap": self.temporal_pr_auc_gap,
            "campaign_yield_overstatement_values": list(self.campaign_yield_overstatement_values),
        }


def load_json(
    path: Path,
) -> dict[str, Any]:
    """Load one required JSON object."""

    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(f"Expected JSON object: {path}")

    return payload


def canonical_sha256(
    payload: Mapping[str, Any],
) -> str:
    """Hash canonical JSON."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def file_sha256(
    path: Path,
) -> str:
    """Hash file content."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def _assert_close(
    left: float,
    right: float,
    *,
    absolute_tolerance: float = 1.0e-12,
) -> bool:
    """Return deterministic numeric reconciliation result."""

    return math.isclose(
        left,
        right,
        rel_tol=1.0e-12,
        abs_tol=absolute_tolerance,
    )


def normalize_cases(
    leakage_results: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Normalize frozen Step 3 list into case-id mapping."""

    raw = leakage_results.get("cases")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("Step 3 cases must be a list.")

    if len(raw) != 5:
        raise RuntimeError(f"Expected 5 Step 3 cases; found {len(raw)}.")

    normalized: dict[
        str,
        dict[str, Any],
    ] = {}

    ordered_ids: list[str] = []

    for item in raw:
        if not isinstance(
            item,
            dict,
        ):
            raise RuntimeError("Step 3 case must be an object.")

        case_id = str(
            item.get(
                "case_id",
                "",
            )
        )

        if not case_id:
            raise RuntimeError("Step 3 case missing case_id.")

        if case_id in normalized:
            raise RuntimeError(f"Duplicate case_id: {case_id}")

        normalized[case_id] = item

        ordered_ids.append(case_id)

    if tuple(ordered_ids) != EXPECTED_CASE_IDS:
        raise RuntimeError("Frozen Step 3 scenario order drift.")

    return normalized


def baseline_metric_rows(
    baseline: Mapping[str, Any],
) -> list[dict[str, object]]:
    """Normalize all eight frozen Step 2 evaluations."""

    raw = baseline.get("evaluations")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("Baseline evaluations missing.")

    if len(raw) != 8:
        raise RuntimeError(f"Expected 8 baseline evaluations; found {len(raw)}.")

    rows: list[dict[str, object]] = []

    for evaluation in raw:
        if not isinstance(
            evaluation,
            dict,
        ):
            raise RuntimeError("Baseline evaluation must be an object.")

        metrics = evaluation.get("metrics")

        if not isinstance(
            metrics,
            dict,
        ):
            raise RuntimeError("Baseline evaluation metrics missing.")

        row: dict[str, object] = {
            "pipeline_id": str(
                evaluation.get(
                    "pipeline_id",
                    "",
                )
            ),
            "model_id": str(
                evaluation.get(
                    "model_id",
                    "",
                )
            ),
            "partition": str(
                evaluation.get(
                    "partition",
                    "",
                )
            ),
            "feature_count": int(
                evaluation.get(
                    "feature_count",
                    0,
                )
            ),
            "train_rows": int(
                evaluation.get(
                    "train_rows",
                    0,
                )
            ),
            "evaluation_rows": int(
                evaluation.get(
                    "evaluation_rows",
                    0,
                )
            ),
        }

        for key, value in sorted(metrics.items()):
            if isinstance(
                value,
                (int, float),
            ) and not isinstance(
                value,
                bool,
            ):
                row[key] = value

        rows.append(row)

    rows.sort(
        key=lambda row: (
            str(row["pipeline_id"]),
            str(row["partition"]),
            str(row["model_id"]),
        )
    )

    return rows


def leakage_model_rows(
    leakage_results: Mapping[str, Any],
) -> list[dict[str, object]]:
    """Normalize ten frozen Step 3 model/case results."""

    cases = normalize_cases(leakage_results)

    rows: list[dict[str, object]] = []

    for case_id in EXPECTED_CASE_IDS:
        case = cases[case_id]

        model_results = case.get("model_results")

        if (
            not isinstance(
                model_results,
                list,
            )
            or len(model_results) != 2
        ):
            raise RuntimeError(f"{case_id}: expected two model_results.")

        for result in model_results:
            if not isinstance(
                result,
                dict,
            ):
                raise RuntimeError(f"{case_id}: invalid model result.")

            model_id = str(
                result.get(
                    "model_id",
                    "",
                )
            )

            if model_id not in EXPECTED_MODEL_IDS:
                raise RuntimeError(f"Unexpected model_id: {model_id}")

            safe = result.get("safe_metrics")

            leaked = result.get("leaked_metrics")

            effect = result.get("metric_effect")

            if not isinstance(
                safe,
                dict,
            ):
                raise RuntimeError(f"{case_id}/{model_id}: safe_metrics missing.")

            if not isinstance(
                leaked,
                dict,
            ):
                raise RuntimeError(f"{case_id}/{model_id}: leaked_metrics missing.")

            if not isinstance(
                effect,
                dict,
            ):
                raise RuntimeError(f"{case_id}/{model_id}: metric_effect missing.")

            row: dict[str, object] = {
                "case_id": case_id,
                "model_id": model_id,
                "evidence_class": str(
                    case.get(
                        "evidence_class",
                        "",
                    )
                ),
                "observed_or_injected": str(
                    case.get(
                        "observed_or_injected",
                        "",
                    )
                ),
                "actual_auditor_result": str(
                    case.get(
                        "actual_auditor_result",
                        "",
                    )
                ),
                "expected_auditor_result": str(
                    case.get(
                        "expected_auditor_result",
                        "",
                    )
                ),
                "campaign_yield_overstatement": float(
                    result.get(
                        "campaign_yield_overstatement",
                        0.0,
                    )
                ),
            }

            for metric in DIRECT_COMPARE_METRICS:
                if metric in safe:
                    row[f"safe_{metric}"] = safe[metric]

                if metric in leaked:
                    row[f"leaked_{metric}"] = leaked[metric]

            for key, value in sorted(effect.items()):
                if isinstance(
                    value,
                    (int, float),
                ) and not isinstance(
                    value,
                    bool,
                ):
                    row[f"reported_effect_{key}"] = value

            rows.append(row)

    rows.sort(
        key=lambda row: (
            str(row["case_id"]),
            str(row["model_id"]),
        )
    )

    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 case/model rows; found {len(rows)}.")

    return rows


def _raw_effect(
    metric: str,
    safe_value: float,
    leaked_value: float,
) -> float:
    """Recompute Step 3 raw leaked-minus-safe effect."""

    return leaked_value - safe_value


def leakage_inflation_value(
    metric: str,
    safe_value: float,
    leaked_value: float,
) -> float:
    """Return direction-normalized leakage inflation.

    Positive means the leaked configuration appears better.
    """

    if metric in HIGHER_IS_BETTER:
        return leaked_value - safe_value

    if metric in LOWER_IS_BETTER:
        return safe_value - leaked_value

    raise ValueError(f"No leakage-inflation direction for {metric}.")


def reconcile_metric_effects(
    leakage_results: Mapping[str, Any],
) -> list[MetricReconciliation]:
    """Independently recompute and reconcile every reported metric effect."""

    cases = normalize_cases(leakage_results)

    rows: list[MetricReconciliation] = []

    for case_id in EXPECTED_CASE_IDS:
        case = cases[case_id]

        model_results = case["model_results"]

        assert isinstance(
            model_results,
            list,
        )

        for result in model_results:
            assert isinstance(
                result,
                dict,
            )

            model_id = str(result["model_id"])

            safe = result["safe_metrics"]

            leaked = result["leaked_metrics"]

            reported = result["metric_effect"]

            if not isinstance(
                safe,
                dict,
            ):
                raise RuntimeError("safe_metrics invalid.")

            if not isinstance(
                leaked,
                dict,
            ):
                raise RuntimeError("leaked_metrics invalid.")

            if not isinstance(
                reported,
                dict,
            ):
                raise RuntimeError("metric_effect invalid.")

            for source_metric, reported_key in REPORTED_EFFECT_KEYS.items():
                safe_value = float(safe[source_metric])

                leaked_value = float(leaked[source_metric])

                reported_value = float(reported[reported_key])

                recomputed = _raw_effect(
                    source_metric,
                    safe_value,
                    leaked_value,
                )

                delta = recomputed - reported_value

                rows.append(
                    MetricReconciliation(
                        case_id=case_id,
                        model_id=model_id,
                        metric=source_metric,
                        safe_value=safe_value,
                        leaked_value=leaked_value,
                        reported_effect=reported_value,
                        recomputed_effect=recomputed,
                        difference=delta,
                        reconciled=_assert_close(
                            recomputed,
                            reported_value,
                        ),
                    )
                )

    rows.sort(
        key=lambda row: (
            row.case_id,
            row.model_id,
            row.metric,
        )
    )

    return rows


def leakage_inflation_rows(
    leakage_results: Mapping[str, Any],
) -> list[dict[str, object]]:
    """Calculate direction-normalized leakage-inflation values."""

    cases = normalize_cases(leakage_results)

    rows: list[dict[str, object]] = []

    directional_metrics = tuple(sorted(HIGHER_IS_BETTER | LOWER_IS_BETTER))

    for case_id in EXPECTED_CASE_IDS:
        model_results = cases[case_id]["model_results"]

        assert isinstance(
            model_results,
            list,
        )

        for result in model_results:
            assert isinstance(
                result,
                dict,
            )

            model_id = str(result["model_id"])

            safe = result["safe_metrics"]

            leaked = result["leaked_metrics"]

            assert isinstance(
                safe,
                dict,
            )

            assert isinstance(
                leaked,
                dict,
            )

            for metric in directional_metrics:
                if metric not in safe or metric not in leaked:
                    continue

                safe_value = float(safe[metric])

                leaked_value = float(leaked[metric])

                direction = "HIGHER_IS_BETTER" if metric in HIGHER_IS_BETTER else "LOWER_IS_BETTER"

                rows.append(
                    {
                        "case_id": case_id,
                        "model_id": model_id,
                        "metric": metric,
                        "direction": direction,
                        "safe_value": safe_value,
                        "leaked_value": leaked_value,
                        "leakage_inflation": (
                            leakage_inflation_value(
                                metric,
                                safe_value,
                                leaked_value,
                            )
                        ),
                    }
                )

    rows.sort(
        key=lambda row: (
            str(row["case_id"]),
            str(row["model_id"]),
            str(row["metric"]),
        )
    )

    return rows


def _case(
    leakage_results: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    """Fetch one frozen scenario by case ID."""

    return normalize_cases(leakage_results)[case_id]


def temporal_gap(
    leakage_results: Mapping[str, Any],
    metric: str,
) -> float:
    """Recompute the maximum Step 3 temporal comparison gap."""

    case = _case(
        leakage_results,
        "S2_RANDOM_TEMPORAL_MIXING",
    )

    model_results = case["model_results"]

    assert isinstance(
        model_results,
        list,
    )

    values: list[float] = []

    for result in model_results:
        assert isinstance(
            result,
            dict,
        )

        effect = result["metric_effect"]

        assert isinstance(
            effect,
            dict,
        )

        values.append(float(effect[metric]))

    return max(values)


def campaign_yield_overstatement_values(
    leakage_results: Mapping[str, Any],
) -> tuple[float, ...]:
    """Collect all independently checked campaign-yield overstatements."""

    cases = normalize_cases(leakage_results)

    values: list[float] = []

    for case_id in EXPECTED_CASE_IDS:
        results = cases[case_id]["model_results"]

        assert isinstance(
            results,
            list,
        )

        for result in results:
            assert isinstance(
                result,
                dict,
            )

            leaked = result["leaked_metrics"]

            safe = result["safe_metrics"]

            assert isinstance(
                leaked,
                dict,
            )

            assert isinstance(
                safe,
                dict,
            )

            recomputed = float(leaked["conversions_per_1000"]) - float(safe["conversions_per_1000"])

            reported = float(result["campaign_yield_overstatement"])

            if not _assert_close(
                recomputed,
                reported,
            ):
                raise RuntimeError(
                    f"Campaign-yield overstatement mismatch: {case_id}/{result['model_id']}"
                )

            values.append(recomputed)

    return tuple(values)


def duplicate_overlap(
    leakage_results: Mapping[str, Any],
) -> int:
    """Read and validate S4 duplicate-overlap evidence."""

    case = _case(
        leakage_results,
        "S4_DUPLICATE_OVERLAP",
    )

    business = case.get("business_effect")

    if not isinstance(
        business,
        dict,
    ):
        raise RuntimeError("S4 business_effect missing.")

    value = business.get("detected_train_test_overlap")

    if not isinstance(
        value,
        int,
    ):
        raise RuntimeError("S4 detected_train_test_overlap missing.")

    return value


def safe_release_status(
    audit_findings: Mapping[str, Any],
) -> str:
    """Return frozen safe-pipeline release status."""

    safe = audit_findings.get("safe_pipeline")

    if not isinstance(
        safe,
        dict,
    ):
        raise RuntimeError("safe_pipeline missing.")

    decision = safe.get("release_decision")

    if not isinstance(
        decision,
        dict,
    ):
        raise RuntimeError("release_decision missing.")

    return str(
        decision.get(
            "status",
            "",
        )
    )


def no_false_pass(
    audit_findings: Mapping[str, Any],
) -> bool:
    """Ensure no frozen Step 3 violation received PASS."""

    findings = audit_findings.get("scenario_reconciliation")

    if (
        not isinstance(
            findings,
            list,
        )
        or len(findings) != 5
    ):
        raise RuntimeError("Expected five scenario reconciliation findings.")

    return all(
        isinstance(
            finding,
            dict,
        )
        and finding.get("status")
        in {
            "WARN",
            "BLOCK",
        }
        for finding in findings
    )


def validate_source_fingerprints(
    baseline: Mapping[str, Any],
    leakage_results: Mapping[str, Any],
    audit_findings: Mapping[str, Any],
) -> None:
    """Require exact Step 2-4 source fingerprints."""

    if baseline.get("baseline_fingerprint_sha256") != STEP2_FINGERPRINT:
        raise RuntimeError("Step 2 baseline fingerprint drift.")

    if leakage_results.get("step3_fingerprint_sha256") != STEP3_FINGERPRINT:
        raise RuntimeError("Step 3 fingerprint drift.")

    if audit_findings.get("step4_fingerprint_sha256") != STEP4_FINGERPRINT:
        raise RuntimeError("Step 4 fingerprint drift.")


def independently_validate(
    baseline: Mapping[str, Any],
    leakage_results: Mapping[str, Any],
    audit_findings: Mapping[str, Any],
) -> tuple[
    IndependentValidation,
    list[MetricReconciliation],
]:
    """Run Step 5 independent critical-metric validation."""

    validate_source_fingerprints(
        baseline,
        leakage_results,
        audit_findings,
    )

    cases = normalize_cases(leakage_results)

    reconciliation = reconcile_metric_effects(leakage_results)

    mismatches = [row for row in reconciliation if not row.reconciled]

    campaign_values = campaign_yield_overstatement_values(leakage_results)

    safe_status = safe_release_status(audit_findings)

    false_pass_ok = no_false_pass(audit_findings)

    overlap = duplicate_overlap(leakage_results)

    model_result_count = sum(len(case["model_results"]) for case in cases.values())

    status = (
        "PASS"
        if (
            len(cases) == 5
            and model_result_count == 10
            and not mismatches
            and safe_status == "PASS"
            and false_pass_ok
            and overlap > 0
        )
        else "BLOCK"
    )

    return (
        IndependentValidation(
            status=status,
            scenario_count=len(cases),
            model_result_count=model_result_count,
            reconciled_metric_effect_count=len(reconciliation) - len(mismatches),
            metric_effect_mismatch_count=len(mismatches),
            safe_release_status=safe_status,
            no_false_pass=false_pass_ok,
            duplicate_train_test_overlap=overlap,
            temporal_roc_auc_gap=temporal_gap(
                leakage_results,
                "roc_auc",
            ),
            temporal_pr_auc_gap=temporal_gap(
                leakage_results,
                "pr_auc",
            ),
            campaign_yield_overstatement_values=campaign_values,
        ),
        reconciliation,
    )


def assert_no_preview_contamination(
    payload: Mapping[str, Any],
) -> None:
    """Reject preview-only data from final release payloads."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
    ).lower()

    if "preview_only" in encoded or "preview_metric" in encoded:
        raise RuntimeError("Preview-only data entered final release.")


def build_release_data(
    baseline: Mapping[str, Any],
    leakage_results: Mapping[str, Any],
    audit_findings: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic Step 5 release data."""

    validation, reconciliation = independently_validate(
        baseline,
        leakage_results,
        audit_findings,
    )

    if validation.status != "PASS":
        raise RuntimeError("Independent Step 5 validation blocked release.")

    payload: dict[str, Any] = {
        "scope": "PROJECT7_STEP5_FINAL_BENCHMARK",
        "release_status": "PASS",
        "source_fingerprints": {
            "step2_baseline": STEP2_FINGERPRINT,
            "step3_cases": STEP3_FINGERPRINT,
            "step4_auditor": STEP4_FINGERPRINT,
        },
        "baseline_model_results": (baseline_metric_rows(baseline)),
        "leakage_model_results": (leakage_model_rows(leakage_results)),
        "leakage_inflation": (leakage_inflation_rows(leakage_results)),
        "metric_effect_reconciliation": [row.to_dict() for row in reconciliation],
        "independent_validation": (validation.to_dict()),
        "safe_release_decision": (validation.safe_release_status),
        "public_artifacts_generated": False,
        "step6_started": False,
    }

    assert_no_preview_contamination(payload)

    payload["step5_fingerprint_sha256"] = canonical_sha256(payload)

    return payload


def build_claim_register(
    release_data: Mapping[str, Any],
    leakage_results: Mapping[str, Any],
) -> dict[str, Any]:
    """Build evidence-linked final claim register."""

    validation = release_data.get("independent_validation")

    if not isinstance(
        validation,
        dict,
    ):
        raise RuntimeError("Independent validation missing.")

    cases = normalize_cases(leakage_results)

    claims: list[dict[str, Any]] = [
        {
            "claim_id": "P7-C001",
            "claim_label": "MEASURED",
            "claim": ("Prediction-time-safe Pipeline C passed the Step 4 release gate."),
            "evidence": [
                "audit_findings.json#safe_pipeline.release_decision",
                "release_data.json#safe_release_decision",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C002",
            "claim_label": "MEASURED",
            "claim": (
                "The source dataset contains the current-call "
                "duration condition evaluated in scenario S1."
            ),
            "evidence": [
                "leakage_case_results.json#S1_CURRENT_CALL_DURATION",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C003",
            "claim_label": "DERIVED",
            "claim": ("Random-versus-temporal evaluation produces a measurable ROC-AUC gap."),
            "value": validation["temporal_roc_auc_gap"],
            "evidence": [
                "leakage_case_results.json#S2_RANDOM_TEMPORAL_MIXING",
                "release_data.json#independent_validation.temporal_roc_auc_gap",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C004",
            "claim_label": "DERIVED",
            "claim": ("Random-versus-temporal evaluation produces a measurable PR-AUC gap."),
            "value": validation["temporal_pr_auc_gap"],
            "evidence": [
                "leakage_case_results.json#S2_RANDOM_TEMPORAL_MIXING",
                "release_data.json#independent_validation.temporal_pr_auc_gap",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C005",
            "claim_label": "CONTROLLED_INJECTION",
            "claim": (
                "Scenario S3 is a controlled global supervised transformation integrity violation."
            ),
            "evidence": [
                "leakage_case_results.json#S3_GLOBAL_SUPERVISED_TRANSFORMATION",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C006",
            "claim_label": "CONTROLLED_INJECTION",
            "claim": ("Scenario S4 is a controlled duplicate-overlap integrity violation."),
            "value": validation["duplicate_train_test_overlap"],
            "evidence": [
                "leakage_case_results.json#S4_DUPLICATE_OVERLAP",
                "release_data.json#independent_validation.duplicate_train_test_overlap",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C007",
            "claim_label": "CONTROLLED_INJECTION",
            "claim": (
                "Scenario S5 is a controlled post-outcome confirmation-proxy integrity violation."
            ),
            "evidence": [
                "leakage_case_results.json#S5_POST_OUTCOME_CONFIRMATION_PROXY",
            ],
            "approved_for_public_use": True,
        },
        {
            "claim_id": "P7-C008",
            "claim_label": "DERIVED",
            "claim": (
                "All reported Step 3 model-level metric effects "
                "reconcile independently from safe and leaked metrics."
            ),
            "value": (validation["metric_effect_mismatch_count"] == 0),
            "evidence": [
                "release_data.json#metric_effect_reconciliation",
            ],
            "approved_for_public_use": True,
        },
    ]

    if cases["S1_CURRENT_CALL_DURATION"]["observed_or_injected"] != "OBSERVED":
        raise RuntimeError("S1 observed/injected label drift.")

    for case_id in (
        "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
        "S4_DUPLICATE_OVERLAP",
        "S5_POST_OUTCOME_CONFIRMATION_PROXY",
    ):
        observed_or_injected = str(
            cases[case_id].get(
                "observed_or_injected",
                "",
            )
        )

        if (
            "INJECT" not in observed_or_injected.upper()
            and "CONTROL" not in observed_or_injected.upper()
        ):
            raise RuntimeError(f"{case_id} is not labeled as injected.")

    for claim in claims:
        label = str(claim["claim_label"])

        if label not in ALLOWED_CLAIM_LABELS:
            raise RuntimeError(f"Invalid claim label: {label}")

        evidence = claim.get("evidence")

        if (
            not isinstance(
                evidence,
                list,
            )
            or not evidence
        ):
            raise RuntimeError(f"{claim['claim_id']} missing evidence.")

    payload: dict[str, Any] = {
        "scope": "PROJECT7_STEP5_CLAIM_REGISTER",
        "claims": claims,
        "claim_count": len(claims),
        "preview_claims_approved": False,
        "unsupported_claims_approved": False,
    }

    payload["claim_register_fingerprint_sha256"] = canonical_sha256(payload)

    return payload


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    """Write deterministic UTF-8 CSV."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not rows:
        raise RuntimeError(f"Refusing empty result table: {path.name}")

    fieldnames = sorted({key for row in rows for key in row})

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def freeze_step5_release(
    assets_root: Path,
) -> dict[str, Any]:
    """Freeze deterministic Step 5 benchmark evidence."""

    baseline = load_json(assets_root / "baseline_results.json")

    leakage = load_json(assets_root / "leakage_case_results.json")

    audit = load_json(assets_root / "audit_findings.json")

    release = build_release_data(
        baseline,
        leakage,
        audit,
    )

    claims = build_claim_register(
        release,
        leakage,
    )

    release_path = assets_root / "release_data.json"

    claims_path = assets_root / "claim_register.json"

    baseline_table = assets_root / "benchmark_model_results.csv"

    leakage_table = assets_root / "leakage_model_results.csv"

    inflation_table = assets_root / "leakage_inflation_results.csv"

    reconciliation_table = assets_root / "independent_reconciliation.csv"

    release_path.write_text(
        json.dumps(
            release,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    claims_path.write_text(
        json.dumps(
            claims,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    write_csv(
        baseline_table,
        baseline_metric_rows(baseline),
    )

    write_csv(
        leakage_table,
        leakage_model_rows(leakage),
    )

    write_csv(
        inflation_table,
        leakage_inflation_rows(leakage),
    )

    reconciliation_raw = release["metric_effect_reconciliation"]

    assert isinstance(
        reconciliation_raw,
        list,
    )

    reconciliation_rows: list[dict[str, object]] = []

    for row in reconciliation_raw:
        if not isinstance(
            row,
            dict,
        ):
            raise RuntimeError("Invalid reconciliation row.")

        reconciliation_rows.append({str(key): value for key, value in row.items()})

    write_csv(
        reconciliation_table,
        reconciliation_rows,
    )

    source_paths = (
        assets_root / "baseline_results.json",
        assets_root / "leakage_case_results.json",
        assets_root / "audit_findings.json",
        assets_root / "audit_manifest.json",
    )

    release_paths = (
        release_path,
        claims_path,
        baseline_table,
        leakage_table,
        inflation_table,
        reconciliation_table,
    )

    manifest: dict[str, Any] = {
        "scope": "PROJECT7_STEP5_RUN_MANIFEST",
        "source_files": {
            path.name: {
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in source_paths
        },
        "release_files": {
            path.name: {
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in release_paths
        },
        "step5_fingerprint_sha256": release["step5_fingerprint_sha256"],
        "claim_register_fingerprint_sha256": claims["claim_register_fingerprint_sha256"],
        "public_artifacts_generated": False,
        "step6_started": False,
    }

    manifest["run_manifest_fingerprint_sha256"] = canonical_sha256(manifest)

    manifest_path = assets_root / "run_manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return {
        "release_data": release,
        "claim_register": claims,
        "run_manifest": manifest,
    }


def independently_validate_frozen_release(
    assets_root: Path,
) -> dict[str, Any]:
    """Reload and independently validate every frozen Step 5 artifact."""

    baseline = load_json(assets_root / "baseline_results.json")

    leakage = load_json(assets_root / "leakage_case_results.json")

    audit = load_json(assets_root / "audit_findings.json")

    release = load_json(assets_root / "release_data.json")

    claims = load_json(assets_root / "claim_register.json")

    manifest = load_json(assets_root / "run_manifest.json")

    validation, reconciliation = independently_validate(
        baseline,
        leakage,
        audit,
    )

    if validation.status != "PASS":
        raise RuntimeError("Independent validation status is not PASS.")

    frozen_validation = release.get("independent_validation")

    if (
        not isinstance(
            frozen_validation,
            dict,
        )
        or frozen_validation != validation.to_dict()
    ):
        raise RuntimeError("Frozen validation does not reconcile.")

    frozen_reconciliation = release.get("metric_effect_reconciliation")

    expected_reconciliation = [row.to_dict() for row in reconciliation]

    if frozen_reconciliation != expected_reconciliation:
        raise RuntimeError("Frozen metric reconciliation does not match recomputation.")

    if release.get("step5_fingerprint_sha256") != manifest.get("step5_fingerprint_sha256"):
        raise RuntimeError("Step 5 fingerprint/manifest mismatch.")

    if claims.get("claim_register_fingerprint_sha256") != manifest.get(
        "claim_register_fingerprint_sha256"
    ):
        raise RuntimeError("Claim-register fingerprint/manifest mismatch.")

    if release.get("public_artifacts_generated") is not False:
        raise RuntimeError("Public artifacts generated before Step 5 gate.")

    if release.get("step6_started") is not False:
        raise RuntimeError("Step 6 started before Step 5 gate.")

    if claims.get("preview_claims_approved") is not False:
        raise RuntimeError("Preview claim approved.")

    if claims.get("unsupported_claims_approved") is not False:
        raise RuntimeError("Unsupported claim approved.")

    assert_no_preview_contamination(release)

    return {
        "status": "PASS",
        "scenario_count": validation.scenario_count,
        "model_result_count": validation.model_result_count,
        "metric_effect_mismatch_count": (validation.metric_effect_mismatch_count),
        "safe_release_status": (validation.safe_release_status),
        "duplicate_train_test_overlap": (validation.duplicate_train_test_overlap),
        "step5_fingerprint_sha256": release["step5_fingerprint_sha256"],
        "claim_register_fingerprint_sha256": claims["claim_register_fingerprint_sha256"],
        "run_manifest_fingerprint_sha256": manifest["run_manifest_fingerprint_sha256"],
    }
