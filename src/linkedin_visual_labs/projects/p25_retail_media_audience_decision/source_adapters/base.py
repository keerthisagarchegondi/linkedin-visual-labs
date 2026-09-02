"""Shared external-source adapter protocol."""

from __future__ import annotations

from typing import Protocol

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    SourceId,
    SourceMetadata,
)


class SourceAdapter(Protocol):
    """Narrow interface implemented by source adapters."""

    @property
    def source_id(self) -> SourceId:
        """Return the stable source identifier."""

        ...

    def metadata(self) -> SourceMetadata:
        """Return immutable source metadata."""

        ...
