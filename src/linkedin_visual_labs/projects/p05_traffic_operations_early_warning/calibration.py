"""Normalized single-approach geometry, with no inferred physical calibration."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .models import Contract, Sha256, Text

Coordinate = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Component = Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]


class Point(Contract):
    x: Coordinate
    y: Coordinate


def cross(a: Point, b: Point, c: Point) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


class Polygon(Contract):
    """Strictly convex polygons only; reject rather than repair malformed geometry."""

    points: tuple[Point, ...] = Field(min_length=3)

    @model_validator(mode="after")
    def convex(self) -> Self:
        if len(set((p.x, p.y) for p in self.points)) != len(self.points):
            raise ValueError("duplicate polygon vertices")
        signs = []
        for i, a in enumerate(self.points):
            b = self.points[(i + 1) % len(self.points)]
            values = [
                cross(a, b, c)
                for j, c in enumerate(self.points)
                if j not in (i, (i + 1) % len(self.points))
            ]
            if not (all(v > 1e-10 for v in values) or all(v < -1e-10 for v in values)):
                raise ValueError("polygon must be nondegenerate and strictly convex")
            signs.append(values[0] > 0)
        if len(set(signs)) != 1:
            raise ValueError("inconsistent polygon orientation")
        return self

    def contains(self, point: Point) -> bool:
        values = [
            cross(a, self.points[(i + 1) % len(self.points)], point)
            for i, a in enumerate(self.points)
        ]
        return all(v >= -1e-10 for v in values) or all(v <= 1e-10 for v in values)

    def area(self) -> float:
        return (
            abs(
                sum(
                    a.x * self.points[(i + 1) % len(self.points)].y
                    - a.y * self.points[(i + 1) % len(self.points)].x
                    for i, a in enumerate(self.points)
                )
            )
            / 2
        )


class Line(Contract):
    start: Point
    end: Point

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if self.start == self.end:
            raise ValueError("zero-length boundary")
        if any(not 0.01 < v < 0.99 for p in (self.start, self.end) for v in (p.x, p.y)):
            raise ValueError("boundary too close to image border")
        return self


def intersects(first: Line, second: Line) -> bool:
    """Closed segments, including touching and collinear overlap."""
    a, b, c, d = first.start, first.end, second.start, second.end
    return segments_intersect(a, b, c, d)


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Intersection without boundary-placement assumptions for polygon edges."""
    if (
        max(a.x, b.x) < min(c.x, d.x)
        or max(c.x, d.x) < min(a.x, b.x)
        or max(a.y, b.y) < min(c.y, d.y)
        or max(c.y, d.y) < min(a.y, b.y)
    ):
        return False
    return cross(a, b, c) * cross(a, b, d) <= 0 and cross(c, d, a) * cross(c, d, b) <= 0


class Geometry(Contract):
    source_sha256: Sha256
    camera_id: Text
    calibration: Literal["RELATIVE_ONLY"] = "RELATIVE_ONLY"
    reference_point: Literal["BOTTOM_CENTER"] = "BOTTOM_CENTER"
    roi: Polygon
    queue_zone: Polygon
    entry: Line
    exit: Line
    direction: tuple[Component, Component]
    entry_direction: tuple[Component, Component]
    exit_direction: tuple[Component, Component]
    exclusions: tuple[Polygon, ...] = ()
    rationale: Text

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if not all(self.roi.contains(p) for p in self.queue_zone.points):
            raise ValueError("queue zone outside ROI")
        if self.queue_zone.area() >= self.roi.area() - 1e-10:
            raise ValueError("queue zone must be smaller than ROI")
        endpoints = (self.entry.start, self.entry.end, self.exit.start, self.exit.end)
        if not all(self.roi.contains(p) for p in endpoints):
            raise ValueError("boundary outside ROI")
        if intersects(self.entry, self.exit):
            raise ValueError("entry and exit intersect")
        dx, dy = self.direction
        displacement_x = self.exit.start.x + self.exit.end.x - self.entry.start.x - self.entry.end.x
        displacement_y = self.exit.start.y + self.exit.end.y - self.entry.start.y - self.entry.end.y
        if dx * displacement_x + dy * displacement_y <= 0:
            raise ValueError("direction must point from entry toward exit")
        for line, (local_dx, local_dy) in (
            (self.entry, self.entry_direction),
            (self.exit, self.exit_direction),
        ):
            if (
                abs((line.end.x - line.start.x) * local_dy - (line.end.y - line.start.y) * local_dx)
                < 1e-8
            ):
                raise ValueError("direction parallel to crossing boundary")
            if local_dx * dx + local_dy * dy <= 0:
                raise ValueError("local crossing direction opposes the journey")
        # Version 1 exclusions are disjoint context masks. Interior holes need a
        # richer reviewed geometry contract, not a silent subtraction here.
        for excluded in self.exclusions:
            if any(self.roi.contains(p) for p in excluded.points) or any(
                excluded.contains(p) for p in self.roi.points
            ):
                raise ValueError("exclusions must be disjoint from analysis ROI")
            for i, a in enumerate(excluded.points):
                b = excluded.points[(i + 1) % len(excluded.points)]
                for j, c in enumerate(self.roi.points):
                    d = self.roi.points[(j + 1) % len(self.roi.points)]
                    if segments_intersect(a, b, c, d):
                        raise ValueError("exclusion crosses ROI")
        return self
