"""Typed Step 1 configuration contracts; no forecasting or allocation logic."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from linkedin_visual_labs.common.random_state import normalize_seed

PROJECT_ID = "p25_quick_commerce_control_tower"
Category = Literal["FOODS", "HOUSEHOLD"]
Store = Literal["CA_1", "CA_2", "CA_3", "CA_4", "TX_1", "TX_2", "TX_3", "WI_1", "WI_2", "WI_3"]
PositiveInteger = Annotated[int, Field(strict=True, gt=0)]
PositiveNumber = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
NonnegativeNumber = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]


class Contract(BaseModel):
    """Reject unknown configuration fields and direct attribute reassignment."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectPathConfig(Contract):
    """Repository-relative locations fixed by the approved project architecture."""

    raw_data: Literal["data/raw/p25_quick_commerce_control_tower"]
    cache: Literal[".cache/p25_quick_commerce_control_tower"]
    sql: Literal["sql/p25_quick_commerce_control_tower"]
    output: Literal["outputs/p25_quick_commerce_control_tower"]


class DataConfig(Contract):
    """Exact real-data scope; fixtures must not silently replace this contract."""

    holdout_days: PositiveInteger
    categories: tuple[Category, Category]
    expected_store_count: PositiveInteger
    expected_series_count: PositiveInteger

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.holdout_days != 28:
            raise ValueError("holdout_days must be 28")
        if self.categories != ("FOODS", "HOUSEHOLD"):
            raise ValueError("categories must be exactly FOODS, HOUSEHOLD in that order")
        if self.expected_store_count != 10 or self.expected_series_count != 20:
            raise ValueError("scope must contain 10 stores and 20 series")
        return self


class ExceptionWeights(Contract):
    """Fixed ex ante priority weights on dimensionless materiality components."""

    volume: NonnegativeNumber
    shortfall: NonnegativeNumber
    absolute_error: NonnegativeNumber
    bias_exposure: NonnegativeNumber
    disagreement_exposure: NonnegativeNumber
    repeated_miss_exposure: NonnegativeNumber

    @model_validator(mode="after")
    def positive_total(self) -> Self:
        if sum(self.model_dump().values()) <= 0:
            raise ValueError("exception weights must have a positive total")
        return self


class DiagnosticsConfig(Contract):
    disagreement_review_threshold: PositiveNumber
    minimum_subgroup_observations: PositiveInteger
    top_exceptions: PositiveInteger
    weights: ExceptionWeights


class GovernanceConfig(Contract):
    """Bias is a fraction of actual demand, not a percentage-point value."""

    absolute_bias_guardrail: Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]


class SeasonalNaiveConfig(Contract):
    """Parameters reserved for the lag-28 baseline."""

    lag: Literal[28]


class HoltWintersConfig(Contract):
    """Parameters reserved for weekly additive exponential smoothing."""

    seasonal_periods: Literal[7]
    seasonal: Literal["add"]
    trend: Literal["add"]
    damped_trend: bool


class HistGradientBoostingConfig(Contract):
    """Bounded estimator settings without automatic random validation."""

    max_iter: PositiveInteger
    learning_rate: PositiveNumber
    max_leaf_nodes: Annotated[int, Field(strict=True, ge=2)]
    l2_regularization: NonnegativeNumber
    early_stopping: Literal[False]


class MLPConfig(Contract):
    """The approved neural challenger architecture and optimizer settings."""

    hidden_layer_sizes: tuple[Literal[128], Literal[64], Literal[32]]
    activation: Literal["relu"]
    solver: Literal["adam"]
    max_iter: PositiveInteger
    alpha: NonnegativeNumber
    learning_rate_init: PositiveNumber
    early_stopping: Literal[False]


class ForecastingConfig(Contract):
    """Configuration only: these contracts do not instantiate estimators."""

    seasonal_naive: SeasonalNaiveConfig
    holt_winters: HoltWintersConfig
    hist_gradient_boosting: HistGradientBoostingConfig
    mlp: MLPConfig


class LaborConfig(Contract):
    """Illustrative units, staffing bounds, costs, and fixed daily capacity."""

    classification: Literal["illustrative"]
    productivity_units_per_hour: dict[Category, PositiveNumber]
    minimum_staffing: PositiveInteger
    maximum_staffing: PositiveInteger
    shift_hours: PositiveNumber
    daily_network_hours: PositiveNumber
    cost_per_hour: PositiveNumber
    uncovered_hour_penalty: PositiveNumber
    store_priority_weights: dict[Store, PositiveNumber]
    critical_uncovered_hours: PositiveNumber
    solver_tolerance: Annotated[float, Field(strict=True, ge=1e-10, le=1e-4)]

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.minimum_staffing > self.maximum_staffing:
            raise ValueError("minimum staffing must not exceed maximum staffing")
        if set(self.productivity_units_per_hour) != {"FOODS", "HOUSEHOLD"}:
            raise ValueError("productivity must cover both categories")
        if len(self.store_priority_weights) != 10:
            raise ValueError("priority weights must cover all 10 stores")
        return self


class InventoryConfig(Contract):
    """Bounded synthetic snapshot; no replenishment or lead-time model."""

    window_days: Annotated[int, Field(strict=True, ge=1, le=28)]
    on_hand_days_min: NonnegativeNumber
    on_hand_days_max: PositiveNumber
    expedite_below_days: PositiveNumber
    reorder_below_days: PositiveNumber
    monitor_below_days: PositiveNumber
    low_demand_units_per_day: PositiveNumber

    @model_validator(mode="after")
    def validate_inventory_bounds(self) -> Self:
        if self.on_hand_days_min > self.on_hand_days_max:
            raise ValueError("inventory generation bounds are reversed")
        if not self.expedite_below_days < self.reorder_below_days < self.monitor_below_days:
            raise ValueError("inventory risk thresholds must be strictly increasing")
        return self


class ScenarioConfig(Contract):
    """Exact approved stress scenarios; capacity remains fixed."""

    name: Literal["Base", "+15% demand", "-10% productivity"]
    demand_multiplier: PositiveNumber
    productivity_multiplier: PositiveNumber
    capacity_multiplier: PositiveNumber

    @model_validator(mode="after")
    def validate_multipliers(self) -> Self:
        expected = {
            "Base": (1.0, 1.0, 1.0),
            "+15% demand": (1.15, 1.0, 1.0),
            "-10% productivity": (1.0, 0.90, 1.0),
        }
        actual = (self.demand_multiplier, self.productivity_multiplier, self.capacity_multiplier)
        if actual != expected[self.name]:
            raise ValueError("scenario must match its approved shock with fixed capacity")
        return self


class OutputConfig(Contract):
    """Final media dimensions; no rendering occurs during Step 1."""

    width: PositiveInteger
    height: PositiveInteger
    fps: PositiveInteger

    @model_validator(mode="after")
    def validate_canvas(self) -> Self:
        if (self.width, self.height, self.fps) != (1080, 1350, 30):
            raise ValueError("output must be 1080 x 1350 at 30 fps")
        return self


class AcquisitionConfig(Contract):
    """Pinned source identity; no implicit mirrors or fixture fallback."""

    record_id: Literal["10203108"]
    sales_url: Literal[
        "https://zenodo.org/records/10203108/files/sales_train_evaluation.csv?download=1"
    ]
    calendar_url: Literal["https://zenodo.org/records/10203108/files/calendar.csv?download=1"]
    sales_md5: Literal["b806dfc9f30a745102b708c09951f6aa"]
    calendar_md5: Literal["3ffeab2991b0c8e861d008b39ea4c95c"]
    expected_observed_days: Literal[1941]
    timeout_seconds: PositiveNumber
    attempts: Annotated[int, Field(strict=True, ge=1, le=5)]


class ResourceConfig(Contract):
    """DuckDB resource bounds; spill remains repository-local."""

    threads: Annotated[int, Field(strict=True, ge=1, le=16)]
    memory_limit: Annotated[str, Field(pattern=r"^[1-9][0-9]*(MB|GB)$")]


class FeatureConfig(Contract):
    """Auditable direct-horizon historical windows, never near-target actuals."""

    lags: tuple[int, ...]
    rolling_windows: tuple[int, ...]
    rolling_end_lag: Literal[28]

    @model_validator(mode="after")
    def validate_windows(self) -> Self:
        if not self.lags or tuple(sorted(set(self.lags))) != self.lags:
            raise ValueError("lags must be nonempty, unique, and ordered")
        if any(lag not in (28, 35, 42, 49, 56) for lag in self.lags):
            raise ValueError("only approved lag 28 and longer features are permitted")
        if (
            not self.rolling_windows
            or tuple(sorted(set(self.rolling_windows))) != self.rolling_windows
        ):
            raise ValueError("rolling windows must be nonempty, unique, and ordered")
        if any(window not in (7, 14) for window in self.rolling_windows):
            raise ValueError("only seven- and fourteen-day shifted summaries are supported")
        return self


class CommerceConfig(Contract):
    """Complete Step 1 settings, with business assumptions loaded from YAML."""

    project_id: Literal["p25_quick_commerce_control_tower"]
    seed: Annotated[int, Field(strict=True)]
    paths: ProjectPathConfig
    data: DataConfig
    governance: GovernanceConfig
    forecasting: ForecastingConfig
    labor: LaborConfig
    scenarios: tuple[ScenarioConfig, ScenarioConfig, ScenarioConfig]
    output: OutputConfig
    acquisition: AcquisitionConfig
    resources: ResourceConfig
    features: FeatureConfig
    diagnostics: DiagnosticsConfig
    inventory: InventoryConfig

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        return normalize_seed(value)

    @model_validator(mode="after")
    def validate_cross_fields(self) -> Self:
        if tuple(scenario.name for scenario in self.scenarios) != (
            "Base",
            "+15% demand",
            "-10% productivity",
        ):
            raise ValueError("all three scenarios must occur exactly once in approved order")
        minimum_hours = (
            self.labor.minimum_staffing * self.labor.shift_hours * self.data.expected_store_count
        )
        if minimum_hours > self.labor.daily_network_hours:
            raise ValueError("network capacity cannot cover minimum staffing")
        return self
