# Metric Contract

Primary public headline metric is frozen as ROC AUC.

The benchmark must also calculate:

- PR AUC;
- Brier score;
- 10-bin expected calibration error;
- calibration slope/intercept where estimable;
- top-decile response rate;
- top-decile lift;
- conversions per 1,000 ranked calls;
- false-positive contacts;
- target prevalence;
- random-versus-temporal gap;
- feature-removal gap;
- duplicate-overlap count.

## Leakage Inflation Index

For higher-is-better metrics:

`leaked - safe`

For lower-is-better metrics:

`safe - leaked`

Therefore a positive value means the leaked evaluation looks better in the
metric's favorable direction.

This is a project-defined diagnostic, not an industry standard.

## Campaign Yield Overstatement

`leaked conversions/1000 - safe-test conversions/1000`

The formula is frozen before results.
