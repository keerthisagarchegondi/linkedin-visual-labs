"""Canonical JSON serialization for generated Zombie Escape cities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
    HiddenRiskHotspot,
    ZombieZone,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridCell,
    GridPosition,
)
from linkedin_visual_labs.projects.p04_zombie_escape.pipeline import (
    ZombiePipelineContext,
)


def generated_cities_payload(
    cities: tuple[GeneratedCity, ...],
) -> dict[str, Any]:
    """Return the canonical JSON-compatible city payload."""
    return {
        "schema_version": 1,
        "city_count": len(cities),
        "cities": [_city_payload(city) for city in cities],
    }


def serialize_generated_cities(
    cities: tuple[GeneratedCity, ...],
) -> str:
    """Serialize generated cities deterministically."""
    return (
        json.dumps(
            generated_cities_payload(cities),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def write_generated_cities(
    context: ZombiePipelineContext,
    cities: tuple[GeneratedCity, ...],
) -> Path:
    """Write canonical cities.json inside the configured output root."""
    output_path = context.resolve_output_path(context.outputs.data.cities)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        serialize_generated_cities(cities),
        encoding="utf-8",
    )

    return output_path


def _city_payload(
    city: GeneratedCity,
) -> dict[str, Any]:
    return {
        "city_id": city.city_id.value,
        "display_name": city.definition.display_name,
        "inspiration_only": city.definition.inspiration_only,
        "seed": city.definition.seed,
        "grid": {
            "rows": city.grid.rows,
            "columns": city.grid.columns,
            "movement": city.grid.movement.value,
            "allow_diagonal": city.grid.allow_diagonal,
            "step_distance": city.grid.step_distance,
        },
        "start": _position_payload(city.definition.start),
        "destination": _position_payload(city.definition.destination),
        "profile": {
            "block_density": (city.definition.profile.block_density),
            "intersection_density": (city.definition.profile.intersection_density),
            "arterial_width": (city.definition.profile.arterial_width),
            "choke_point_density": (city.definition.profile.choke_point_density),
            "hidden_risk_structure": (city.definition.profile.hidden_risk_structure),
            "synthetic_barrier": (city.definition.profile.synthetic_barrier),
        },
        "visible_zombie_zones": [_visible_zone_payload(zone) for zone in city.visible_zombie_zones],
        "hidden_risk_hotspots": [
            _hidden_hotspot_payload(hotspot) for hotspot in city.hidden_risk_hotspots
        ],
        "synthetic_barrier_cells": [
            _position_payload(position) for position in city.synthetic_barrier_cells
        ],
        "cells": [_cell_payload(cell) for cell in city.cells],
    }


def _position_payload(
    position: GridPosition,
) -> dict[str, int]:
    return {
        "row": position.row,
        "column": position.column,
    }


def _visible_zone_payload(
    zone: ZombieZone,
) -> dict[str, Any]:
    return {
        "center": _position_payload(zone.center),
        "radius": zone.radius,
        "intensity": zone.intensity,
    }


def _hidden_hotspot_payload(
    hotspot: HiddenRiskHotspot,
) -> dict[str, Any]:
    return {
        "center": _position_payload(hotspot.center),
        "radius": hotspot.radius,
        "intensity": hotspot.intensity,
    }


def _cell_payload(
    cell: GridCell,
) -> dict[str, Any]:
    return {
        "row": cell.position.row,
        "column": cell.position.column,
        "terrain": cell.terrain.value,
        "observed_risk": cell.observed_risk,
        "true_risk": cell.true_risk,
    }
