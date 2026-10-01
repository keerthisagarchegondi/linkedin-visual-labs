# LinkedIn Visual Labs

`linkedin_visual_labs` is a collection of visual machine-learning, simulation,
optimization, NLP, audio, computer-vision, and decision-science experiments.

The repository is designed to produce entertaining, technically defensible
LinkedIn content while maintaining reusable software-engineering foundations.

## Repository identity

- Repository: `linkedin-visual-labs`
- Python package: `linkedin_visual_labs`
- Primary execution style: `python -m linkedin_visual_labs ...`
- Primary development environment: GitHub Codespaces
- Python version: 3.13

## Remote development

The project is developed inside a repository-scoped GitHub Codespace.

The development stack is:

1. GitHub-hosted virtual machine
2. Linux development container
3. Repository workspace under `/workspaces/linkedin-visual-labs`
4. Project virtual environment under `.venv`
5. GitHub Actions for independent quality verification


## Installation and optional deep learning

Base installation is `python -m pip install -e .`; shared developer tools use
`python -m pip install -e ".[dev]"`. Neither installs PyTorch.
The default Codespaces setup uses the same lightweight dev extra.

Only Zombie Escape (`p04_zombie_escape`, Project 2) uses PyTorch, in
`dl_model.py` and `dl_tensors.py`; its DL pipeline and DL tests depend on them.
Bayesian Dice, Monopoly and Project 5 do not require PyTorch.
To run all tests or the full strict type check, install the Zombie extra.
For the project's deterministic CPU training and CI:

```bash
python -m pip install "torch>=2.6" --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[dev,zombie-dl]"
mypy --strict src tests
pytest
```

The CPU index follows [PyTorch's installation instructions](https://docs.pytorch.org/get-started/locally/).
Installing `.[zombie-dl]` directly also provides PyTorch, but the default Linux
distribution may include CUDA dependencies; the two-command CPU path avoids them.
The generic CI job runs all non-Zombie tests with `.[dev]`; the dedicated
`zombie-dl` CI job runs every Zombie test and full-repository strict mypy with
CPU PyTorch. No tests are skipped overall. Bayesian Dice stays on `.[dev]`,
with its full formatting, lint, tests and deterministic schedule checks.
Full strict typing is centralized in the dedicated CI job.
Ignored Monopoly production artifacts remain a separate runtime prerequisite.

## Foundation commands

```bash
python -m linkedin_visual_labs doctor
python -m linkedin_visual_labs version

ruff format .
ruff check .
mypy src tests
pytest

<!-- P01_BAYESIAN_DICE_START -->

## Project 1 â€” Bayesian Dice Detective

**Question:** How many rolls before knowing whether a pair of dice is loaded?

Project 1 runs six deterministic pair-of-dice Bayesian experiments:

- Unloaded - Unloaded
- Unloaded - Partially Loaded
- Unloaded - Fully Loaded
- Partially Loaded - Partially Loaded
- Partially Loaded - Fully Loaded
- Fully Loaded - Fully Loaded

Inference observes only the pair sum and updates six exact Bayesian models
sequentially. The headline metric is the **Stable Roll**: the earliest roll
after which the final FAIR or LOADED decision never changes again.

The canonical experiment contains 10,000 rolls per case and 60,000 observed
pair sums in total.

The final visualization is a deterministic 1080Ã—1080, 30 fps, approximately
45-second H.264 video with six synchronized analytical panels.

See [Project 1 â€” Bayesian Dice Detective](docs/projects/p01_bayesian_dice.md)
for the complete experiment, validation, and reproduction contract.

<!-- P01_BAYESIAN_DICE_END -->

<!-- P02_MONOPOLY_AI_STATUS_START -->
### Project 3 - Monopoly AI Landlord Arena

**Status: Complete**

Four deterministic rule-based investment strategies competed across **10,000 simulated games / 40,000 strategy-game outcomes**.

**Collector won most often with a 37.72% win rate.**

The project includes deterministic simulation, strategy agents, balanced-seat tournament design, Wilson confidence intervals, pairwise statistical validation, semantic event replay, and a 60-second cinematic data-storytelling pipeline.

Project documentation: `docs/projects/p02_monopoly_ai.md`

<!-- P02_MONOPOLY_AI_STATUS_END -->

<!-- PROJECT8_PUBLIC_START -->

## Project 8 — Sampled Recommendation Metrics

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

Project 8 examines a controlled recommendation-evaluation example in
which full-catalog and sampled Average Precision can produce different
model orderings even though the underlying model rank profiles remain
unchanged.

**Public research artifacts**

- Zenodo DOI: [10.5281/zenodo.23058261](https://doi.org/10.5281/zenodo.23058261)
- Zenodo archive: https://zenodo.org/records/23058261
- GitHub release: https://github.com/keerthisagarchegondi/linkedin-visual-labs/releases/tag/v1.0.0
- Source: `src/linkedin_visual_labs/projects/p28_sampled_recommendation_metrics/`
- Documentation: `docs/projects/p28_sampled_recommendation_metrics/`
- Interactive dashboard: `assets/p28_sampled_recommendation_metrics/dashboard/index.html`
- Manuscript: `docs/projects/p28_sampled_recommendation_metrics/release/manuscript/Project8_Final_Manuscript_Release_Candidate.pdf`

The public GitHub release and Zenodo deposit are research artifacts.
They do not by themselves imply journal or conference peer review,
acceptance, or publication.

<!-- PROJECT8_PUBLIC_END -->
