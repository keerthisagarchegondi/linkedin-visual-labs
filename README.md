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