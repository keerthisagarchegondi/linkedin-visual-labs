# Project 8 — Final LinkedIn Post

I kept the models fixed and changed only the evaluation protocol.

The model ranking changed.

For Project 8, I reconstructed and extended a published toy example in
recommender-system evaluation using three fixed rank profiles over a
catalog of 10,000 items.

Under **full-catalog Average Precision (AP)**:

**C > B > A**

Under **expected sampled AP with 99 negative items**:

**A > B > C**

That is a complete reversal in model ordering even though the underlying
rank profiles do not change.

The change comes from the **evaluation candidate set**.

I then evaluated a predefined negative-sample-size grid:

`1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999`

The computed AP ordering changes as sample size increases.

Observed crossover intervals on that grid were:

- A/B: `500–1000`
- A/C: `200–500`
- B/C: `50–99`
- B/C: `200–500`

These are grid intervals only — I did not interpolate exact crossover
points.

I also used **AUC as a negative control**.

Under the frozen sampling protocol, its expected value remains consistent
with the full-catalog ordering:

**A > C > B**

The analysis was checked with analytical expectations, Monte Carlo
validation at 1,000 and 10,000 repetitions, independent recomputation,
reconciliation against source-reported values, and the Project 8
regression suite.

The conclusion is intentionally narrow:

This does **not** show that sampled metrics are universally unreliable.

It shows that, in this controlled toy example, **evaluation design alone
can change which model appears best**.

That makes the sampling protocol part of the measurement system — not
just an implementation detail.

The manuscript, reproducibility archive, code, dashboard, and DOI are in
the first comment.

Primary source:
Krichene & Rendle, *On Sampled Metrics for Item Recommendation*, KDD 2020.

#RecommendationSystems #RecommenderSystems #MachineLearning
#ModelEvaluation #DataScience #Reproducibility #Python
