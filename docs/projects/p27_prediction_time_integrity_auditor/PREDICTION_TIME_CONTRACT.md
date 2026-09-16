# Prediction-Time Contract

## Prediction moment

Immediately before the current outbound call begins.

## Availability classes

- PRE_DECISION
- KNOWN_AT_DECISION
- DURING_ACTION
- POST_OUTCOME
- UNKNOWN

## Fail-closed policy

DURING_ACTION, POST_OUTCOME, and UNKNOWN features are not permitted in the
prediction-time-safe pipeline.

`duration` is DURING_ACTION.

`campaign` is UNKNOWN in Version 1 because the dataset description does not
prove that the recorded value is finalized before the current contact begins.

Observed input classifications are canonical in:

`assets/p27_prediction_time_integrity_auditor/project_contract.json`
