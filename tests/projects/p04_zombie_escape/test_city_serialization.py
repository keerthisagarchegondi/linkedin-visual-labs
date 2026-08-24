"""City serialization tests for Project 2."""

from __future__ import annotations

import json
from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape import (
    build_pipeline_context,
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    generate_all_cities,
)
from linkedin_visual_labs.projects.p04_zombie_escape.serialization import (
    generated_cities_payload,
    serialize_generated_cities,
    write_generated_cities,
)


def test_serialized_city_payload_has_expected_shape() -> None:
    cities = generate_all_cities(load_zombie_config())

    payload = generated_cities_payload(cities)

    assert payload["schema_version"] == 1

    assert payload["city_count"] == 3

    city_payloads = payload["cities"]

    assert isinstance(
        city_payloads,
        list,
    )

    assert [city["city_id"] for city in city_payloads] == [
        "phoenix",
        "new_york",
        "chicago",
    ]

    for city in city_payloads:
        assert len(city["cells"]) == 1_296


def test_city_json_is_byte_deterministic() -> None:
    config = load_zombie_config()

    first = serialize_generated_cities(generate_all_cities(config))

    second = serialize_generated_cities(generate_all_cities(config))

    assert first == second


def test_city_json_rejects_nan_by_construction() -> None:
    config = load_zombie_config()

    text = serialize_generated_cities(generate_all_cities(config))

    assert "NaN" not in text
    assert "Infinity" not in text


def test_city_json_round_trips_through_standard_json() -> None:
    config = load_zombie_config()

    text = serialize_generated_cities(generate_all_cities(config))

    payload = json.loads(text)

    assert payload["city_count"] == 3


def test_write_generated_cities_uses_canonical_output_path(
    tmp_path: Path,
) -> None:
    context = build_pipeline_context(
        repository_root=tmp_path,
        config_path=(Path.cwd() / "configs/p04_zombie_escape.yaml"),
    )

    cities = generate_all_cities(context.configuration)

    output = write_generated_cities(
        context,
        cities,
    )

    assert output == (tmp_path / ("outputs/p04_zombie_escape/data/cities.json"))

    assert output.is_file()

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["city_count"] == 3
