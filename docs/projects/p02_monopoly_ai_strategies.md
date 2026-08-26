# Project 3 — Strategy Contract

## Purpose

Project 3 compares four autonomous rule-based strategy agents under the
same deterministic simplified property-investment game engine.

These are not reinforcement-learning agents.

The strategy layer expresses intent.

The game engine owns legality and state mutation.

---

## Collector

**Philosophy:** Own broadly and keep capital working.

- Desired cash reserve: $150
- Development reserve: $200
- Buys broadly
- No preferred color groups
- Buys transit
- Buys utilities
- Moderate monopoly-completion preference
- Maximum one build per development phase

**Hypothesis under test:**

Can diversified asset accumulation outperform concentrated or highly
defensive capital allocation?

---

## Specialist

**Philosophy:** Concentrate capital in selected strategic groups.

- Desired cash reserve: $350
- Development reserve: $400
- Primary groups: Amber / Crimson / Gold
- Secondary groups: Cedar / Emerald
- Strong monopoly-completion priority
- Selective elsewhere
- Maximum two builds per development phase

**Hypothesis under test:**

Can focused capital allocation and group synergy outperform broad
acquisition?

---

## Cash Protector

**Philosophy:** Bankruptcy has a zero-percent return.

- Desired cash reserve: $600
- Development reserve: $750
- High purchase selectivity
- Cautious development
- High liquidity preference
- Maximum one build per development phase

**Hypothesis under test:**

Does preserving liquidity and reducing bankruptcy risk improve long-run
tournament performance?

---

## Aggressive Builder

**Philosophy:** Deploy capital rapidly when development becomes possible.

- Desired cash reserve: $75
- Development reserve: $75
- Extreme monopoly-completion priority
- Rapid house deployment
- Accepts high liquidity risk
- Maximum four builds per development phase

**Hypothesis under test:**

Can aggressive reinvestment generate enough rent upside to compensate
for increased bankruptcy exposure?

---

## Legal actions

Purchase phase:

- BUY
- PASS

Development phase:

- BUILD
- HOLD_CASH

Every decision contains an action and reason code.

Policies receive read-only context.

Policies cannot mutate game state.

---

## Evaluation

Primary:

- tournament win rate

Risk:

- bankruptcy rate

Resilience:

- median finishing cash

Behavior diagnostics:

- assets acquired
- groups completed
- houses built
- rent collected / paid
- minimum cash
- reserve breaches

---

## Fairness principle

Every strategy plays all 10,000 canonical games and occupies each seat
exactly 2,500 times.

The tournament does not alter game rules by strategy.

No strategy receives special pricing, rent, movement, development, or
bankruptcy privileges.
