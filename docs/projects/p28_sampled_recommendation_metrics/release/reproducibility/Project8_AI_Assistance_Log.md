# Project 8 — AI Assistance Log

## 1. Purpose

This log documents the use of generative AI assistance during the development,
validation, documentation, and manuscript-preparation workflow for Project 8:

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

The purpose is transparency. The log distinguishes AI-assisted work from the
scientific results and records the boundaries applied to AI-generated material.

## 2. AI system used

- Provider: OpenAI
- Product: ChatGPT
- Role: drafting, coding/orchestration guidance, documentation support,
  consistency checking, and publication-preparation assistance

This log does not claim that the AI system independently verified or certified
the scientific validity of the study.

## 3. AI-assisted activities

### 3.1 Project planning and workflow structuring

AI assistance was used to:

- organize Project 8 into numbered steps and sub-steps;
- define validation gates and stop conditions;
- structure the repository workflow;
- maintain continuity between scientific, visual, and manuscript stages; and
- generate copy-paste PowerShell/Python orchestration instructions.

The scientific assumptions used in the project were kept under the frozen
Project 8 contract rather than being generated ad hoc during manuscript writing.

### 3.2 Coding and implementation guidance

AI assistance was used to help draft and troubleshoot code or command sequences
for:

- repository checks;
- deterministic validation;
- analytical metric calculations;
- Monte Carlo validation orchestration;
- artifact freezing;
- figure/dashboard generation workflows;
- manuscript-state tracking; and
- Git staging/commit workflows.

Generated code was executed in the project environment and was subject to
Project 8 tests and validation gates.

### 3.3 Debugging and validator repair

AI assistance was used to diagnose and repair documentation-validator issues,
including:

- Markdown blockquote normalization;
- Markdown-versus-LaTeX inline-math normalization;
- LaTeX numeric-format normalization; and
- semantic-marker alignment where manuscript wording and validator wording were
  equivalent in meaning but differed literally.

These repairs were intended to improve validation robustness without changing
the frozen scientific results.

### 3.4 Scientific writing and manuscript drafting

AI assistance was used to draft and refine manuscript sections covering:

- abstract;
- source example and study scope;
- mathematical methods;
- independent implementation;
- full-catalog results;
- sampled-evaluation results;
- sample-size sensitivity analysis;
- Monte Carlo validation;
- source reconciliation;
- discussion;
- limitations;
- reproducibility;
- contribution statement;
- AI-assistance disclosure; and
- data/code availability language.

AI-generated prose was constrained to the validated Project 8 results and
explicit interpretation boundaries.

### 3.5 Formatting and artifact generation

AI assistance was used to prepare or regenerate:

- manuscript Markdown;
- manuscript DOCX;
- manuscript PDF;
- reproducibility appendix;
- BibTeX bibliography file;
- AI-assistance log;
- LinkedIn-oriented communication material; and
- Project 8 video/visual communication artifacts.

Displayed metric/result values in manuscript-facing files were standardized to
four decimal places after the manuscript was approved. Counts, seeds, formulas,
sample-size grid values, crossover intervals, and numerical tolerances remained
exact where appropriate.

### 3.6 Reference support

AI assistance was used to help identify and verify the primary source used for
the source-reported toy example:

Krichene, W., and Rendle, S. (2020). *On Sampled Metrics for Item
Recommendation*. Proceedings of the 26th ACM SIGKDD International Conference on
Knowledge Discovery & Data Mining, 1748–1757.
DOI: `10.1145/3394486.3403226`.

A BibTeX file was then generated from the verified bibliographic information.

## 4. Activities not delegated to AI as scientific authority

The AI system was not treated as the scientific authority for:

- the frozen A/B/C rank profiles;
- full-catalog metric values;
- sampled analytical expectations;
- the sample-size sweep;
- crossover intervals;
- Monte Carlo acceptance results;
- AUC invariance under the frozen protocol;
- source-value reconciliation;
- interpretation of numerical ties; or
- final publication claims.

Those items were governed by the Project 8 computational artifacts,
mathematical definitions, validation results, and frozen claim register.

## 5. Scientific result provenance

The central scientific result is based on the frozen Project 8 analysis:

- full-catalog AP ordering: `C > B > A`;
- expected sampled AP ordering at `m = 99`: `A > B > C`;
- rank profiles unchanged between evaluations;
- AUC ordering across the tested grid: `A > C > B`.

Displayed manuscript values are rounded to four decimal places, but ordering,
tie, and validation decisions use the underlying unrounded values.

The AI system did not create alternative scientific values when drafting the
manuscript.

## 6. Validation safeguards applied to AI-assisted work

The workflow used the following safeguards:

1. scientific configuration was frozen before manuscript drafting;
2. analytical values were separated from Monte Carlo estimates;
3. source-reported rounded values were used only for reconciliation;
4. full-precision values controlled ordering and tie decisions;
5. exact crossover interpolation was prohibited;
6. universal sampled-metric claims were prohibited;
7. whole-paper reproduction claims were prohibited;
8. publication and DOI claims were prohibited until independently established;
9. frozen artifacts were checked for immutability during validated steps; and
10. Project 8 regression tests were rerun during the manuscript workflow.

During the completed validated manuscript-building stages, the Project 8 test
suite reported:

`169 passed`

## 7. Human responsibility

The author remains responsible for:

- the research question;
- selection and interpretation of the source example;
- acceptance of the experimental design;
- execution of repository code;
- review of validation outputs;
- approval of manuscript wording;
- verification of references;
- approval of figures and communication artifacts;
- final publication decisions; and
- compliance with journal, conference, archive, employer, and immigration
  requirements.

AI assistance does not transfer authorship responsibility or scientific
accountability.

## 8. Disclosure language for the manuscript

A concise disclosure suitable for the manuscript is:

> Generative AI tools were used to assist with manuscript drafting, wording
> refinement, coding/orchestration guidance, and documentation structure. The
> numerical results, formulas, validation conditions, and scientific claims were
> constrained to the project's frozen analytical artifacts and validation
> contract. The author reviewed and approved the final content and remains
> responsible for the study design, source verification, interpretation, and
> publication submission.

## 9. Disclosure boundaries

This log does not state or imply that:

- AI generated or discovered the central scientific phenomenon;
- AI independently reproduced the source paper;
- AI certified the numerical results;
- AI performed peer review;
- AI is an author;
- the manuscript has been accepted or published; or
- a DOI has been assigned to Project 8.

## 10. Step 9.18 status

- Step: `Project 8 — Step 9 — Sub-step 9.18`
- Artifact: `Project8_AI_Assistance_Log`
- Status: `GENERATED`
- Scientific values changed: `NO`
- Manuscript claims expanded: `NO`
- Publication status changed: `NO`
- DOI status changed: `NO`
