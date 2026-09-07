-- One expected row per method/store/category/date, including invalid candidate evidence.
SELECT *,
    CASE WHEN valid THEN forecast_units - actual_units END AS signed_error,
    CASE WHEN valid THEN abs(forecast_units - actual_units) END AS absolute_error,
    CASE WHEN valid THEN greatest(actual_units - forecast_units, 0) END AS shortfall_units,
    CASE WHEN valid THEN greatest(forecast_units - actual_units, 0) END AS excess_units
FROM normalized_predictions
ORDER BY model_name, store_id, category, date
