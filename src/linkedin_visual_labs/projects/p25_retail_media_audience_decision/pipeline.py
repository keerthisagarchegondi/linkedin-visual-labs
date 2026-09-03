"""Project 4 Step 2 data-ingestion orchestration."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    SourceId,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters import (
    criteo,
    dunnhumby,
    hillstrom,
    retailrocket,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    CachePolicy,
    SourceResult,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.validation import (
    validate_all,
)

SOURCE_NAMES = (
    "hillstrom",
    "dunnhumby",
    "criteo",
    "retailrocket",
)


def cache_root(
    repository_root: Path,
) -> Path:
    """Return the ignored Project 4 cache root."""

    return repository_root / ".cache" / "p25_retail_media_audience_decision"


def cache_policy(
    repository_root: Path,
    *,
    name: str,
    source_id: SourceId,
) -> CachePolicy:
    """Build one deterministic cache policy."""

    root = cache_root(repository_root)

    return CachePolicy(
        source_id=source_id,
        raw_dir=(root / "raw" / name),
        normalized_dir=(root / "normalized" / name),
        provenance_dir=(root / "provenance"),
    )


def fetch_sources(
    *,
    repository_root: Path,
    source: str,
    offline: bool,
    criteo_max_rows: int,
) -> list[SourceResult]:
    """Fetch one or all Project 4 evidence sources."""

    if source != "all" and source not in SOURCE_NAMES:
        raise ValueError(f"Unknown source {source!r}; expected all or {SOURCE_NAMES}")

    selected = SOURCE_NAMES if source == "all" else (source,)

    results: list[SourceResult] = []

    for name in selected:
        if name == "hillstrom":
            result = hillstrom.fetch_and_normalize(
                cache_policy(
                    repository_root,
                    name="hillstrom",
                    source_id=SourceId.HILLSTROM,
                ),
                offline=offline,
            )

        elif name == "dunnhumby":
            result = dunnhumby.fetch_and_normalize(
                cache_policy(
                    repository_root,
                    name="dunnhumby",
                    source_id=SourceId.DUNNHUMBY,
                ),
                offline=offline,
            )

        elif name == "criteo":
            result = criteo.fetch_and_normalize(
                cache_policy(
                    repository_root,
                    name="criteo",
                    source_id=SourceId.CRITEO,
                ),
                offline=offline,
                max_rows=criteo_max_rows,
            )

        elif name == "retailrocket":
            result = retailrocket.fetch_and_normalize(
                cache_policy(
                    repository_root,
                    name="retailrocket",
                    source_id=SourceId.RETAILROCKET,
                ),
                offline=offline,
            )

        else:
            raise AssertionError(f"Unhandled source: {name}")

        results.append(result)

    return results


def validate_cached_sources(
    *,
    repository_root: Path,
) -> dict[str, int]:
    """Run independent Step 2 source validation."""

    return validate_all(cache_root=cache_root(repository_root))
