# Project 5 aggregation SQL

`aggregate_demand.sql` groups the CSV-backed `raw_sales` view while demand is still wide. Python substitutes only day-sum expressions constructed from validated consecutive `d_N` identifiers. The result must have exactly 20 rows before DuckDB unpivots it and joins the validated calendar.

No item-by-day long table is constructed. Source identifiers are checked separately; missing, negative, fractional, and nonnumeric selected demand are rejected. The query runs with configured threads, memory limit, and repository-local spill storage. A resource failure must stop preparation, never shorten history or drop stores. Diagnostic SQL belongs to later steps and is not implemented here.


Step 4 adds prediction_errors.sql and metric_rollup.sql as the error and pooled-metric relations; required scorecard/association/ranking/exception files are executed against those relations. champion_counts.sql independently reconciles Python selection; champion_map.sql is a dataset without rendering. Every table has stable ordering. See docs/projects/p25_quick_commerce_control_tower/evaluation_and_governance.md for exact formulas, coverage rules, fixed ranking weights, and SQL/Python tolerances.
