# Source Discrepancy Record

## Verified source locations

Kim et al.'s arXiv v2 PDF, page 3, Eq. (4), defines the point-adjustment protocol; Section 3.2 and Eqs. (5)-(7) discuss uniform random scores. The AAAI record identifies the final publication as AAAI 2022, pp. 7194-7201, published 2022-06-28, DOI `10.1609/aaai.v36i7.20680`. Accessed 2026-10-12.

## SOURCE_AS_PRINTED

Eq. (4) is operationally unambiguous for an inclusive source segment: one threshold crossing in `S_m` sets the segment's adjusted predictions to one. Eq. (6) prints a recall expression containing an anomaly-ratio factor `1/gamma` and exponent `(t_e - t_s)`. Eq. (7) prints a precision expression using the same endpoint-difference exponent.

## SOURCE_PROTOCOL_IMPLEMENTATION

The authors' `tadpak` repository describes itself as a PA%K implementation and exposes `pak(scores, targets, thres, k=20)`. Its public repository page did not expose a license file during this inspection; Project 9 will not copy its implementation. The repository is reference-only.

## OUR_EXPLICIT_GENERATIVE_MODEL

Project 9 uses event cardinality `L` and independent Bernoulli alerts, so the valid event-hit probability is `1-(1-q)^L`. It satisfies the endpoint checks in `EXPERIMENT_PROTOCOL.md` and is an independent model, not a correction attributed to Kim et al.

## RESOLVED_OR_UNRESOLVED_DISCREPANCY

`UNRESOLVED`. The printed Eq. (6) can be outside the probability range under literal endpoint values (for example, its `1/gamma` term with `delta=1` and `gamma<1`), and the inclusive set notation versus exponent `t_e-t_s` leaves a one-point cardinality ambiguity. The protocol definition itself remains usable. No erratum or author clarification was verified in this Step 2 screen, and Project 9 makes no accusation of error.
