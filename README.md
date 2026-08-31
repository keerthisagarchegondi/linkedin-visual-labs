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

## Foundation commands

```bash
python -m linkedin_visual_labs doctor
python -m linkedin_visual_labs version

ruff format .
ruff check .
mypy src tests
pytest

<!-- P01_BAYESIAN_DICE_START -->

## Project 1 — Bayesian Dice Detective

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

The final visualization is a deterministic 1080×1080, 30 fps, approximately
45-second H.264 video with six synchronized analytical panels.

See [Project 1 — Bayesian Dice Detective](docs/projects/p01_bayesian_dice.md)
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
