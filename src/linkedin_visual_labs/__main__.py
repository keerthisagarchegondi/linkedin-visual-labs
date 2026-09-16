"""Module entry point for LinkedIn Visual Labs."""

# PROJECT7_PREDICTION_INTEGRITY_DISPATCH_START
import sys as _project7_sys

from .projects.p27_prediction_time_integrity_auditor.cli import (
    main as _project7_prediction_integrity_main,
)

if len(_project7_sys.argv) > 1 and _project7_sys.argv[1] == "prediction-integrity":
    raise SystemExit(_project7_prediction_integrity_main(_project7_sys.argv[2:]))
# PROJECT7_PREDICTION_INTEGRITY_DISPATCH_END


from linkedin_visual_labs.cli import app

if __name__ == "__main__":
    app()
