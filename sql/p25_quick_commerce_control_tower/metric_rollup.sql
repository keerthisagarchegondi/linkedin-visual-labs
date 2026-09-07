-- Expand common error evidence to explicitly named evaluation levels.
WITH expanded AS (
    SELECT 'network' AS level, 'ALL' AS dimension, * FROM prediction_errors
    UNION ALL SELECT 'store', store_id, * FROM prediction_errors
    UNION ALL SELECT 'category', category, * FROM prediction_errors
    UNION ALL SELECT 'store_category', store_id || '/' || category, * FROM prediction_errors
    UNION ALL SELECT 'day_of_week', weekday, * FROM prediction_errors
    UNION ALL SELECT 'event', event_status, * FROM prediction_errors
    UNION ALL SELECT 'snap', snap_status, * FROM prediction_errors
    UNION ALL SELECT 'horizon', cast(horizon AS VARCHAR), * FROM prediction_errors
), pooled AS (
    SELECT g.level, g.dimension, g.model_name,
        count(e.date) AS expected_observations,
        count(*) FILTER (WHERE e.valid) AS observations,
        coalesce(sum(e.actual_units), 0) AS demand_volume,
        coalesce(sum(e.actual_units) FILTER (WHERE e.valid), 0) AS actual_units,
        coalesce(sum(e.forecast_units) FILTER (WHERE e.valid), 0) AS forecast_units,
        coalesce(sum(e.absolute_error), 0) AS absolute_error,
        coalesce(sum(e.signed_error), 0) AS signed_error,
        coalesce(sum(e.shortfall_units), 0) AS shortfall_units,
        coalesce(sum(e.excess_units), 0) AS excess_units,
        count(*) FILTER (WHERE e.valid AND e.signed_error < 0) AS under_count,
        count(*) FILTER (WHERE e.valid AND e.signed_error > 0) AS over_count,
        count(*) FILTER (WHERE e.raw_finite) AS finite_raw_count,
        count(*) FILTER (WHERE e.raw_finite AND e.raw_forecast_units < 0) AS clipping_count
    FROM scorecard_grid g LEFT JOIN expanded e
        ON g.level=e.level AND g.dimension=e.dimension AND g.model_name=e.model_name
    GROUP BY g.level, g.dimension, g.model_name
)
SELECT *,
    absolute_error / nullif(actual_units, 0) AS wape,
    absolute_error / nullif(observations, 0) AS mae,
    signed_error / nullif(actual_units, 0) AS bias,
    under_count / nullif(observations, 0) AS underforecast_rate,
    over_count / nullif(observations, 0) AS overforecast_rate,
    observations / nullif(expected_observations, 0) AS completeness,
    clipping_count / nullif(finite_raw_count, 0) AS clipping_rate,
    CASE WHEN observations=0 THEN 'undefined_empty'
         WHEN actual_units=0 THEN 'undefined_zero_demand'
         WHEN observations<expected_observations THEN 'partial_coverage' ELSE 'defined' END AS metric_status
FROM pooled ORDER BY level, dimension, model_name
