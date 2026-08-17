"""Launch-project CLI registrations."""

from linkedin_visual_labs.projects.p01_bayesian_dice.cli import (
    app as dice_app,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.cli import (
    app as monopoly_app,
)
from linkedin_visual_labs.projects.p04_zombie_escape.cli import (
    app as zombie_app,
)

__all__ = [
    "dice_app",
    "monopoly_app",
    "zombie_app",
]
