"""Module entry point for LinkedIn Visual Labs."""

# PROJECT7_PREDICTION_INTEGRITY_DISPATCH_START
import sys as _project7_sys

from .projects.p27_prediction_time_integrity_auditor.cli import (
    main as _project7_prediction_integrity_main,
)

if len(_project7_sys.argv) > 1 and _project7_sys.argv[1] == "prediction-integrity":
    raise SystemExit(_project7_prediction_integrity_main(_project7_sys.argv[2:]))
# PROJECT7_PREDICTION_INTEGRITY_DISPATCH_END

# PROJECT8_SAMPLED_METRICS_DISPATCH_START
import sys as _project8_sys

from .projects.p28_sampled_recommendation_metrics.cli import (
    main as _project8_sampled_metrics_main,
)

if len(_project8_sys.argv) > 1 and _project8_sys.argv[1] == "sampled-metrics":
    raise SystemExit(_project8_sampled_metrics_main(_project8_sys.argv[2:]))
# PROJECT8_SAMPLED_METRICS_DISPATCH_END


from linkedin_visual_labs.cli import app

if __name__ == "__main__":
    app()
