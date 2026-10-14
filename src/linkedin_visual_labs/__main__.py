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

# PROJECT9_ANOMALY_EVALUATION_DISPATCH_START
import sys as _project9_sys

from .projects.p29_anomaly_point_adjustment_audit.cli import (
    main as _project9_anomaly_evaluation_main,
)

if len(_project9_sys.argv) > 1 and _project9_sys.argv[1] == "anomaly-evaluation":
    raise SystemExit(_project9_anomaly_evaluation_main(_project9_sys.argv[2:]))
# PROJECT9_ANOMALY_EVALUATION_DISPATCH_END


from linkedin_visual_labs.cli import app

if __name__ == "__main__":
    app()
