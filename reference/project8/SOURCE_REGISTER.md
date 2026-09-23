# Project 8 — Source Register

## S1 — Original paper

Walid Krichene and Steffen Rendle.
**On Sampled Metrics for Item Recommendation.**
KDD 2020.
DOI: 10.1145/3394486.3403226

Primary landing page:
https://research.google/pubs/on-sampled-metrics-for-item-recommendation/

## S2 — Selected toy-example source

Walid Krichene and Steffen Rendle.
**On Sampled Metrics for Item Recommendation (Extended Abstract).**
IJCAI 2021, Sister Conferences Best Papers Track, pp. 4784–4788.
DOI: 10.24963/ijcai.2021/651

Primary PDF:
https://www.ijcai.org/proceedings/2021/0651.pdf

Visually verified Tables 1–2 study inputs:

- A: [100, 100, 100, 100, 100]
- B: [40, 40, 8437, 9266, 4482]
- C: [212, 2, 743, 5342, 1548]
- N = 10,000
- m = 99 reference negative draws
- five evaluation instances per profile
- one relevant item per instance
- uniform negative sampling with replacement
- sampled rank = 1 + Binomial(m, (r-1)/(N-1))

The published sampled values are stochastic reference evidence.
They are never used as answers by the Project 8 result generator.

## Scope boundary

Project 8 reproduces a selected published toy example through an independent
implementation of the documented mathematics.

It is not:
- a replication of the full KDD experimental program;
- observed retail/customer data;
- trained recommender models;
- evidence of business uplift.
