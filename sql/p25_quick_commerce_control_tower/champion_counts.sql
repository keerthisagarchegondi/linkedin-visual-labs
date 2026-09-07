-- Independent SQL eligibility ordering reconciliation with Python selection.
WITH ranked AS (
 SELECT *, row_number() OVER (PARTITION BY store_id, category ORDER BY wape, tie_rank) AS choice
 FROM candidate_eligibility WHERE eligible
)
SELECT model_name, count(*) AS champion_count FROM ranked WHERE choice=1
GROUP BY model_name ORDER BY model_name
