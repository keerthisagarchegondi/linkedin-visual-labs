# Literature, Overlap, and Venue Screen

## Overlap matrix

| Prior work | Source / identifier | Establishes | Project 9 replication target | Controlled extension | Remaining uncertainty |
|---|---|---|---|---|---|
| Kim et al. | AAAI 2022; DOI 10.1609/aaai.v36i7.20680 | PA can overestimate performance; random scores can yield high PA F1 | PA mechanism and random-score behavior | Fixed-prevalence, fixed-q/event-cardinality finite-sample audit | Printed analytical equation ambiguity |
| TADPAK | github.com/tuslkkk/tadpak | Authors' PA%K reference implementation | Protocol interpretation only | Independent implementation; no copied code | License not verified from public page |
| Outliar | github.com/UsmarHaider/outliar | Public benchmark audit of random/untrained controls under PA | Confirms overlap is substantial | Synthetic, predeclared equal-event finite-sample audit, not a detector benchmark | Repository claims are not independently reproduced here |
| PATE | arXiv:2405.12096; KDD 2024 | Proximity-aware metric; reports PA F1 can fail to characterize performance | Context only | No new replacement metric proposed | Broader metric literature is not exhaustive |

Searches also located later PA-related work, including PAdf and *Towards Unbiased Evaluation of Time-series Anomaly Detector*. Search non-findings are not novelty evidence.

## Contribution boundary

The responsible framing is an independent partial replication and controlled methodological note. It must not claim novelty for PA inflation, random-score inflation, or a new evaluation metric. The value proposition is transparent finite-sample measurement: paired identical alerts, predeclared conditions, expected-count references distinguished from expected F1, and reproducible presentation.

## Venue screen

**ReScience C:** Strong topical fit only if the work substantiates a replication of the original result with original open source and evidence; it accepts negative results, requires accessible reproducible materials, and publishes CC BY. Its FAQ warns that an already replicated original may make a further replication unlikely. No fees are reported.

**TMLR:** Scope explicitly includes reproducibility studies and studies of method strengths/weaknesses. Acceptance requires evidence-supported claims and audience interest. It is open review, double blind, has no fees, permits arXiv overlap, and says LLMs are not authors while human authors remain responsible. Suitability is plausible but materially uncertain because the controlled extension may be judged insufficient.

**arXiv:** Likely categories are `cs.LG`, with possible `cs.AI` and `stat.ME`, matching the source paper. It is an appropriate possible preprint route, subject to current submission/account/endorsement/moderation rules at submission time. Do not infer endorsement need, AI disclosure wording, source-format acceptance, or author eligibility from this screen; recheck official live guidance before any submission.

**ORCID / metadata:** ORCID supports persistent work identifiers and links authenticated iDs into publisher/repository metadata workflows. It is optional preparation, not evidence of publication.

## Decision

`publication_scope_status = EDITORIAL_SCOPE_CHECK_NEEDED`. Implementation and a portfolio/reproducibility artifact are scientifically responsible; candidate journal submission needs a later editor-facing scope assessment after results and claim audit.
