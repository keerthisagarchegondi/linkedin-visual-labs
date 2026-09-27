# Project 8 — Final LinkedIn Post

I kept the models fixed and changed only the evaluation protocol.

The model ranking changed.

For this project, I reconstructed and extended a toy recommender-system
evaluation example using three fixed rank profiles across a catalog of
10,000 items.

Under **full-catalog Average Precision (AP)**:

**C > B > A**

Under **expected sampled AP with 99 negative items**:

**A > B > C**

That is a complete reversal in model ordering, even though the underlying
model rankings never changed.

The only thing that changed was the **evaluation candidate set**.

I then extended the analysis across a predefined sample-size grid:

`1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999`

The AP ordering changed multiple times as the number of sampled negatives
increased.

Computed-grid crossover intervals were:

- A/B: `500–1000`
- A/C: `200–500`
- B/C: `50–99`
- B/C: `200–500`

These are interval statements only — I did not interpolate exact crossover
points.

I also used **AUC as a negative control**.

Unlike AP, NDCG, and Recall@10, expected sampled AUC remained invariant
under the frozen sampling protocol, with ordering:

**A > C > B**

across the tested grid.

The analysis was validated using analytical expectations, Monte Carlo checks
at 1,000 and 10,000 repetitions, independent recomputation of critical
numerical values, reconciliation against 12 rounded source-reported values,
and the Project 8 regression suite.

The result is intentionally narrow:

This does **not** mean sampled metrics are universally unreliable.

It shows that, in this controlled toy example, **evaluation design alone can
change which model appears best**.

That makes the sampling protocol part of the measurement system — not just an
implementation detail.

Primary source:
Krichene & Rendle, *On Sampled Metrics for Item Recommendation*, KDD 2020.

#RecommendationSystems #RecommenderSystems #MachineLearning #DataScience
#MLOps #ModelEvaluation #Experimentation #Reproducibility #Python
