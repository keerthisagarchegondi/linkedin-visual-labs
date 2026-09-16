"""Prediction-Time Integrity Auditor scaffold."""

from .config import load_config
from .models import AvailabilityClass, ProjectConfig, SplitConfig

__all__ = [
    "AvailabilityClass",
    "ProjectConfig",
    "SplitConfig",
    "load_config",
]

__version__ = "0.1.0"
