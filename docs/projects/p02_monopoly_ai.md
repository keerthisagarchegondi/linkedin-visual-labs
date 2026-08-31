# Project 3 - Monopoly AI Landlord Arena

## Status

**Complete.**

Project 3 asks:

> Which simplified property-investment strategy wins most often over 10,000 simulated games?

The project is a deterministic analytical simulation rather than reinforcement learning and does not reproduce official Monopoly artwork or branding.

## Strategies

- **Collector** - acquires broadly and maximizes optionality.
- **Specialist** - concentrates on completing property groups.
- **Cash Protector** - prioritizes liquidity and selective investment.
- **Aggressive Builder** - develops controlled assets quickly.

## Tournament

- Games: **10,000**
- Strategy-game outcomes: **40,000**
- Master seed: **73031**
- Seats per strategy per seat position: **2,500**
- Simulation: deterministic under the frozen contract

## Final result

| Strategy | Win rate | Bankruptcy rate | Median finishing cash |
| --- | ---: | ---: | ---: |
| Collector | 37.72% | 40.26% | $1,540 |
| Aggressive Builder | 31.28% | 49.19% | $264.50 |
| Cash Protector | 16.81% | 52.42% | $0 |
| Specialist | 14.19% | 53.53% | $0 |

**Collector won most often.**

Statistical validation includes 95% Wilson confidence intervals and pairwise tests with Holm multiple-comparison correction.

## Representative game

The cinematic narrative is grounded in representative game 8721 and its semantic event stream.

The selected narrative sequence includes:

1. Specialist acquires Gold Avenue.
2. Collector expands to Skyline Tower.
3. Collector builds on Skyline Drive.
4. Collector receives rent on Emerald Avenue.
5. Cash Protector experiences a liquidity shock.
6. Cash Protector reaches rent-driven bankruptcy.

The representative game winner is Specialist. The representative game was selected for narrative usefulness rather than because its winner matched the tournament leader.

## Video

Accepted artifact:

`project3_property_trading_cinematic_v3_60s.mp4`

Media contract:

- Resolution: 1080 x 1080
- Duration: 60 seconds
- Frame rate: 30 FPS
- Frame count: 1,800
- Codec: H.264
- Pixel format: yuv420p

Accepted artifact SHA256:

`d018a85a1eda8cd31dfdb2e4e44c1ae349dc770b9b0c5318a51906c355a05501`

The accepted post-production renderer is preserved at:

`src/linkedin_visual_labs/projects/p02_monopoly_ai/cinematic_v3_renderer.py`

Its source provenance is recorded in:

`assets/p02_monopoly_ai/cinematic_v3_provenance.json`

Generated video files, temporary frames, FFmpeg binaries, local fonts, virtual environments, and Codex scratch work are not stored in Git.

## Technical architecture

The completed project contains:

- deterministic game engine
- rule-based strategy agents
- reproducible random streams
- 10,000-game tournament runner
- balanced-seat fairness checks
- statistical validation
- semantic event replay
- cinematic storyboard and motion infrastructure
- direct Pillow-based cinematic renderer
- FFmpeg H.264 export
- renderer and artifact provenance
- automated unit and integration tests

## Quality gates

At Project 3 Step 8 closeout:

- Ruff lint: PASS
- Ruff format: PASS
- mypy `src tests`: PASS
- pytest: **633 passed**
- cinematic provenance test: PASS
- local `main` equals `origin/main`

Project 3 Step 9 adds the final documentation and completion contract but does not change simulation or rendering behavior.

## Limitations

- The game rules are intentionally simplified.
- Strategies are deterministic rule-based agents, not reinforcement learning agents.
- Results describe this simulation contract and should not be interpreted as universal property-investment advice.
- Representative-game storytelling is illustrative and does not replace aggregate tournament statistics.
- The cinematic renderer is preserved as post-production provenance and is intentionally exempted from strict mypy error enforcement.

## Reproduction

Core analytical commands:

```text
python -m linkedin_visual_labs monopoly contract
python -m linkedin_visual_labs monopoly tournament
```

Authoritative repository gates:

```text
python -m ruff check src tests
python -m ruff format src tests --check
mypy src tests
pytest -q
git diff --check
```

## Disclaimer

Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro.
