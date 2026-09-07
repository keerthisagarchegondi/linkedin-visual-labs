-- Only regex-validated d_N identifiers supply {day_sums}.
-- raw_sales is a CSV-backed view; materialize 20 aggregate rows, never item x day rows.
CREATE TEMP TABLE wide_aggregate AS
SELECT store_id, state_id, cat_id AS category,
       {day_sums}
FROM raw_sales
WHERE cat_id IN ('FOODS', 'HOUSEHOLD')
GROUP BY store_id, state_id, cat_id;
