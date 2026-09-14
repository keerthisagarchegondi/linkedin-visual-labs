# Project 6 — Presentation metric truth audit, Sub-step4.C.A

Current revised pack: **REVIEW_REQUIRED**, not approved. Prior mechanical PASS did
not establish semantic clarity or human design acceptance. This audit does not
rewrite upstream analytical evidence or regenerate the full presentation pack.

## Findings and corrected interpretation

The numerical comparison medians reproduce independently. Baseline is the median
of60 rolling endpoints1320..1379; later is the median of210 endpoints1440..1649.
Each occupancy window averages60 integer-second observed confirmed-track counts;
it is not instantaneous occupancy or a median of one-second density values.
Underlying integer-time support is1261..1379 versus1381..1649. Continuous event
support unions are(1260,1379] and(1380,1649], with confirmation available by each endpoint.
The original source-selected baseline remains[1260,1380). These are different
length screened summaries, with overlapping dependent windows. Like-for-like means
same definition and eligibility, not the same physical vehicles or equal exposure.

0.7583333333333333→4.45 is valid as a descriptive comparison of median60s mean
observed zone occupancy. Increase=486.8131868131869%; ratio=5.868131868131869×.
Use+486.8% or5.87× baseline, never treat a percentage increase as the ratio.
The comparison population has10 versus34 eligible IDs in the corresponding support
unions; movement uses gap-free observations and nested medians, not a fixed cohort.

Throughput2→3.5 is the median of unique eligible exits in60s rolling windows.
Movement0.007695508997332229→0.008994308146367019 (+16.877365090275886%)
is median across windows of median across nonmissing integer seconds of median
eligible track image-plane displacement rates. It is not speed or a pooled
vehicle-weighted mean. At least10 valid integer-second medians support each window.

49.15s is median of108 supported rolling dwell medians in[1440,1650), with3–4
completed journeys per supported window.108 is not a count of independent journeys.
Baseline has0 supported dwell windows; no change can be calculated. Full-source
median of65 unique eligible completed journeys is42.0s, a different statistic.
Dwell is secondary only; display sample/caveat or omit it.

572 candidate IDs /178 confirmed IDs /65 complete journeys and131 entries /81 exits
are full[0,1800) processing counts, not a current window or physical vehicle census.
The ten-minute map depicts[1200,1800) history; its full-source cards must stay
separate. Under current-observation eligibility64 confirmed IDs occur in this map
interval. Retrospective trajectory confirmation and online-known observation
confirmation are different populations; new overlays use the latter explicitly.

WARNING is continuous on ticks1440..1736, representing[1440,1737),297s until NORMAL.
The complete warning-rule flag is true for only53 ticks across evaluation. The
latched state includes hysteresis; it does not prove297s of continuously qualifying
drivers. Queue outcome never qualifies; null lead time remains unchanged.

## Misleading or ambiguous earlier wording

- Dashboard “warning snapshot24:00” with4.45/+486.8%/3.5/+16.9% used later interval
  summaries rather than the24:00 values. A distant footnote did not sufficiently
  resolve the mixed timestamp/population impression.
- “0.76 vehicles”, “Density4.45”, “3.5 exits/min” and “Movement+16.9%” need explicit
  rolling statistic, support interval and units beside the value.
- Full-source131/81 counts next to rolling density invite an invalid local imbalance
  inference. They do not prove50 additional real vehicles or sustained accumulation.
- “Dwell49.15s” needs108 supported windows,3–4 journeys/window and no baseline caveat.
- “Several signals deteriorated” and “healthy flow” overinterpret increased activity.
  Density/imbalance rise while discharge and movement remain active; no causal or
  service-health threshold establishes deterioration of every flow dimension.
- “297s warning” must identify the latched state, not full-rule persistence.
- “Avoid false escalation” is an objective, not validated reduction in false alarms.
- Queue not confirmed describes the configured rule; it does not prove no real queue.
- The original static image's178/65/81 cards were explicitly full-source, but should
  remain visibly separate from its600s trajectory population.

## Canonical five primary KPIs

Use one snapshot at24:00: WARNING;60s mean observed occupancy3.70;
entry–exit balance+5 (8 entries/3 exits); throughput3 eligible exits/60s;
relative movement index0.011305435163455783 image diagonals/s.
All numeric values use(1380,1440]; no interval medians or whole-source totals in
that strip. Adjacent comparison, separately labelled: (1440,1500] has5 entries,
4 exits,+1 balance. This supports continuing discharge, not a forced failure story.
Secondary: sample-supported dwell, full-source processing counts, independent queue
validation. Remove dwell from headline KPIs.

## Evidence-supported story

Higher observed zone accumulation and positive entry–exit imbalance, with continuing discharge. A configured pressure WARNING qualified at24:00; independent queue validation did not qualify. Relative movement/throughput comparison medians increased, so congestion, globally deteriorating flow and healthy discharge are not established. Describe accumulation/flow imbalance with a configured warning, not proven congestion prediction.

## Recovered visual layers and limits

Earlier trajectory_map.png/video keyframes contain dense accumulated true paths,
completed/incomplete line distinctions, ROI/queue outlines, entry/exit geometry,
state timeline and actual metric trend insets. Detection/tracking and crossing
contact sheets show source-linked boxes and curved paths over actual cars.
The richer target combines these with real pixels; no schematic source replacement.
New historical trails fade, never bridge gaps>1s, and retain original timestamps.
The trajectory histogram/contours are a new presentation-only derivation, not an
earlier validated vehicle-density metric. Observation weighting emphasizes track
duration and repeated positions; no physical occupancy/queue-hotspot claim follows.
Flow arrows encode mean local image-plane direction only, never calibrated speed.
No new analytical thresholds, inference, tracking, events, metric-stage or warning
stage execution is allowed. Audit reductions only read existing lower-level outputs.

## Complete canonical truth records

Machine-readable records: outputs/p05_traffic_operations_early_warning/data/presentation_metrics.json.
Every record supplies all15 requested fields, hashes, exact endpoint semantics,
population, numerator/denominator (or explicit nonapplicability), allowed wording
and presentation-only claim status. Technical/layout numbers are recorded separately.
The HTML review table contains the same records, including full detail expansion.

Later dwell has12 distinct contributing journeys across its108 supported overlapping windows.

### baseline_density_window_mean

- **metric_id:** "baseline_density_window_mean"
- **metric_name:** "Baseline Observed zone occupancy"
- **exact_value:** 0.7583333333333333
- **unit:** "mean observed vehicle tracks"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); each window(t-60,t]. Integer-second sample union [1261,1379] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Mean of60 integer-second observed confirmed-track counts, then median across selected endpoints"
- **numerator:** "At each endpoint, sum60 integer-second eligible observed-track counts; outer median is an order statistic."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 60, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of60s rolling observed zone occupancy: 0.7583333333333333; endpoints[1320,1380)."
- **definition:** "Mean of60 integer-second observed confirmed-track counts, then median across selected endpoints"
- **outer_sample_size:** 60
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### baseline_throughput

- **metric_id:** "baseline_throughput"
- **metric_name:** "Baseline Discharge / throughput"
- **exact_value:** 2.0
- **unit:** "eligible exits per60s"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); each window(t-60,t]. Integer-second sample union [1261,1379] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Unique eligible EXIT track IDs in(t-60,t], available by t; median across endpoints"
- **numerator:** "At each endpoint, count unique eligible EXIT track IDs; outer median is an order statistic."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 60, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of60s rolling discharge / throughput: 2.0; endpoints[1320,1380)."
- **definition:** "Unique eligible EXIT track IDs in(t-60,t], available by t; median across endpoints"
- **outer_sample_size:** 60
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### baseline_movement_index

- **metric_id:** "baseline_movement_index"
- **metric_name:** "Baseline Relative movement index"
- **exact_value:** 0.007695508997332229
- **unit:** "image diagonals/second"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); each window(t-60,t]. Integer-second sample union [1261,1379] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Median of per-second medians of eligible gap-free track displacements; >=10 nonmissing seconds per60s window; then median across endpoints"
- **numerator:** "No arithmetic numerator: nested medians of normalized displacement rates."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 60, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of60s rolling relative movement index: 0.007695508997332229; endpoints[1320,1380)."
- **definition:** "Median of per-second medians of eligible gap-free track displacements; >=10 nonmissing seconds per60s window; then median across endpoints"
- **outer_sample_size:** 60
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### baseline_inflow_outflow_imbalance

- **metric_id:** "baseline_inflow_outflow_imbalance"
- **metric_name:** "Baseline Flow imbalance"
- **exact_value:** -1.0
- **unit:** "entries minus exits per60s"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); each window(t-60,t]. Integer-second sample union [1261,1379] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Unique eligible ENTRY IDs minus unique EXIT IDs in(t-60,t], available by t; median across endpoints"
- **numerator:** "At each endpoint, eligible unique ENTRY count minus eligible unique EXIT count; outer median."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 60, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of60s rolling flow imbalance: -1.0; endpoints[1320,1380)."
- **definition:** "Unique eligible ENTRY IDs minus unique EXIT IDs in(t-60,t], available by t; median across endpoints"
- **outer_sample_size:** 60
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### baseline_queue_count

- **metric_id:** "baseline_queue_count"
- **metric_name:** "Baseline Configured low-motion queue count"
- **exact_value:** 0.0
- **unit:** "eligible observed queue-zone tracks"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); point-count at each selected tick; no rolling window for queue_count"
- **aggregation_type:** "median_of_point_counts"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Count at each integer second of eligible observed tracks in queue zone with active low motion; outer median is NOT a60s mean"
- **numerator:** "Eligible observed queue-zone low-motion track count at each selected tick; outer median."
- **denominator:** {"per_window_seconds": null, "outer_valid_endpoints": 60, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of point-in-time configured low-motion queue count: 0.0; endpoints[1320,1380)."
- **definition:** "Count at each integer second of eligible observed tracks in queue zone with active low motion; outer median is NOT a60s mean"
- **outer_sample_size:** 60
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### baseline_median_completed_dwell_seconds

- **metric_id:** "baseline_median_completed_dwell_seconds"
- **metric_name:** "Baseline Completed journey dwell"
- **exact_value:** null
- **unit:** "seconds"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "Endpoint selection [1320,1380); each window(t-60,t]. Integer-second sample union [1261,1379] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Median completed eligible dwell for exits in(t-60,t], available by t; >=3 journeys; then median across supported endpoints"
- **numerator:** "No arithmetic numerator: median across supported window medians of(exit_timestamp-entry_timestamp)."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 0, "outer_selected_endpoints": 60}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Baseline median of60s rolling completed journey dwell: unavailable; endpoints[1320,1380)."
- **definition:** "Median completed eligible dwell for exits in(t-60,t], available by t; >=3 journeys; then median across supported endpoints"
- **outer_sample_size:** 0
- **observed_track_ids_in_support_union:** 10
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_density_window_mean

- **metric_id:** "later_density_window_mean"
- **metric_name:** "Later Observed zone occupancy"
- **exact_value:** 4.45
- **unit:** "mean observed vehicle tracks"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); each window(t-60,t]. Integer-second sample union [1381,1649] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Mean of60 integer-second observed confirmed-track counts, then median across selected endpoints"
- **numerator:** "At each endpoint, sum60 integer-second eligible observed-track counts; outer median is an order statistic."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 210, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of60s rolling observed zone occupancy: 4.45; endpoints[1440,1650)."
- **definition:** "Mean of60 integer-second observed confirmed-track counts, then median across selected endpoints"
- **outer_sample_size:** 210
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_throughput

- **metric_id:** "later_throughput"
- **metric_name:** "Later Discharge / throughput"
- **exact_value:** 3.5
- **unit:** "eligible exits per60s"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); each window(t-60,t]. Integer-second sample union [1381,1649] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Unique eligible EXIT track IDs in(t-60,t], available by t; median across endpoints"
- **numerator:** "At each endpoint, count unique eligible EXIT track IDs; outer median is an order statistic."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 210, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of60s rolling discharge / throughput: 3.5; endpoints[1440,1650)."
- **definition:** "Unique eligible EXIT track IDs in(t-60,t], available by t; median across endpoints"
- **outer_sample_size:** 210
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_movement_index

- **metric_id:** "later_movement_index"
- **metric_name:** "Later Relative movement index"
- **exact_value:** 0.008994308146367019
- **unit:** "image diagonals/second"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); each window(t-60,t]. Integer-second sample union [1381,1649] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Median of per-second medians of eligible gap-free track displacements; >=10 nonmissing seconds per60s window; then median across endpoints"
- **numerator:** "No arithmetic numerator: nested medians of normalized displacement rates."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 210, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of60s rolling relative movement index: 0.008994308146367019; endpoints[1440,1650)."
- **definition:** "Median of per-second medians of eligible gap-free track displacements; >=10 nonmissing seconds per60s window; then median across endpoints"
- **outer_sample_size:** 210
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_inflow_outflow_imbalance

- **metric_id:** "later_inflow_outflow_imbalance"
- **metric_name:** "Later Flow imbalance"
- **exact_value:** 2.0
- **unit:** "entries minus exits per60s"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); each window(t-60,t]. Integer-second sample union [1381,1649] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Unique eligible ENTRY IDs minus unique EXIT IDs in(t-60,t], available by t; median across endpoints"
- **numerator:** "At each endpoint, eligible unique ENTRY count minus eligible unique EXIT count; outer median."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 210, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of60s rolling flow imbalance: 2.0; endpoints[1440,1650)."
- **definition:** "Unique eligible ENTRY IDs minus unique EXIT IDs in(t-60,t], available by t; median across endpoints"
- **outer_sample_size:** 210
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_queue_count

- **metric_id:** "later_queue_count"
- **metric_name:** "Later Configured low-motion queue count"
- **exact_value:** 0.0
- **unit:** "eligible observed queue-zone tracks"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); point-count at each selected tick; no rolling window for queue_count"
- **aggregation_type:** "median_of_point_counts"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Count at each integer second of eligible observed tracks in queue zone with active low motion; outer median is NOT a60s mean"
- **numerator:** "Eligible observed queue-zone low-motion track count at each selected tick; outer median."
- **denominator:** {"per_window_seconds": null, "outer_valid_endpoints": 210, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of point-in-time configured low-motion queue count: 0.0; endpoints[1440,1650)."
- **definition:** "Count at each integer second of eligible observed tracks in queue zone with active low motion; outer median is NOT a60s mean"
- **outer_sample_size:** 210
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### later_median_completed_dwell_seconds

- **metric_id:** "later_median_completed_dwell_seconds"
- **metric_name:** "Later Completed journey dwell"
- **exact_value:** 49.14999999999998
- **unit:** "seconds"
- **start_timestamp:** 1440
- **end_timestamp:** 1650
- **aggregation_window:** "Endpoint selection [1440,1650); each window(t-60,t]. Integer-second sample union [1381,1649] inclusive."
- **aggregation_type:** "median_of_rolling_statistics"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations. Median completed eligible dwell for exits in(t-60,t], available by t; >=3 journeys; then median across supported endpoints"
- **numerator:** "No arithmetic numerator: median across supported window medians of(exit_timestamp-entry_timestamp)."
- **denominator:** {"per_window_seconds": 60, "outer_valid_endpoints": 108, "outer_selected_endpoints": 210}
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median of60s rolling completed journey dwell: 49.14999999999998; endpoints[1440,1650)."
- **definition:** "Median completed eligible dwell for exits in(t-60,t], available by t; >=3 journeys; then median across supported endpoints"
- **outer_sample_size:** 108
- **observed_track_ids_in_support_union:** 34
- **comparison_caveat:** "Same eligibility criteria, not same vehicle identities; unequal60 vs210 overlapping windows. Limited screened baseline; descriptive, not held-out causal comparison."

### density_window_mean_percent

- **metric_id:** "density_window_mean_percent"
- **metric_name:** "Zone occupancy descriptive comparison"
- **exact_value:** 486.81318681318686
- **unit:** "percent"
- **start_timestamp:** 1320
- **end_timestamp:** 1650
- **aggregation_window:** "Disjoint endpoint selections[1320,1380) and[1440,1650); same60s rolling definition"
- **aggregation_type:** "comparison_of_rolling_medians"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 3.691666666666667
- **denominator:** 0.7583333333333333
- **baseline_comparator:** 0.7583333333333333
- **percentage_change_formula:** "100*(later_median-baseline_median)/baseline_median"
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/release_data.json", "sha256": "c80ff9c1da0bbe2c1ca603731635419165a677b1b214635a197c0d68e0947751"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Zone occupancy: +486.8% between the specified rolling-median comparison intervals."

### throughput_percent

- **metric_id:** "throughput_percent"
- **metric_name:** "Throughput descriptive comparison"
- **exact_value:** 75.0
- **unit:** "percent"
- **start_timestamp:** 1320
- **end_timestamp:** 1650
- **aggregation_window:** "Disjoint endpoint selections[1320,1380) and[1440,1650); same60s rolling definition"
- **aggregation_type:** "comparison_of_rolling_medians"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 1.5
- **denominator:** 2.0
- **baseline_comparator:** 2.0
- **percentage_change_formula:** "100*(later_median-baseline_median)/baseline_median"
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/release_data.json", "sha256": "c80ff9c1da0bbe2c1ca603731635419165a677b1b214635a197c0d68e0947751"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Throughput: +75.0% between the specified rolling-median comparison intervals."

### movement_index_percent

- **metric_id:** "movement_index_percent"
- **metric_name:** "Relative movement descriptive comparison"
- **exact_value:** 16.877365090275887
- **unit:** "percent"
- **start_timestamp:** 1320
- **end_timestamp:** 1650
- **aggregation_window:** "Disjoint endpoint selections[1320,1380) and[1440,1650); same60s rolling definition"
- **aggregation_type:** "comparison_of_rolling_medians"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 0.0012987991490347895
- **denominator:** 0.007695508997332229
- **baseline_comparator:** 0.007695508997332229
- **percentage_change_formula:** "100*(later_median-baseline_median)/baseline_median"
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/release_data.json", "sha256": "c80ff9c1da0bbe2c1ca603731635419165a677b1b214635a197c0d68e0947751"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Relative movement: +16.9% between the specified rolling-median comparison intervals."

### density_ratio

- **metric_id:** "density_ratio"
- **metric_name:** "Zone occupancy ratio"
- **exact_value:** 5.868131868131869
- **unit:** "times baseline"
- **start_timestamp:** 1320
- **end_timestamp:** 1650
- **aggregation_window:** "Same two rolling-median selections"
- **aggregation_type:** "comparison_of_rolling_medians"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 4.45
- **denominator:** 0.7583333333333333
- **baseline_comparator:** 0.7583333333333333
- **percentage_change_formula:** "later/baseline (ratio, not percentage increase)"
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Later median rolling occupancy was5.87 times baseline; not a current count."

### at_1380_density_mean

- **metric_id:** "at_1380_density_mean"
- **metric_name:** "60s mean observed zone occupancy"
- **exact_value:** 0.6833333333333333
- **unit:** "mean observed vehicle tracks"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "(1320,1380],60 original seconds; occupancy integer ticks 1321..1380"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 41
- **denominator:** 60
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "60s mean observed zone occupancy: 0.6833333333333333; last60s ending23:00."
- **event_ids:** ["event:699", "event:705", "event:709", "event:713", "event:719"]
- **interval_boundary:** "left-open,right-closed"

### at_1380_entry

- **metric_id:** "at_1380_entry"
- **metric_name:** "Entries"
- **exact_value:** 3
- **unit:** "eligible entries"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "(1320,1380],60 original seconds; occupancy integer ticks 1321..1380"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 3
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entries: 3; last60s ending23:00."
- **event_ids:** ["event:699", "event:705", "event:709", "event:713", "event:719"]
- **interval_boundary:** "left-open,right-closed"

### at_1380_exit

- **metric_id:** "at_1380_exit"
- **metric_name:** "Exits /60s"
- **exact_value:** 2
- **unit:** "eligible exits"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "(1320,1380],60 original seconds; occupancy integer ticks 1321..1380"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 2
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Exits /60s: 2; last60s ending23:00."
- **event_ids:** ["event:699", "event:705", "event:709", "event:713", "event:719"]
- **interval_boundary:** "left-open,right-closed"

### at_1380_imbalance

- **metric_id:** "at_1380_imbalance"
- **metric_name:** "Entry–exit balance"
- **exact_value:** 1
- **unit:** "entries minus exits"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "(1320,1380],60 original seconds; occupancy integer ticks 1321..1380"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 1
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entry–exit balance: 1; last60s ending23:00."
- **event_ids:** ["event:699", "event:705", "event:709", "event:713", "event:719"]
- **interval_boundary:** "left-open,right-closed"

### at_1380_movement_index

- **metric_id:** "at_1380_movement_index"
- **metric_name:** "Relative movement index"
- **exact_value:** 0.007999546193544146
- **unit:** "image diagonals/second"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "(1320,1380],60 original seconds; occupancy integer ticks 1321..1380"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** "median of per-second medians"
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Relative movement index: 0.007999546193544146; last60s ending23:00."
- **event_ids:** ["event:699", "event:705", "event:709", "event:713", "event:719"]
- **interval_boundary:** "left-open,right-closed"

### at_1440_density_mean

- **metric_id:** "at_1440_density_mean"
- **metric_name:** "60s mean observed zone occupancy"
- **exact_value:** 3.7
- **unit:** "mean observed vehicle tracks"
- **start_timestamp:** 1380
- **end_timestamp:** 1440
- **aggregation_window:** "(1380,1440],60 original seconds; occupancy integer ticks 1381..1440"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 222
- **denominator:** 60
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "60s mean observed zone occupancy: 3.7; last60s ending24:00."
- **event_ids:** ["event:716", "event:740", "event:744", "event:748", "event:753", "event:759", "event:766", "event:774", "event:780", "event:785", "event:791"]
- **interval_boundary:** "left-open,right-closed"

### at_1440_entry

- **metric_id:** "at_1440_entry"
- **metric_name:** "Entries"
- **exact_value:** 8
- **unit:** "eligible entries"
- **start_timestamp:** 1380
- **end_timestamp:** 1440
- **aggregation_window:** "(1380,1440],60 original seconds; occupancy integer ticks 1381..1440"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 8
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entries: 8; last60s ending24:00."
- **event_ids:** ["event:716", "event:740", "event:744", "event:748", "event:753", "event:759", "event:766", "event:774", "event:780", "event:785", "event:791"]
- **interval_boundary:** "left-open,right-closed"

### at_1440_exit

- **metric_id:** "at_1440_exit"
- **metric_name:** "Exits /60s"
- **exact_value:** 3
- **unit:** "eligible exits"
- **start_timestamp:** 1380
- **end_timestamp:** 1440
- **aggregation_window:** "(1380,1440],60 original seconds; occupancy integer ticks 1381..1440"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 3
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Exits /60s: 3; last60s ending24:00."
- **event_ids:** ["event:716", "event:740", "event:744", "event:748", "event:753", "event:759", "event:766", "event:774", "event:780", "event:785", "event:791"]
- **interval_boundary:** "left-open,right-closed"

### at_1440_imbalance

- **metric_id:** "at_1440_imbalance"
- **metric_name:** "Entry–exit balance"
- **exact_value:** 5
- **unit:** "entries minus exits"
- **start_timestamp:** 1380
- **end_timestamp:** 1440
- **aggregation_window:** "(1380,1440],60 original seconds; occupancy integer ticks 1381..1440"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 5
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entry–exit balance: 5; last60s ending24:00."
- **event_ids:** ["event:716", "event:740", "event:744", "event:748", "event:753", "event:759", "event:766", "event:774", "event:780", "event:785", "event:791"]
- **interval_boundary:** "left-open,right-closed"

### at_1440_movement_index

- **metric_id:** "at_1440_movement_index"
- **metric_name:** "Relative movement index"
- **exact_value:** 0.011305435163455783
- **unit:** "image diagonals/second"
- **start_timestamp:** 1380
- **end_timestamp:** 1440
- **aggregation_window:** "(1380,1440],60 original seconds; occupancy integer ticks 1381..1440"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** "median of per-second medians"
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Relative movement index: 0.011305435163455783; last60s ending24:00."
- **event_ids:** ["event:716", "event:740", "event:744", "event:748", "event:753", "event:759", "event:766", "event:774", "event:780", "event:785", "event:791"]
- **interval_boundary:** "left-open,right-closed"

### at_1500_density_mean

- **metric_id:** "at_1500_density_mean"
- **metric_name:** "60s mean observed zone occupancy"
- **exact_value:** 4.683333333333334
- **unit:** "mean observed vehicle tracks"
- **start_timestamp:** 1440
- **end_timestamp:** 1500
- **aggregation_window:** "(1440,1500],60 original seconds; occupancy integer ticks 1441..1500"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 281
- **denominator:** 60
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "60s mean observed zone occupancy: 4.683333333333334; last60s ending25:00."
- **event_ids:** ["event:771", "event:777", "event:788", "event:794", "event:797", "event:800", "event:806", "event:816", "event:821"]
- **interval_boundary:** "left-open,right-closed"

### at_1500_entry

- **metric_id:** "at_1500_entry"
- **metric_name:** "Entries"
- **exact_value:** 5
- **unit:** "eligible entries"
- **start_timestamp:** 1440
- **end_timestamp:** 1500
- **aggregation_window:** "(1440,1500],60 original seconds; occupancy integer ticks 1441..1500"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 5
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entries: 5; last60s ending25:00."
- **event_ids:** ["event:771", "event:777", "event:788", "event:794", "event:797", "event:800", "event:806", "event:816", "event:821"]
- **interval_boundary:** "left-open,right-closed"

### at_1500_exit

- **metric_id:** "at_1500_exit"
- **metric_name:** "Exits /60s"
- **exact_value:** 4
- **unit:** "eligible exits"
- **start_timestamp:** 1440
- **end_timestamp:** 1500
- **aggregation_window:** "(1440,1500],60 original seconds; occupancy integer ticks 1441..1500"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 4
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Exits /60s: 4; last60s ending25:00."
- **event_ids:** ["event:771", "event:777", "event:788", "event:794", "event:797", "event:800", "event:806", "event:816", "event:821"]
- **interval_boundary:** "left-open,right-closed"

### at_1500_imbalance

- **metric_id:** "at_1500_imbalance"
- **metric_name:** "Entry–exit balance"
- **exact_value:** 1
- **unit:** "entries minus exits"
- **start_timestamp:** 1440
- **end_timestamp:** 1500
- **aggregation_window:** "(1440,1500],60 original seconds; occupancy integer ticks 1441..1500"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 1
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Entry–exit balance: 1; last60s ending25:00."
- **event_ids:** ["event:771", "event:777", "event:788", "event:794", "event:797", "event:800", "event:806", "event:816", "event:821"]
- **interval_boundary:** "left-open,right-closed"

### at_1500_movement_index

- **metric_id:** "at_1500_movement_index"
- **metric_name:** "Relative movement index"
- **exact_value:** 0.00903810240553118
- **unit:** "image diagonals/second"
- **start_timestamp:** 1440
- **end_timestamp:** 1500
- **aggregation_window:** "(1440,1500],60 original seconds; occupancy integer ticks 1441..1500"
- **aggregation_type:** "rolling_endpoint"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** "median of per-second medians"
- **denominator:** "not applicable: count/order statistic"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}, {"path": "outputs/p05_traffic_operations_early_warning/data/operational_metrics.parquet", "sha256": "a4d6d47ad7191e680516ba114a41b2b3f249cdd55213732f6e4fd2fdcf5999f5"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Relative movement index: 0.00903810240553118; last60s ending25:00."
- **event_ids:** ["event:771", "event:777", "event:788", "event:794", "event:797", "event:800", "event:806", "event:816", "event:821"]
- **interval_boundary:** "left-open,right-closed"

### whole_candidates

- **metric_id:** "whole_candidates"
- **metric_name:** "Full-source candidates"
- **exact_value:** 572
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Created tracker identities, including unconfirmed fragments; not detection boxes or unique physical vehicles. Birth score>=0.55; duplicate suppression configured."
- **numerator:** 572
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "572 candidates — full30-min source processing count."

### whole_confirmed

- **metric_id:** "whole_confirmed"
- **metric_name:** "Full-source confirmed"
- **exact_value:** 178
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Clip-local tracker identities with at least3 observation hits, accepted under metric eligibility; not independent physical vehicle count."
- **numerator:** 178
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "178 confirmed — full30-min source processing count."

### whole_completed

- **metric_id:** "whole_completed"
- **metric_name:** "Full-source completed"
- **exact_value:** 65
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Confirmed track IDs with ordered ENTRY then EXIT, no observation gap>1s over retained history; dwell=exit-entry."
- **numerator:** 65
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "65 completed — full30-min source processing count."

### whole_entries

- **metric_id:** "whole_entries"
- **metric_name:** "Full-source entries"
- **exact_value:** 131
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Unique eligible directional ENTRY crossings; at most one per track."
- **numerator:** 131
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "131 entries — full30-min source processing count."

### whole_exits

- **metric_id:** "whole_exits"
- **metric_name:** "Full-source exits"
- **exact_value:** 81
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Unique eligible directional EXIT crossings; at most one per track."
- **numerator:** 81
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "81 exits — full30-min source processing count."

### whole_incomplete

- **metric_id:** "whole_incomplete"
- **metric_name:** "Full-source incomplete"
- **exact_value:** 507
- **unit:** "track IDs / events as specified"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Journey rows excluded from completed dwell, including unconfirmed fragments and censored/gapped histories."
- **numerator:** 507
- **denominator:** "not applicable: count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/track_inventory.parquet", "sha256": "c836b3b6eea644effa6757b977d69c014f893b43ad2f9ac613d10e625b084852"}, {"path": "outputs/p05_traffic_operations_early_warning/data/crossing_events.parquet", "sha256": "cbd9864e24143ec32dcd4807ea488052bbee529648b54a964abb26dd4ca2b795"}, {"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "507 incomplete — full30-min source processing count."

### LOW_MOTION_START

- **metric_id:** "LOW_MOTION_START"
- **metric_name:** "LOW_MOTION_START"
- **exact_value:** 10
- **unit:** "event records"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Retrospectively confirmed trajectory events; low motion<0.002 image diagonals/s for3s; not independent queue qualification."
- **numerator:** 10
- **denominator:** "not applicable"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/zone_events.parquet", "sha256": "328556e68a17a238322ad243e5b59de2872f1d18057a3fbc322a1355a88d0c04"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "10 LOW_MOTION_START events, full30-min source; not queue events."

### LOW_MOTION_END

- **metric_id:** "LOW_MOTION_END"
- **metric_name:** "LOW_MOTION_END"
- **exact_value:** 10
- **unit:** "event records"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800) whole source"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Retrospectively confirmed trajectory events; low motion<0.002 image diagonals/s for3s; not independent queue qualification."
- **numerator:** 10
- **denominator:** "not applicable"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/zone_events.parquet", "sha256": "328556e68a17a238322ad243e5b59de2872f1d18057a3fbc322a1355a88d0c04"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "10 LOW_MOTION_END events, full30-min source; not queue events."

### whole_dwell

- **metric_id:** "whole_dwell"
- **metric_name:** "Full-source completed journey median"
- **exact_value:** 42.0
- **unit:** "seconds"
- **start_timestamp:** 0
- **end_timestamp:** 1800
- **aggregation_window:** "[0,1800);65 unique completed journeys"
- **aggregation_type:** "whole_episode"
- **eligible_population:** "Confirmed track IDs with ordered ENTRY then EXIT, no observation gap>1s over retained history; dwell=exit-entry."
- **numerator:** "median of65 journey durations"
- **denominator:** 65
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/journeys.parquet", "sha256": "a0c3b543f427685933b06f7263f15f246a46ad503c2cb226b982247551aebaea"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Full-source median completed dwell42.0s (65 eligible journeys); different statistic from rolling49.15s."

### warning_state

- **metric_id:** "warning_state"
- **metric_name:** "Traffic state"
- **exact_value:** "WARNING"
- **unit:** "configured state"
- **start_timestamp:** 1440
- **end_timestamp:** 1440
- **aggregation_window:** "Point at1440s; state persists through1736s tick"
- **aggregation_type:** "point_in_time"
- **eligible_population:** "Frozen state-machine output; rule plus hysteresis"
- **numerator:** "three drivers at first full30s persistence completion"
- **denominator:** "configured rule"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_timeline.parquet", "sha256": "0e4a566361eb957ccf815bda9869ab3d6751c46fef3d0692da4a120925b5e7fa"}, {"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Configured WARNING first qualified at24:00."

### warning_duration

- **metric_id:** "warning_duration"
- **metric_name:** "Continuous latched WARNING state"
- **exact_value:** 297
- **unit:** "seconds"
- **start_timestamp:** 1440
- **end_timestamp:** 1737
- **aggregation_window:** "[1440,1737);1s grid, next NORMAL at1737"
- **aggregation_type:** "interval_duration"
- **eligible_population:** "WARNING state rows (no CRITICAL in this episode)"
- **numerator:** 297
- **denominator:** "elapsed original seconds"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_timeline.parquet", "sha256": "0e4a566361eb957ccf815bda9869ab3d6751c46fef3d0692da4a120925b5e7fa"}, {"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "WARNING state lasted4m57s,24:00–28:57, including reset hysteresis; not continuous triggering-rule satisfaction."

### warning_flag

- **metric_id:** "warning_flag"
- **metric_name:** "Complete warning-rule flag ticks"
- **exact_value:** 53
- **unit:** "1s grid ticks"
- **start_timestamp:** 1380
- **end_timestamp:** 1800
- **aggregation_window:** "[1380,1800);not necessarily contiguous"
- **aggregation_type:** "interval_aggregate"
- **eligible_population:** "warning_qualified=true rows"
- **numerator:** 53
- **denominator:** "not elapsed continuous streak"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_timeline.parquet", "sha256": "0e4a566361eb957ccf815bda9869ab3d6751c46fef3d0692da4a120925b5e7fa"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "53 evaluation ticks satisfied the full warning-rule flag; distinct from297s latched WARNING state."

### queue_result

- **metric_id:** "queue_result"
- **metric_name:** "Independent queue validation"
- **exact_value:** "NO_VISIBLE_QUEUE_EVENT"
- **unit:** "classification"
- **start_timestamp:** 1380
- **end_timestamp:** 1800
- **aggregation_window:** "[1380,1800) evaluation"
- **aggregation_type:** "interval_aggregate"
- **eligible_population:** "Configured queue outcome; no independent physical ground truth"
- **numerator:** "no qualified outcome"
- **denominator:** "configured thresholds,not accuracy denominator"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/queue_outcome_timeline.parquet", "sha256": "a445e9199be9310679d9ca0398a1f6017d58915b91f2c84da7982cd04cd0992a"}, {"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Independent configured queue rule did not qualify; physical queue absence is not established."

### lead

- **metric_id:** "lead"
- **metric_name:** "Lead time"
- **exact_value:** null
- **unit:** "seconds"
- **start_timestamp:** 1380
- **end_timestamp:** 1800
- **aggregation_window:** "[1380,1800) evaluation"
- **aggregation_type:** "event_difference"
- **eligible_population:** "Qualified warning and independent queue onsets"
- **numerator:** "queue onset unavailable"
- **denominator:** "not applicable"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Lead time not reportable: no qualifying queue onset."

### baseline_false_warning

- **metric_id:** "baseline_false_warning"
- **metric_name:** "In-sample baseline warning exposure"
- **exact_value:** 0
- **unit:** "warning seconds"
- **start_timestamp:** 1320
- **end_timestamp:** 1380
- **aggregation_window:** "[1320,1380);60 evaluable1s ticks"
- **aggregation_type:** "interval_aggregate"
- **eligible_population:** "In-sample calibration diagnostic"
- **numerator:** 0
- **denominator:** 60
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "0 warning seconds /60 evaluable in-sample baseline seconds;0 episodes, not false-alarm accuracy."

### transitions

- **metric_id:** "transitions"
- **metric_name:** "State transitions"
- **exact_value:** [{"timestamp": 1380.0, "state": "NORMAL", "drivers": ""}, {"timestamp": 1383.0, "state": "WATCH", "drivers": "INFLOW_OUTFLOW_IMBALANCE"}, {"timestamp": 1440.0, "state": "WARNING", "drivers": "DENSITY_LEVEL|INFLOW_OUTFLOW_IMBALANCE|DENSITY_TREND"}, {"timestamp": 1737.0, "state": "NORMAL", "drivers": ""}, {"timestamp": 1754.0, "state": "WATCH", "drivers": "INFLOW_OUTFLOW_IMBALANCE"}, {"timestamp": 1758.0, "state": "NORMAL", "drivers": ""}]
- **unit:** "source seconds / state"
- **start_timestamp:** 1380
- **end_timestamp:** 1800
- **aggregation_window:** "[1380,1800)"
- **aggregation_type:** "event_sequence"
- **eligible_population:** "Frozen state rows including hysteresis"
- **numerator:** "not applicable"
- **denominator:** "not applicable"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/warning_timeline.parquet", "sha256": "0e4a566361eb957ccf815bda9869ab3d6751c46fef3d0692da4a120925b5e7fa"}, {"path": "outputs/p05_traffic_operations_early_warning/data/warning_summary.json", "sha256": "8d6eddba9b052f89ff9c6cec7946692b8916b51a636547feb19533d45131ad06"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "NORMAL23:00 → WATCH23:03 → WARNING24:00 → NORMAL28:57 → WATCH29:14 → NORMAL29:18."

### static_tracks

- **metric_id:** "static_tracks"
- **metric_name:** "Ten-minute trajectory visual scope"
- **exact_value:** 64
- **unit:** "eligible track IDs observed"
- **start_timestamp:** 1200
- **end_timestamp:** 1800
- **aggregation_window:** "[1200,1800) continuous10-minute interval"
- **aggregation_type:** "interval_aggregate"
- **eligible_population:** "Observed vehicle tracks already confirmed at the observation (>=3 hits), ultimately confirmed, ROI-eligible, excluding entire tracks with movement>0.15 image diagonals/s. Missing/lost predictions are not occupancy observations."
- **numerator:** 64
- **denominator:** "not applicable"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/tracks.parquet", "sha256": "fae06e6e0f4c99eab957490c3d47c6f2c340cd05c6756a5d85ff0f371e42d6eb"}, {"path": "outputs/p05_traffic_operations_early_warning/data/trajectories.parquet", "sha256": "d4648a041865d075fe0904bf9ae43cac237af244ccbc3078c477e98664c32671"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "64 eligible confirmed track IDs observed in20:00–30:00; not178 full-source confirmed tracks."

### sensitivity

- **metric_id:** "sensitivity"
- **metric_name:** "Configured sensitivity warning range"
- **exact_value:** [1430.0, 1447.0]
- **unit:** "source seconds"
- **start_timestamp:** 1380
- **end_timestamp:** 1800
- **aggregation_window:** "Frozen configured sensitivity variants"
- **aggregation_type:** "configuration_sensitivity"
- **eligible_population:** "Preserved variant outputs,not independently sampled episodes"
- **numerator:** "min/max onset"
- **denominator:** "number of variants,not trial count"
- **baseline_comparator:** null
- **percentage_change_formula:** null
- **evidence_source:** [{"path": "outputs/p05_traffic_operations_early_warning/data/sensitivity_results.parquet", "sha256": "08559d8a19a07e6868ddf6ef6df28006778be07acb15a239ae2e53416db2100a"}]
- **claim_status:** "VERIFIED_PRESENTATION_ONLY_NOT_PUBLICATION_APPROVED"
- **classification:** "PRESENTATION_DERIVED"
- **allowed_presentation_wording:** "Warning onset1430–1447s across frozen variants; not a confidence interval."
