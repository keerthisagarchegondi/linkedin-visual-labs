SELECT a.*, b.dimension AS comparison_group, b.observations AS comparison_observations,
 b.wape AS comparison_wape, a.wape-b.wape AS wape_difference,
 a.bias-b.bias AS bias_difference, 'observed_association' AS relationship
FROM metric_rollup a JOIN metric_rollup b ON a.model_name=b.model_name AND a.level=b.level
 AND a.dimension<>b.dimension
WHERE a.level='event' ORDER BY a.dimension, a.model_name
