# Product Contract

## Decision

Which customers should be prioritized for the next outbound call?

## Prediction moment

Immediately before the current call begins.

## Release question

Would the candidate receive PASS, WARN, or BLOCK based on reproducible
prediction-time integrity evidence?

## Dataset

Official UCI Bank Marketing dataset, dataset ID 222.

Preferred benchmark file:

`bank-additional-full.csv`

Expected:

- 41,188 rows;
- 20 inputs;
- binary target `y`;
- source ordering preserved;
- current official UCI DOI `10.24432/C5K306`;
- CC BY 4.0.

## V1 boundary

This project evaluates whether model evaluation is valid at prediction time.

It does not prove absence of all possible leakage and does not establish
production suitability outside the supported audit scope.
