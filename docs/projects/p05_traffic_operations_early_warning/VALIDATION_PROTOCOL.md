# Project 6 — Block 3 validation protocol

The protocol and primary numeric rules are bound by configs/p05_traffic_operations_early_warning/block3.json
and the pre-evaluation copies under ignored block3. Metrics retain original source
time. Baseline selection precedes warning evaluation; evaluation starts at1380s.
The 60s fast-track exception is explicit; the formal300s contract is preserved.

Independent pathway: validation.recompute_metrics reads raw tracked observations,
accepted crossings, source-frame availability and geometry. It does not call
metrics.calculate or metrics.eligible_inputs. It rebuilds confirmation, geometry,
low motion, ordered completed pairs, window membership, counts and medians. Each
of1800metric rows must agree within1e-9numeric tolerance. Missing expected values
must remain null/NaN. Baseline median/p10/p90/MAD and every normalization are checked
using the independent scalar values/validated metric columns. Separate onset streak
counts must reproduce exact original timestamps and signed or null arithmetic.

All mismatches fail. Fixed fixtures exercise missingness, sparse dwell, endpoint
exclusion, delayed confirmation, zero-baseline normalization, sustained/transient
queue, warning hysteresis, negative/zero/positive/missing onset results, predeclared
sensitivity, action enablement, evidence tampering and unsupported/preview claims.
No real-inference test or new weight is needed. Focused, all Project6, Ruff and
strict mypy precede the mandatory full pytest once on frozen final code/config.
Finalization asserts those hashes unchanged. No post-full implementation correction
is silently included in the full-suite claim.

This validates computation, not human-ground-truth identity, queue appearance,
causality or production performance. Independent labelled accuracy remains absent.
Raw/source imagery publication remains false. Aggregate-content approval is separate
from final-artifact publication approval. Negative/no-event results are preserved.

See BLOCK3_REVIEW.md for actual findings, failure fixes, limitations and log incident.
