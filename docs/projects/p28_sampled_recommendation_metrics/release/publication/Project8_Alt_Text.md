# Project 8 — Final Figure / Dashboard / Video Alt Text

## Figure 1 — AP reversal
Bar charts compare Average Precision for the same three fixed rank profiles under full-catalog and sampled evaluation. In the full catalog, AP orders the models C > B > A, with displayed values A 0.0100, B 0.0101, and C 0.1014. With 99 sampled negatives, expected AP orders the same models A > B > C, with displayed values A 0.6366, B 0.3407, and C 0.3262. The figure emphasizes that the model rankings are unchanged and only the evaluation candidate set changes.

## Figure 2 — Sample-size sensitivity
Line chart of expected sampled Average Precision for models A, B, and C across sampled-negative counts 1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, and 9999. The ordering changes as sample size increases. Computed-grid crossover intervals are A/B 500–1000, A/C 200–500, and B/C 50–99 and 200–500. Exact crossover points are not inferred.

## Figure 3 — AUC negative control
Comparison of full-catalog and expected sampled AUC for the same fixed rank profiles. Expected sampled AUC equals full-catalog AUC under the frozen sampling protocol, so the ordering remains A > C > B across the tested sample-size grid. The figure serves as a negative control showing that not every evaluated metric changes ordering under candidate sampling.

## Dashboard
Interactive Project 8 dashboard summarizing the toy-example reproduction-and-extension study. It presents the full-catalog AP ordering C > B > A, expected sampled AP ordering at m = 99 of A > B > C, the sample-size sweep, crossover intervals, AUC negative control, and validation status. The dashboard states that the same fixed rank profiles can yield a different model winner when only the evaluation candidate set changes.

## 45-second explainer video
Animated explainer showing three fixed model rank profiles, full-catalog evaluation over 10,000 candidates, a sampled evaluation that retains the relevant item and draws 99 negatives, the AP ordering change from C > B > A to A > B > C, sample-size sensitivity, AUC as a negative control, and validation checks. The closing message is that evaluation protocol can affect which model appears best in this controlled toy example; it does not claim that every sampled metric reverses model ordering.
