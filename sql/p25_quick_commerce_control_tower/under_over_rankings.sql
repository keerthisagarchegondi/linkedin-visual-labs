SELECT *,
 row_number() OVER (ORDER BY shortfall_units DESC, dimension, model_name) AS under_rank,
 row_number() OVER (ORDER BY excess_units DESC, dimension, model_name) AS over_rank,
 row_number() OVER (ORDER BY abs(bias) DESC NULLS LAST, dimension, model_name) AS bias_rank,
 CASE WHEN observations>=(SELECT minimum_subgroup_observations FROM diagnostics_settings) THEN row_number() OVER
   (ORDER BY CASE WHEN observations>=(SELECT minimum_subgroup_observations FROM diagnostics_settings) THEN wape END DESC NULLS LAST, dimension, model_name)
 END AS wape_rank
FROM store_category_scorecard ORDER BY under_rank
