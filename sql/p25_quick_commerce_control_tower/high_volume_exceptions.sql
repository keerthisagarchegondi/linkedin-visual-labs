-- Unit misses, not noisy small-denominator percentages, define materiality.
SELECT e.*, e.actual_units AS demand_volume, c.champion_model, c.eligibility_status,
 e.model_name=c.champion_model AS is_champion,
 row_number() OVER (ORDER BY e.absolute_error DESC, e.actual_units DESC,
 e.store_id, e.category, e.date, e.model_name) AS materiality_rank
FROM prediction_errors e LEFT JOIN champions c USING (store_id, category)
WHERE e.valid AND e.absolute_error>0 ORDER BY materiality_rank
