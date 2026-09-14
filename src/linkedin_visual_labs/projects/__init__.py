"""Launch-project CLI registrations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typer import Typer

from linkedin_visual_labs.projects.p01_bayesian_dice.cli import (
    app as dice_app,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.cli import (
    app as monopoly_app,
)
from linkedin_visual_labs.projects.p04_zombie_escape.cli import (
    app as zombie_app,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.cli import (
    app as commerce_app,
)

__all__ = [
    "commerce_app",
    "dice_app",
    "monopoly_app",
    "traffic_app",
    "zombie_app",
]


def __getattr__(name: str) -> "Typer":
    """Keep traffic contract-only imports independent of the runtime scaffold."""
    if name == "traffic_app":
        from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.cli import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
