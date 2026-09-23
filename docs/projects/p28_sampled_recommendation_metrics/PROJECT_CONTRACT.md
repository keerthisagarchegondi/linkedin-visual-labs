# Project 8 — Project Contract

## Scientific question

For fixed recommender ranking profiles, can evaluation against sampled
irrelevant items change metric-based ordering relative to full-catalog
evaluation?

## Frozen source-defined input

- `N = 10,000`
- five evaluation instances per profile
- one relevant item per instance
- reference sampled comparison uses `m = 99` negative draws
- sampling is uniform with replacement

Profiles:

- A: `[100, 100, 100, 100, 100]`
- B: `[40, 40, 8437, 9266, 4482]`
- C: `[212, 2, 743, 5342, 1548]`

## Scope boundary

This is a selected-result independent replication, not a complete
replication of the original KDD study.

The project does not establish a new discovery, train recommenders, or
claim real-world business impact.
