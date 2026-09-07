-- Components and their configured weights are supplied as audited tables.
SELECT *, row_number() OVER (ORDER BY priority_score DESC, store_id, category, model_name) AS priority_rank
FROM (
 SELECT c.*, w.volume*c.volume_component + w.shortfall*c.shortfall_component
   + w.absolute_error*c.absolute_error_component + w.bias_exposure*c.bias_component
   + w.disagreement_exposure*c.disagreement_component
   + w.repeated_miss_exposure*c.repeat_component AS priority_score
 FROM exception_components c CROSS JOIN exception_weights w
) ORDER BY priority_rank
