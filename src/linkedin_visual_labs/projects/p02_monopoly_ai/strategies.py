"""Configuration-driven autonomous strategy policies.

Policies receive read-only decision context and return immutable
decisions. They never receive or mutate GameState directly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
    StrategyPolicyConfig,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    PropertyGroupId,
    SpaceType,
    StrategyAction,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.engine import (
    DecisionContext,
    DecisionProvider,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
    BoardSpace,
    BuildDecision,
    PropertyDefinition,
    PurchaseDecision,
)


class StrategyPolicy(Protocol):
    """Complete strategy-policy interface."""

    @property
    def strategy_id(self) -> StrategyId:
        """Canonical strategy ID."""

    @property
    def desired_cash_reserve(self) -> int:
        """Preferred post-purchase cash reserve."""

    @property
    def development_cash_reserve(self) -> int:
        """Preferred post-build cash reserve."""

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        """Return BUY or PASS."""

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        """Return BUILD or HOLD_CASH decisions."""


def _require_mapping(
    value: object,
    *,
    name: str,
) -> Mapping[object, object]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(f"{name} must be a mapping")

    return value


def _require_text(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise ValueError(f"{name} must be a string")

    return value


def _require_text_list(
    value: object,
    *,
    name: str,
) -> tuple[str, ...]:
    if not isinstance(
        value,
        list,
    ):
        raise ValueError(f"{name} must be a list")

    result: list[str] = []

    for index, item in enumerate(value):
        result.append(
            _require_text(
                item,
                name=f"{name}[{index}]",
            )
        )

    return tuple(result)


@dataclass(frozen=True, slots=True)
class PolicySettings:
    """Typed strategy settings derived from the frozen YAML."""

    strategy_id: StrategyId
    label: str
    desired_cash_reserve: int
    development_cash_reserve: int
    maximum_builds_per_turn: int


class BaseStrategyPolicy:
    """Shared deterministic strategy behavior."""

    def __init__(
        self,
        *,
        settings: PolicySettings,
        board: BoardDefinition,
    ) -> None:
        self._settings = settings
        self._board = board

        self._asset_definitions = {
            space.asset.asset_id: space.asset for space in board.spaces if space.asset is not None
        }

        groups: dict[
            PropertyGroupId,
            list[str],
        ] = {}

        for asset in self._asset_definitions.values():
            if asset.group_id is None:
                continue

            groups.setdefault(
                asset.group_id,
                [],
            ).append(asset.asset_id)

        self._group_assets = {
            group_id: tuple(
                sorted(
                    asset_ids,
                    key=self._asset_board_index,
                )
            )
            for group_id, asset_ids in groups.items()
        }

    @property
    def strategy_id(self) -> StrategyId:
        return self._settings.strategy_id

    @property
    def desired_cash_reserve(self) -> int:
        return self._settings.desired_cash_reserve

    @property
    def development_cash_reserve(self) -> int:
        return self._settings.development_cash_reserve

    @property
    def maximum_builds_per_turn(self) -> int:
        return self._settings.maximum_builds_per_turn

    def reserve_after_purchase(
        self,
        *,
        context: DecisionContext,
        asset: PropertyDefinition,
    ) -> int:
        """Cash remaining after purchasing the landed asset."""

        return context.player.cash - asset.purchase_price

    def reserve_after_build(
        self,
        *,
        available_cash: int,
        asset: PropertyDefinition,
    ) -> int:
        """Cash remaining after one house build."""

        if asset.house_cost is None:
            raise ValueError("buildable property requires house_cost")

        return available_cash - asset.house_cost

    def _asset_board_index(
        self,
        asset_id: str,
    ) -> int:
        return self._asset_definitions[asset_id].board_index

    def _owns_complete_group(
        self,
        *,
        context: DecisionContext,
        player_id: str,
        group_id: PropertyGroupId,
    ) -> bool:
        return all(
            context.properties[asset_id].owner_id == player_id
            for asset_id in self._group_assets[group_id]
        )

    def _purchase_completes_group(
        self,
        *,
        context: DecisionContext,
        asset: PropertyDefinition,
    ) -> bool:
        if asset.group_id is None:
            return False

        player_id = context.player.player_id

        group_assets = self._group_assets[asset.group_id]

        return all(
            (candidate_id == asset.asset_id)
            or (context.properties[candidate_id].owner_id == player_id)
            for candidate_id in group_assets
        )

    def _plan_builds(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
        group_priority: tuple[
            PropertyGroupId,
            ...,
        ]
        | None = None,
        reserve: int | None = None,
        maximum_builds: int | None = None,
    ) -> tuple[BuildDecision, ...]:
        """Plan legal even-development builds deterministically."""

        del board

        player_id = context.player.player_id

        desired_reserve = self.development_cash_reserve if reserve is None else reserve

        build_limit = self.maximum_builds_per_turn if maximum_builds is None else maximum_builds

        available_cash = context.player.cash

        temporary_houses = {
            asset_id: view.house_count for asset_id, view in context.properties.items()
        }

        complete_groups = [
            group_id
            for group_id in self._group_assets
            if self._owns_complete_group(
                context=context,
                player_id=player_id,
                group_id=group_id,
            )
        ]

        if group_priority is None:
            ordered_groups = sorted(
                complete_groups,
                key=str,
            )
        else:
            preferred = [group_id for group_id in group_priority if group_id in complete_groups]

            remaining = sorted(
                (group_id for group_id in complete_groups if group_id not in preferred),
                key=str,
            )

            ordered_groups = preferred + remaining

        decisions: list[BuildDecision] = []

        while len(decisions) < build_limit:
            chosen_asset_id: str | None = None

            for group_id in ordered_groups:
                group_assets = self._group_assets[group_id]

                minimum_houses = min(temporary_houses[asset_id] for asset_id in group_assets)

                candidates = [
                    asset_id
                    for asset_id in group_assets
                    if (
                        temporary_houses[asset_id] == minimum_houses
                        and temporary_houses[asset_id] < 4
                    )
                ]

                if not candidates:
                    continue

                candidate_id = min(
                    candidates,
                    key=self._asset_board_index,
                )

                asset = self._asset_definitions[candidate_id]

                if asset.house_cost is None:
                    continue

                if available_cash - asset.house_cost < desired_reserve:
                    continue

                chosen_asset_id = candidate_id
                break

            if chosen_asset_id is None:
                break

            asset = self._asset_definitions[chosen_asset_id]

            assert asset.house_cost is not None

            decisions.append(
                BuildDecision(
                    action=StrategyAction.BUILD,
                    reason_code=(f"{self.strategy_id.value}_development"),
                    property_id=chosen_asset_id,
                )
            )

            temporary_houses[chosen_asset_id] += 1

            available_cash -= asset.house_cost

        if decisions:
            return tuple(decisions)

        return (
            BuildDecision(
                action=StrategyAction.HOLD_CASH,
                reason_code=(f"{self.strategy_id.value}_reserve_hold"),
            ),
        )


class CollectorPolicy(BaseStrategyPolicy):
    """Broad-acquisition strategy."""

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        del space

        remaining = self.reserve_after_purchase(
            context=context,
            asset=asset,
        )

        if context.player.cash >= asset.purchase_price and remaining >= self.desired_cash_reserve:
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="collector_buy_broadly",
                asset_id=asset.asset_id,
            )

        return PurchaseDecision(
            action=StrategyAction.PASS,
            reason_code="collector_reserve",
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        return self._plan_builds(
            context=context,
            board=board,
            maximum_builds=1,
        )


class SpecialistPolicy(BaseStrategyPolicy):
    """Preferred-group concentration strategy."""

    def __init__(
        self,
        *,
        settings: PolicySettings,
        board: BoardDefinition,
        primary_groups: tuple[
            PropertyGroupId,
            ...,
        ],
        secondary_groups: tuple[
            PropertyGroupId,
            ...,
        ],
        low_priority_groups: tuple[
            PropertyGroupId,
            ...,
        ],
    ) -> None:
        super().__init__(
            settings=settings,
            board=board,
        )

        self._primary_groups = primary_groups

        self._secondary_groups = secondary_groups

        self._low_priority_groups = low_priority_groups

    @property
    def primary_groups(
        self,
    ) -> tuple[
        PropertyGroupId,
        ...,
    ]:
        return self._primary_groups

    @property
    def secondary_groups(
        self,
    ) -> tuple[
        PropertyGroupId,
        ...,
    ]:
        return self._secondary_groups

    def purchase_priority_score(
        self,
        *,
        context: DecisionContext,
        asset: PropertyDefinition,
    ) -> int:
        """Return deterministic Specialist acquisition priority."""

        completes = self._purchase_completes_group(
            context=context,
            asset=asset,
        )

        group_id = asset.group_id

        if group_id in self._primary_groups:
            return 100 if completes else 80

        if group_id in self._secondary_groups:
            return 75 if completes else 55

        if group_id in self._low_priority_groups:
            return 45 if completes else 15

        if asset.space_type in {
            SpaceType.TRANSIT,
            SpaceType.UTILITY,
        }:
            return 30

        return 0

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        del space

        if context.player.cash < asset.purchase_price:
            return PurchaseDecision(
                action=StrategyAction.PASS,
                reason_code="specialist_unaffordable",
            )

        remaining = self.reserve_after_purchase(
            context=context,
            asset=asset,
        )

        score = self.purchase_priority_score(
            context=context,
            asset=asset,
        )

        if remaining < self.desired_cash_reserve:
            return PurchaseDecision(
                action=StrategyAction.PASS,
                reason_code="specialist_reserve",
            )

        if score >= 50:
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="specialist_priority",
                asset_id=asset.asset_id,
            )

        # Low-priority assets require a wider liquidity cushion.
        if score >= 30 and remaining >= (self.desired_cash_reserve + 300):
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="specialist_surplus_cash",
                asset_id=asset.asset_id,
            )

        return PurchaseDecision(
            action=StrategyAction.PASS,
            reason_code="specialist_low_priority",
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        priority = self._primary_groups + self._secondary_groups + self._low_priority_groups

        return self._plan_builds(
            context=context,
            board=board,
            group_priority=priority,
            maximum_builds=self.maximum_builds_per_turn,
        )


class CashProtectorPolicy(BaseStrategyPolicy):
    """Liquidity-preservation strategy."""

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        del space

        if context.player.cash < asset.purchase_price:
            return PurchaseDecision(
                action=StrategyAction.PASS,
                reason_code="cash_protector_unaffordable",
            )

        remaining = self.reserve_after_purchase(
            context=context,
            asset=asset,
        )

        if remaining < self.desired_cash_reserve:
            return PurchaseDecision(
                action=StrategyAction.PASS,
                reason_code="cash_protector_reserve",
            )

        completes_group = self._purchase_completes_group(
            context=context,
            asset=asset,
        )

        # High selectivity: outside a group completion, an asset may
        # consume no more than 20% of current liquidity.
        affordable_fraction = asset.purchase_price <= (context.player.cash // 5)

        if completes_group or affordable_fraction:
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code=("cash_protector_selective_buy"),
                asset_id=asset.asset_id,
            )

        return PurchaseDecision(
            action=StrategyAction.PASS,
            reason_code="cash_protector_selective_pass",
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        return self._plan_builds(
            context=context,
            board=board,
            reserve=self.development_cash_reserve,
            maximum_builds=1,
        )


class AggressiveBuilderPolicy(BaseStrategyPolicy):
    """Low-reserve, rapid-development strategy."""

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        del space

        if context.player.cash < asset.purchase_price:
            return PurchaseDecision(
                action=StrategyAction.PASS,
                reason_code="aggressive_unaffordable",
            )

        remaining = self.reserve_after_purchase(
            context=context,
            asset=asset,
        )

        completes_group = self._purchase_completes_group(
            context=context,
            asset=asset,
        )

        if remaining >= self.desired_cash_reserve or completes_group:
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code=("aggressive_capital_deployment"),
                asset_id=asset.asset_id,
            )

        return PurchaseDecision(
            action=StrategyAction.PASS,
            reason_code="aggressive_minimum_liquidity",
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        return self._plan_builds(
            context=context,
            board=board,
            reserve=self.development_cash_reserve,
            maximum_builds=self.maximum_builds_per_turn,
        )


class StrategyRegistryProvider(DecisionProvider):
    """Delegate engine decisions to the appropriate strategy policy."""

    def __init__(
        self,
        policies: Mapping[
            StrategyId,
            StrategyPolicy,
        ],
    ) -> None:
        self._policies = dict(policies)

        required = set(StrategyId)

        missing = required - set(self._policies)

        if missing:
            raise ValueError(
                "strategy registry missing: "
                + ", ".join(sorted(strategy.value for strategy in missing))
            )

    def policy_for(
        self,
        strategy_id: StrategyId,
    ) -> StrategyPolicy:
        try:
            return self._policies[strategy_id]
        except KeyError as exc:
            raise ValueError(f"unknown strategy: {strategy_id}") from exc

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        policy = self.policy_for(context.player.strategy_id)

        return policy.purchase_decision(
            context=context,
            space=space,
            asset=asset,
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        policy = self.policy_for(context.player.strategy_id)

        return policy.build_decisions(
            context=context,
            board=board,
        )


def _settings_for(
    config: MonopolyConfig,
    strategy_id: StrategyId,
) -> PolicySettings:
    matching = [strategy for strategy in config.strategies if strategy.strategy_id is strategy_id]

    if len(matching) != 1:
        raise ValueError(f"expected one config for {strategy_id.value}")

    strategy: StrategyPolicyConfig = matching[0]

    return PolicySettings(
        strategy_id=strategy.strategy_id,
        label=strategy.label,
        desired_cash_reserve=(strategy.desired_cash_reserve),
        development_cash_reserve=(strategy.development_cash_reserve),
        maximum_builds_per_turn=(strategy.maximum_builds_per_turn),
    )


def _raw_policy(
    config: MonopolyConfig,
    strategy_id: StrategyId,
) -> Mapping[object, object]:
    strategies = _require_mapping(
        config.raw.get("strategies"),
        name="strategies",
    )

    policies = _require_mapping(
        strategies.get("policies"),
        name="strategies.policies",
    )

    return _require_mapping(
        policies.get(strategy_id.value),
        name=(f"strategies.policies.{strategy_id.value}"),
    )


def build_strategy_registry(
    config: MonopolyConfig,
) -> StrategyRegistryProvider:
    """Load all four canonical policies from frozen configuration."""

    board = build_board(config)

    collector = CollectorPolicy(
        settings=_settings_for(
            config,
            StrategyId.COLLECTOR,
        ),
        board=board,
    )

    specialist_raw = _raw_policy(
        config,
        StrategyId.SPECIALIST,
    )

    specialist_purchase = _require_mapping(
        specialist_raw.get("purchase"),
        name="specialist.purchase",
    )

    specialist = SpecialistPolicy(
        settings=_settings_for(
            config,
            StrategyId.SPECIALIST,
        ),
        board=board,
        primary_groups=tuple(
            PropertyGroupId(value)
            for value in _require_text_list(
                specialist_purchase.get("primary_property_groups"),
                name=("specialist.primary_property_groups"),
            )
        ),
        secondary_groups=tuple(
            PropertyGroupId(value)
            for value in _require_text_list(
                specialist_purchase.get("secondary_property_groups"),
                name=("specialist.secondary_property_groups"),
            )
        ),
        low_priority_groups=tuple(
            PropertyGroupId(value)
            for value in _require_text_list(
                specialist_purchase.get("low_priority_property_groups"),
                name=("specialist.low_priority_property_groups"),
            )
        ),
    )

    cash_protector = CashProtectorPolicy(
        settings=_settings_for(
            config,
            StrategyId.CASH_PROTECTOR,
        ),
        board=board,
    )

    aggressive_builder = AggressiveBuilderPolicy(
        settings=_settings_for(
            config,
            StrategyId.AGGRESSIVE_BUILDER,
        ),
        board=board,
    )

    return StrategyRegistryProvider(
        {
            StrategyId.COLLECTOR: collector,
            StrategyId.SPECIALIST: specialist,
            StrategyId.CASH_PROTECTOR: cash_protector,
            StrategyId.AGGRESSIVE_BUILDER: aggressive_builder,
        }
    )
