SELECT *, 'observed_association' AS relationship FROM metric_rollup WHERE level='day_of_week' ORDER BY dimension, model_name
