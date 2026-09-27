# Project 8 — Evidence / Claim Linkage

## P8-C001 — SUPPORTED

**Claim:** The frozen A/B/C rank profiles are the source-reported toy-example inputs.

**Classification:** SOURCE_REPORTED

**Evidence:** reference_ranks.json, source_provenance.json

**Manuscript locations:** 2.1 Source-reported toy rank profiles, Appendix G

**Public safe:** YES

## P8-C002 — SUPPORTED

**Claim:** Full-catalog AP orders the profiles C>B>A.

**Classification:** REPLICATED_COMPUTATION

**Evidence:** full_metrics.csv

**Manuscript locations:** 5.1 Full-catalog metrics, Appendix B

**Public safe:** YES

## P8-C003 — SUPPORTED

**Claim:** Expected sampled AP at m=99 orders the profiles A>B>C.

**Classification:** REPLICATED_COMPUTATION

**Evidence:** sampled_metrics.csv

**Manuscript locations:** 5.2 Expected sampled metrics at m = 99, Appendix C

**Public safe:** YES

## P8-C004 — SUPPORTED

**Claim:** The full-catalog and expected sampled AP model orderings differ at m=99.

**Classification:** REPLICATED_COMPUTATION

**Evidence:** full_metrics.csv, sampled_metrics.csv

**Manuscript locations:** 5.3 AP model-selection reversal, Abstract

**Public safe:** YES

## P8-C005 — SUPPORTED

**Claim:** Expected sampled AUC equals full-catalog AUC under the frozen sampling protocol.

**Classification:** MATHEMATICAL_DERIVATION

**Evidence:** sample_size_sweep.csv, validation_results.json

**Manuscript locations:** 3.6 AUC, 5.5 AUC negative control, Appendix G

**Public safe:** YES

## P8-C006 — SUPPORTED

**Claim:** The predefined sample-size grid contains adjacent intervals where one or more pairwise model relations change.

**Classification:** REPLICATED_COMPUTATION

**Evidence:** sample_size_sweep.csv, release_data.json

**Manuscript locations:** 6. Sample-size sensitivity, Appendix D

**Public safe:** YES

## P8-C007 — REJECTED

**Claim:** An exact crossover sample size can be identified between grid points.

**Classification:** UNSUPPORTED

**Evidence:** None — rejected claim

**Manuscript locations:** Not used as a supported public claim

**Public safe:** NO

**Reason / boundary:** Step 4 computes only the preregistered sample-size grid and does not solve for unobserved exact crossover locations.

## P8-C008 — REJECTED

**Claim:** The Monte Carlo cross-model differences are paired estimates.

**Classification:** UNSUPPORTED

**Evidence:** None — rejected claim

**Manuscript locations:** Not used as a supported public claim

**Public safe:** NO

**Reason / boundary:** Models use independent deterministic random streams.

## P8-C009 — REJECTED

**Claim:** Every sampled recommendation metric must reverse every model ordering.

**Classification:** UNSUPPORTED

**Evidence:** None — rejected claim

**Manuscript locations:** Not used as a supported public claim

**Public safe:** NO

**Reason / boundary:** The frozen evidence is metric-specific; AUC is an explicit negative control.

## P8-C010 — SUPPORTED

**Claim:** Both preregistered Monte Carlo runs agree with analytical expectations under abs(MC-analytic) <= max(5*SE, 1e-3).

**Classification:** REPLICATED_COMPUTATION

**Evidence:** validation_results.json

**Manuscript locations:** 7. Monte Carlo validation, Appendix E, Appendix G

**Public safe:** YES
