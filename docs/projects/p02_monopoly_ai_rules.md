# Project 3 — Monopoly AI Landlord Arena

## Simplified Rules Contract — Part 1

**Contract scope:** Project 3 — Step 1 — Sub-steps 1.1 through 1.25.

This document freezes the first part of the simulation contract before
implementation.

---

## 1.1 Project objective and viewer question

### Viewer question

> Four landlord strategies. 10,000 games. Which one survives?

### Analytical question

> When four autonomous landlord strategies repeatedly allocate capital
> under uncertainty, which strategy wins most often—and what risk does
> it take to get there?

The project is an analytical experiment about repeated capital-allocation
decisions under uncertainty.

The board game is the experimental environment, not the analytical
conclusion.

The first implementation compares four autonomous rule-based strategy
agents. It does not use reinforcement learning.

---

## 1.2 Intellectual-property boundary

Required disclaimer:

> Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro.

The implementation must use an original analytical board schematic.

The project must not reproduce:

- Monopoly logos;
- Hasbro board artwork;
- official visual board layouts;
- official card artwork;
- official fonts;
- official player-token artwork.

Original analytical labels, icons, typography, property names, board
geometry, and strategy visualization are required.

The agents must be described technically as:

> Autonomous rule-based strategy agents evaluated through Monte Carlo
> simulation.

They must not be described as reinforcement-learning agents.

---

## 1.3 Simplified board model

The canonical board contains exactly 40 indexed spaces:

0 through 39.

Movement is circular.

Moving beyond space 39 wraps to space 0.

The canonical board contains:

- 22 color-group properties;
- 4 transit assets;
- 2 utility assets;
- 3 Chance event spaces;
- 3 Community event spaces;
- 2 tax spaces;
- GO;
- Jail;
- Free Rest;
- Go To Jail.

The board topology is immutable during a game.

All display names in the canonical board are original analytical names.

---

## 1.4 Board-space taxonomy

Supported space types are:

### GO

Starting location and salary boundary.

### PROPERTY

Purchasable color-group asset.

Properties may:

- have one owner;
- participate in group completion;
- collect rent;
- support houses.

### TRANSIT

Purchasable non-color-group asset.

Transit rent depends on how many transit assets the owner controls.

Transit spaces cannot receive houses.

### UTILITY

Purchasable non-color-group asset.

Utility rent depends on the landing dice roll and utility ownership count.

Utility spaces cannot receive houses.

### CHANCE

Draws the next deterministic seeded Chance event.

### COMMUNITY

Draws the next deterministic seeded Community event.

### TAX

Transfers a fixed cash amount from player to bank.

### JAIL

A normal board location unless the player has been sent to jail.

### FREE_REST

No economic effect.

### GO_TO_JAIL

Immediately moves the player to Jail without collecting GO salary.

---

## 1.5 Property model

A color property has:

- asset ID;
- board index;
- original display name;
- property-group ID;
- purchase price;
- base rent;
- owner;
- house count.

Ownership and houses belong to game state rather than immutable board
definition.

A property may have no more than one owner.

---

## 1.6 Property-group model

The canonical simulation contains eight property groups:

| Group | Label | Properties | House cost |
|---|---|---:|---:|
| G1 | Harbor | 2 | $50 |
| G2 | Copper | 3 | $70 |
| G3 | Cedar | 3 | $90 |
| G4 | Amber | 3 | $110 |
| G5 | Crimson | 3 | $130 |
| G6 | Gold | 3 | $150 |
| G7 | Emerald | 3 | $175 |
| G8 | Skyline | 2 | $200 |

Total color properties:

22.

The names and price structure are original to this analytical
simulation.

---

## 1.7 Player-state model

Each player state must contain at least:

- unique player ID;
- strategy ID;
- seat index;
- current cash;
- board position;
- owned assets;
- jail-turn state;
- bankruptcy state;
- bankruptcy turn if applicable;
- cumulative rent paid;
- cumulative rent collected;
- minimum observed cash.

Game-state mutation belongs to the engine.

Strategy policies receive read-only decision context and cannot mutate
player or game state directly.

---

## 1.8 Bank and economy model

Every player begins with:

$1,500.

The bank has unlimited liquidity.

This removes bank inventory exhaustion from the experiment so that
strategy behavior remains the primary variable.

Cash enters players through:

- starting cash;
- GO salary;
- positive event effects;
- rent received.

Cash leaves players through:

- asset purchases;
- house construction;
- taxes;
- negative event effects;
- rent paid.

Rent is strictly a player-to-player transfer.

Property purchases, houses, taxes, GO payments, and event cash effects
use the bank as counterparty.

Mortgages are omitted.

Loans are omitted.

Player-to-player trading is omitted.

---

## 1.9 Two-dice movement rules

Every normal movement turn uses exactly two independent six-sided dice.

Possible total:

2 through 12.

Dice are generated from the game's deterministic pseudo-random generator.

The same game seed and same strategy configuration must reproduce the
same dice sequence.

Doubles do not grant another turn.

The three-consecutive-doubles rule is omitted.

These simplifications reduce extra-turn path dependence and make seat
fairness easier to measure.

---

## 1.10 Passing GO

When forward movement crosses from space 39 to space 0, the player
receives:

$200.

Landing directly on GO also receives the same salary when the landing
results from ordinary forward movement.

A player moved directly to Jail does not receive GO salary.

Event-specific movement follows the event contract.

---

## 1.11 Property-purchase rules

The following space types may be purchased:

- PROPERTY;
- TRANSIT;
- UTILITY.

Purchase is possible only when:

1. the asset is currently unowned;
2. the player is active;
3. the player has enough cash to pay the full purchase price;
4. the player's strategy returns BUY;
5. the engine validates the decision.

The purchase price is transferred to the bank.

Ownership is then assigned to the player.

Property auctions are omitted.

A strategy may intentionally PASS even when the player can afford the
asset.

---

## 1.12 Property-ownership rules

One asset may have at most one owner.

An active player may own any number of legal purchasable assets.

Normal player-to-player property transfers are prohibited because
trading is outside the initial project scope.

Ownership can change only through:

- purchase from the bank;
- bankruptcy transfer to a creditor;
- bankruptcy return to the bank.

Mortgage state does not exist.

---

## 1.13 Rent rules

When a player lands on an asset owned by another active player, rent is
transferred from tenant to owner.

### Color property without complete group

Rent equals:

base rent.

### Complete group with zero houses

Rent equals:

2 × base rent.

### Developed property

House multipliers are:

| Houses | Rent multiplier |
|---:|---:|
| 0 | 1× base, or 2× when complete group |
| 1 | 5× base |
| 2 | 12× base |
| 3 | 24× base |
| 4 | 40× base |

Developed-property multipliers replace the unimproved complete-group
multiplier.

### Transit assets

Rent is:

| Transits owned | Rent |
|---:|---:|
| 1 | $25 |
| 2 | $50 |
| 3 | $100 |
| 4 | $200 |

### Utilities

Rent is based on the dice total that caused the landing:

| Utilities owned | Multiplier |
|---:|---:|
| 1 | 4 × dice total |
| 2 | 10 × dice total |

Rent never goes to the bank.

---

## 1.14 Group completion

A color group is complete when one active player owns every property in
that group.

Transit ownership does not count as a color-group monopoly.

Utility ownership does not count as a color-group monopoly.

Only completed color groups are eligible for house development.

---

## 1.15 Simplified house development

The simulation supports houses but not hotels.

Maximum houses per property:

4.

A player may build only when:

- the player owns the complete color group;
- the player is active;
- the player can afford the house;
- the strategy returns BUILD;
- the requested build preserves even development.

### Even-development rule

After a build action, the difference between the highest and lowest
house count within that group cannot exceed one.

This prevents an agent from placing every house on a single property.

Houses may not be placed on:

- transit assets;
- utilities;
- non-purchasable spaces.

---

## 1.16 House costs and rent escalation

House cost is fixed by property group.

House construction transfers cash from the player to the bank.

The group's house cost applies to every property within that group.

Rent escalation uses the common multiplier schedule defined in Section
1.13.

This intentionally simplifies the economic structure while preserving
the central investment trade-off:

> Deploy capital into development now versus retain liquidity for future
> obligations.

---

## 1.17 Cash-reserve semantics

A cash reserve is a strategy preference rather than a game-engine rule.

Example:

A Cash Protector may prefer to keep $500 after a purchase.

The engine does not reject a legal purchase merely because it violates
that strategy's desired reserve.

Instead:

- strategy determines whether it wants to BUY;
- engine determines whether BUY is legal.

This separation is required so strategy behavior remains independently
testable.

---

## 1.18 Jail entry

A player enters Jail through:

- GO_TO_JAIL board space;
- GO_TO_JAIL event.

When sent to Jail:

- position becomes Jail index 10;
- no GO salary is collected;
- jail_turns_remaining becomes 1.

Landing normally on the Jail board space does not create jail state.

---

## 1.19 Jail exit

A jailed player skips exactly one scheduled turn.

After that skipped turn:

- jail state is cleared;
- normal play resumes on the player's following turn.

There is:

- no fine;
- no strategy decision;
- no doubles-release mechanic;
- no jail card.

This keeps jail as a deterministic interruption rather than a fifth
investment policy.

---

## 1.20 Simplified Chance and Community events

Chance and Community are included.

Each deck contains six simplified events.

Deck order is deterministically shuffled once using the game RNG.

Cards are consumed sequentially.

After the final card, the deck cycles back to its beginning.

Supported event actions are:

- move to GO;
- move forward;
- move backward;
- go to Jail;
- receive fixed cash;
- pay fixed cash.

No copyrighted card text or artwork is used.

Event effects are analytical primitives rather than recreations of
official cards.

---

## 1.21 Bankruptcy

A player becomes bankrupt when a mandatory payment exceeds available
cash.

There are:

- no mortgages;
- no emergency asset sales;
- no loans;
- no player negotiation.

Bankruptcy occurs immediately.

A bankrupt player:

- becomes inactive;
- stops receiving normal turns;
- cannot buy assets;
- cannot build;
- cannot collect future normal rent after losing assets.

---

## 1.22 Assets after bankruptcy

### Bankruptcy caused by rent

When the creditor is another player:

- owned assets transfer to the creditor;
- houses remain attached to transferred properties.

### Bankruptcy caused by the bank

For taxes or negative bank events:

- owned assets return to the bank;
- ownership is cleared;
- houses are removed.

This rule is deterministic and requires no auction.

---

## 1.23 Turn sequence

Every active turn follows this order:

1. START_TURN
2. CHECK_JAIL
3. ROLL_DICE
4. MOVE
5. APPLY_PASS_GO
6. RESOLVE_LANDING
7. RESOLVE_REQUIRED_PAYMENT
8. REQUEST_PURCHASE_DECISION_IF_ELIGIBLE
9. APPLY_PURCHASE_DECISION
10. REQUEST_BUILD_DECISIONS
11. APPLY_VALID_BUILD_DECISIONS
12. CHECK_BANKRUPTCY
13. END_TURN

A jailed skipped turn terminates after jail resolution and does not roll
dice.

A bankrupt player receives no turn.

---

## 1.24 Game phases

Canonical game phases are:

### SETUP

Board, players, strategies, event decks, and deterministic RNG are
initialized.

### ACTIVE

Normal gameplay is running.

### TERMINATED_BANKRUPTCY

Only one active player remains.

### TERMINATED_TURN_LIMIT

The maximum game-turn limit is reached before only one player remains.

No other terminal phase exists in the initial implementation.

---

## 1.25 Game turn limit

The canonical maximum is:

500 turns.

A turn means one scheduled player turn, including a skipped jail turn.

The game ends naturally before the limit if only one active player
remains.

If multiple players remain after turn 500, the game transitions to:

TERMINATED_TURN_LIMIT.

The ranking/winner procedure for turn-limit games is intentionally
deferred to Project 3 — Step 1 — Sub-steps 1.27–1.28.

This prevents the winner formula from being implicitly introduced before
its contract is explicitly frozen.

---

## 1.26 Winner determination at natural termination

Natural termination occurs when exactly one active player remains.

That player is the winner.

No terminal-net-worth calculation may override a natural surviving
winner.

The winner receives finishing position 1.

Previously bankrupt players are ranked below all active players according
to the finishing-position rules defined later in this contract.

---

## 1.27 Winner determination at the turn limit

If turn 500 is reached while multiple players remain active, the game
terminates through the turn-limit resolution procedure.

The winner is the active player with the greatest terminal economic net
worth.

Terminal economic net worth is:

> cash + configured purchase value of currently owned assets +
> historical construction cost of houses currently owned.

The asset value is the configured purchase price rather than a
model-generated resale price.

This is intentional.

The simulation does not attempt to estimate a secondary real-estate
market.

Therefore terminal scoring remains transparent and reproducible.

Bankrupt players are not eligible to win a turn-limit game.

---

## 1.28 Deterministic tie-breaking

When active players are tied on terminal net worth, apply the following
ordered comparison:

1. greater terminal net worth;
2. greater cash;
3. greater cumulative rent collected;
4. more complete color groups;
5. more owned purchasable assets;
6. deterministic game-seed-derived tie-break rank.

The following are explicitly prohibited as final tie-breakers:

- seat index;
- alphabetical strategy ordering;
- Python collection iteration order.

The seed-derived final rank prevents systematic seat or strategy-name
advantage.

For bankrupt players, later bankruptcy ranks above earlier bankruptcy.

If an additional deterministic distinction is required, bankruptcy event
index is used before the seeded final tie-break rank.

### Bankruptcy-payment clarification

When a mandatory payment exceeds the player's available cash:

1. all available player cash is transferred toward the obligation;
2. the player's cash becomes zero;
3. any unpaid remainder is forgiven;
4. the player becomes bankrupt;
5. the bankruptcy asset-transfer contract is applied.

This keeps bankruptcy deterministic because mortgages, loans, asset
sales, and negotiation are deliberately omitted.

---

## 1.29 Event-log schema

Every material game transition must be represented in a deterministic
ordered event log.

Every event contains:

- game ID;
- contiguous event index;
- turn number;
- event type;
- player ID when applicable;
- strategy ID when applicable;
- seat index when applicable;
- position before and after when applicable;
- cash before and after when applicable;
- asset ID when applicable;
- counterparty player ID when applicable;
- transfer amount when applicable;
- structured metadata.

Canonical event types are:

- GAME_SETUP;
- TURN_START;
- JAIL_SKIP;
- DICE_ROLL;
- MOVE;
- PASS_GO;
- EVENT_DRAW;
- CASH_TRANSFER;
- PURCHASE_DECISION;
- ASSET_PURCHASED;
- BUILD_DECISION;
- HOUSE_BUILT;
- RENT_DUE;
- BANKRUPTCY;
- ASSET_TRANSFER;
- TURN_END;
- GAME_END.

`event_index` starts at zero and must be contiguous.

The representative-game animation must be derived from this real engine
event log rather than from a separately scripted game narrative.

---

## 1.30 Reproducible game-seed contract

Randomness must never depend on Python's process-randomized `hash()`.

Game seeds are generated using SHA-256.

For tournament game index `i`:

    SHA256(
        "p02-monopoly-ai"
        + ":"
        + master_seed
        + ":"
        + game_index
    )

The first eight digest bytes are interpreted as an unsigned big-endian
integer.

Each game then derives independent labeled streams:

- dice;
- chance;
- community;
- tie_break.

For example:

    SHA256(
        "p02-monopoly-ai"
        + ":"
        + game_seed
        + ":"
        + "dice"
    )

This stream isolation is important.

A future change that adds a Chance draw must not accidentally alter all
later dice rolls.

---

## 1.31 Tournament master-seed contract

Canonical master seed:

    73031

Canonical tournament size:

    10,000 games

Canonical game indices:

    0 through 9,999

Every canonical game seed must be unique.

The same:

    configuration
    + master seed
    + strategy contracts

must reproduce the same tournament.

Changing the master seed must change individual game trajectories.

---

## 1.32 Seat-rotation methodology

The tournament uses an eight-game deterministic seat cycle.

Let:

    C = Collector
    S = Specialist
    P = Cash Protector
    A = Aggressive Builder

The cycle is:

    Game mod 8 = 0: C S P A
    Game mod 8 = 1: S P A C
    Game mod 8 = 2: P A C S
    Game mod 8 = 3: A C S P

    Game mod 8 = 4: C A P S
    Game mod 8 = 5: A P S C
    Game mod 8 = 6: P S C A
    Game mod 8 = 7: S C A P

The first four assignments rotate the forward ordering.

The next four rotate the reverse ordering.

This avoids permanently preserving one circular relative ordering among
strategies.

---

## 1.33 Equal strategy-seat representation

Because:

    10,000 / 8 = 1,250 complete seat cycles

the canonical tournament contains exactly 1,250 complete cycles.

Each strategy therefore plays:

    10,000 total games

and occupies each of the four seats:

    2,500 times

This must be validated automatically before tournament results are
accepted.

No strategy receives a privileged permanent starting seat.

---

## 1.34 Collector policy contract

The Collector follows the philosophy:

> Own broadly and keep capital working.

Configured desired reserve:

    $150

Configured development reserve:

    $200

Collector behavior:

- generally purchases legal affordable properties;
- has no preferred color-group list;
- buys transit assets;
- buys utilities;
- values portfolio breadth;
- receives a moderate bonus for completing a monopoly;
- develops completed groups moderately;
- builds at most one house per development phase.

Collector is intended to test whether broad asset accumulation can beat
greater strategic concentration.

---

## 1.35 Specialist policy contract

The Specialist follows the philosophy:

> Concentrate capital in selected strategic groups.

Configured desired reserve:

    $350

Configured development reserve:

    $400

Primary groups:

    Amber   — G4
    Crimson — G5
    Gold    — G6

Secondary groups:

    Cedar   — G3
    Emerald — G7

Lower-priority groups:

    Harbor  — G1
    Copper  — G2
    Skyline — G8

The Specialist:

- strongly prioritizes preferred-group acquisition;
- places very high value on completing preferred groups;
- purchases non-priority assets more selectively;
- develops completed preferred groups;
- may build at most two houses per development phase.

The purpose is to evaluate concentrated strategic capital allocation
against portfolio breadth.

---

## 1.36 Cash Protector policy contract

The Cash Protector follows the philosophy:

> Bankruptcy has a zero-percent return.

Configured desired reserve:

    $600

Configured development reserve:

    $750

The Cash Protector:

- buys selectively;
- avoids purchases that materially compromise liquidity;
- develops cautiously;
- maintains substantially more cash than the other strategies;
- may build at most one house per development phase.

The policy tests whether survival and liquidity discipline translate into
higher tournament success.

The reserve remains a policy preference, not an engine constraint.

---

## 1.37 Aggressive Builder policy contract

The Aggressive Builder follows the philosophy:

> Deploy capital rapidly once strategic development becomes possible.

Configured desired reserve:

    $75

Configured development reserve:

    $75

The Aggressive Builder:

- strongly prioritizes completing groups;
- accepts low post-decision liquidity;
- builds houses rapidly;
- may build as many as four legal houses during one development phase;
- remains subject to the same affordability and even-development rules
  as every other strategy.

It tests high-upside, high-liquidity-risk capital deployment.

The engine never gives this strategy special economic privileges.

---

## 1.38 Legal strategy actions

The complete initial strategy-action vocabulary is:

    BUY
    PASS
    BUILD
    HOLD_CASH

During an eligible asset-purchase decision:

    BUY
    PASS

are legal.

During a development decision:

    BUILD
    HOLD_CASH

are legal.

Every decision includes:

    action
    reason_code

and may additionally identify an asset/property target.

No strategy may mutate game state directly.

---

## 1.39 Engine-side decision validation

Strategies express intent.

The game engine owns legality.

For BUY, the engine verifies:

- purchase-phase action compatibility;
- target existence;
- target purchasability;
- target is unowned;
- player is active;
- player can afford the price.

For BUILD, the engine verifies:

- development-phase compatibility;
- property existence;
- ownership;
- complete-group ownership;
- active-player state;
- affordability;
- maximum-house limit;
- even-development rule.

Illegal decisions are not silently converted.

The engine must:

1. reject the decision;
2. produce an explicit domain error;
3. log the invalid decision.

This makes policy defects observable during testing.

---

## 1.40 Primary metric — tournament win rate

The headline Project 3 metric is:

    tournament win rate

For strategy `s`:

    wins(s) / completed_games

Every strategy participates exactly once in each canonical game.

Therefore the canonical denominator is:

    10,000

The strategy with the highest properly validated win rate is the
headline tournament winner, subject to later statistical-comparison
rules.

---

## 1.41 Bankruptcy-rate metric

For strategy `s`:

    bankrupt_games(s) / completed_games

Lower bankruptcy rate indicates greater survival resilience.

A strategy may simultaneously have:

    high win rate
    and
    high bankruptcy rate

This is analytically important rather than contradictory.

The video should use bankruptcy rate to reveal the risk required to
produce the strategy's wins.

---

## 1.42 Median-finishing-cash metric

For each strategy, finishing cash is recorded after every completed
game.

A bankrupt player's finishing cash is:

    $0

The headline cash-resilience statistic is:

    median finishing cash

rather than mean finishing cash.

Median is used because extreme high-cash outcomes can heavily skew the
mean.

---

## 1.43 Finishing-position distribution

Every strategy receives one finishing position:

    1
    2
    3
    4

Active players always rank above bankrupt players.

For active players in turn-limit games, the winner/tie-break scoring
rules determine rank.

For bankrupt players:

    later bankruptcy = better finishing position

The tournament records the frequency with which each strategy finishes
first, second, third, and fourth.

---

## 1.44 Property-acquisition metrics

Per strategy and per game record:

- total assets acquired during the game;
- color properties acquired;
- transit assets acquired;
- utility assets acquired;
- assets still owned at game end.

Acquisition metrics explain behavioral differences.

They are not used directly to declare the tournament winner.

---

## 1.45 Group-completion metrics

Record:

- groups completed during the game;
- complete groups owned at game end;
- first group-completion turn.

If a strategy never completes a group:

    first_group_completion_turn = null

These metrics are diagnostic.

---

## 1.46 House-development metrics

Record:

- total houses built during the game;
- houses still owned at game end;
- first house-build turn.

If a strategy never builds:

    first_house_build_turn = null

This allows direct measurement of how rapidly the Aggressive Builder
actually deploys development capital relative to other strategies.

---

## 1.47 Rent-paid and rent-collected metrics

Every player tracks:

    total_rent_paid
    total_rent_collected

Derived:

    net_rent
    =
    total_rent_collected
    -
    total_rent_paid

These are diagnostic explanations for performance.

Rent itself remains a zero-sum player-to-player transfer before
bankruptcy shortfalls.

---

## 1.48 Cash-reserve metrics

Track:

- minimum cash observed;
- median end-of-turn cash;
- mean end-of-turn cash;
- number of active turns ending below the strategy's desired reserve.

A reserve breach means:

> An active player's end-of-turn cash is below that strategy's configured
> desired reserve.

This makes the difference between Cash Protector and Aggressive Builder
empirically measurable rather than merely descriptive.

---

## 1.49 Game-length metrics

Per game:

    turns_played
    termination_reason

Tournament aggregates:

    mean turns
    median turns
    turn-limit resolution rate

Game length is primarily a simulation diagnostic.

It is not one of the three headline video metrics.

---

## 1.50 Confidence-interval methodology

Win rate and bankruptcy rate are binomial proportions.

Their canonical 95% confidence intervals use the:

    Wilson score interval

with:

    z = 1.959963984540054

For observed proportion:

    p_hat = successes / n

the Wilson center is:

    (p_hat + z^2/(2n))
    ------------------
        1 + z^2/n

and half-width is:

                    sqrt(
                         p_hat(1-p_hat)/n
                         + z^2/(4n^2)
                        )
    z * --------------------------------
                      1 + z^2/n

Final bounds are clipped to:

    [0, 1]

The initial Project 3 headline does not require a confidence interval for
median finishing cash.

A later contract section defines how statistically close strategy win
rates affect winner interpretation.

---

## 1.51 Strategy-pair comparison methodology

Every canonical game contains all four strategies.

Therefore six unique strategy pairs are evaluated.

For strategies A and B, define head-to-head superiority rate as:

    games where A finishes above B
    --------------------------------
    games containing both A and B

The canonical denominator is 10,000.

Because deterministic ranking removes tied finishing positions:

    H2H(A,B) + H2H(B,A) = 1

Also report:

- win-rate difference;
- bankruptcy-rate difference;
- median-finishing-cash difference.

Inferential pairwise comparison uses a two-sided exact binomial test
against the null head-to-head rate of 0.50.

Because six pairwise comparisons are performed, Holm correction is
applied with family-wise alpha 0.05.

The project distinguishes a numerical leader from a statistically
supported advantage.

If the inferential comparison does not support separation, the result
must be described as statistically close rather than overstated.

---

## 1.52 Fairness acceptance thresholds

Hard canonical fairness requirements are:

- exactly 10,000 completed games;
- exactly 40,000 strategy-game records;
- four strategies per game;
- four distinct seats per game;
- exactly one winner per game;
- positions 1 through 4 assigned exactly once per game;
- exactly 10,000 appearances for every strategy;
- exactly 2,500 appearances per strategy per seat;
- zero impossible ownership states;
- zero illegal house states;
- zero unresolved games;
- tournament win rates sum to one within 1e-12;
- same master seed reproduces the same canonical output hash.

Seat-effect diagnostics are:

    overall seat win-rate spread <= 0.05
    within-strategy seat win-rate spread <= 0.10

Exact exposure balance is the primary anti-bias mechanism.

Large empirical seat effects still trigger investigation.

---

## 1.53 Canonical 10,000-game tournament contract

The canonical tournament contains:

    10,000 games
    4 strategies per game
    40,000 strategy-game result rows
    master seed 73031
    maximum 500 turns per game

Tournament execution is headless.

Rendering is disabled during tournament simulation.

Execution must remain bounded.

Unbounded multiprocessing is prohibited.

---

## 1.54 Representative-game selection contract

The representative game is selected automatically.

Manual cherry-picking is prohibited.

Winner identity and seat identity are not selection features.

An eligible game contains at least:

- one property purchase;
- one rent transfer;
- one completed group;
- one house build;
- one strategy reserve breach.

Eligible games are compared with tournament medians for:

- turns played;
- property purchases;
- houses built;
- rent transferred;
- bankrupt-player count.

Each feature is normalized by median absolute deviation.

A zero median-absolute-deviation scale uses fallback 1.0.

The game with the smallest total absolute standardized distance is
selected.

Final deterministic tie-break:

    lowest game_index

---

## 1.55 Tournament-results CSV schema

Output:

    outputs/p02_monopoly_ai/data/tournament_results.csv

Grain:

    one row per strategy per game

Canonical row count:

    40,000

The schema records identifiers, seed, seat, finishing position, winner,
bankruptcy state, cash, terminal net worth, acquisition, groups, houses,
rent, liquidity behavior, game length, and termination reason.

---

## 1.56 Tournament-summary JSON schema

Output:

    outputs/p02_monopoly_ai/data/tournament_summary.json

The summary contains:

- schema metadata;
- tournament seed and game count;
- headline result;
- strategy-level statistics;
- six pairwise comparisons;
- fairness results;
- game-length statistics;
- representative-game identity;
- validation results;
- artifact hashes.

No video renderer may independently recompute or hardcode the winner.

---

## 1.57 Representative-game event-log schema

Representative summary:

    outputs/p02_monopoly_ai/data/representative_game.json

Representative event bundle:

    outputs/p02_monopoly_ai/data/representative_game_events.json

The event bundle stores:

- game identity;
- game seed;
- initial state;
- ordered real engine events;
- final state.

The 14–31 second video sequence replays these events.

---

## 1.58 Video-manifest schema

Manifest:

    outputs/p02_monopoly_ai/manifests/ai_landlord_arena.json

It records:

- media metadata;
- timeline contract;
- canonical tournament identity;
- representative-game identity;
- headline winner;
- displayed metrics;
- source artifact hashes;
- render metadata.

---

## 1.59 Media contract

Canonical video:

    outputs/p02_monopoly_ai/video/ai_landlord_arena.mp4

Media specification:

    1080 x 1080
    60 seconds
    30 FPS
    1,800 frames
    H.264
    yuv420p

Audio is not required.

All visuals must be original analytical graphics.

---

## 1.60 Opening storyboard — 0 to 7 seconds

Headline:

    4 STRATEGIES · 10,000 GAMES

Hook:

    Four landlord strategies.
    10,000 games.
    Which one survives?

Story purpose:

Introduce the controlled capital-allocation experiment immediately.

---

## 1.61 Strategy introduction — 7 to 14 seconds

Four cards introduce:

    Collector          — BUY BROADLY
    Specialist         — TARGET GROUPS
    Cash Protector     — KEEP CASH
    Aggressive Builder — BUILD FAST

Story purpose:

Explain the investment philosophies before showing outcomes.

---

## 1.62 Representative game — 14 to 31 seconds

Replay the actual deterministic representative-game event log.

Show:

- dice;
- movement;
- purchases;
- ownership changes;
- rent transfers;
- group completion;
- houses;
- cash changes;
- liquidity warnings.

Story purpose:

Demonstrate how policy differences become real economic decisions.

---

## 1.63 Scale-up — 31 to 39 seconds

Transition from one representative game to the full tournament.

Counter reaches exactly:

    10,000

Key line:

> One game is a story. 10,000 games are evidence.

---

## 1.64 Leaderboard — 39 to 50 seconds

The leaderboard converges toward actual tournament win rates.

Headline metric:

    tournament win rate

Supporting metrics:

    bankruptcy rate
    median finishing cash

Story purpose:

Reveal repeated performance rather than one-game luck.

---

## 1.65 Risk/reward — 50 to 55 seconds

Display:

- highest win rate;
- lowest bankruptcy rate;
- highest median finishing cash.

Story purpose:

Show that reward, survival, and liquidity need not identify the same
strategy.

---

## 1.66 Winner summary — 55 to 60 seconds

Opening line:

    10,000 GAMES LATER...

Reveal the actual numerical tournament winner, win rate, confidence
interval, and statistically responsible interpretation.

The closing lesson must be derived from the actual result.

No winner or conclusion is frozen before the tournament runs.

---

## 1.67 Video data-to-visual traceability

All result-bearing video content maps to persisted artifacts.

Representative actions derive from:

    representative_game_events.json

Leaderboard and metrics derive from:

    tournament_summary.json

Final winner derives from:

    tournament_summary.headline_result

The manifest stores hashes for the tournament, summary, representative
game, and representative event log.

Hardcoded winners and hardcoded result metrics are prohibited.

---

## 1.68 Project acceptance criteria

Project 3 is accepted only when:

- rules are frozen;
- four policies are implemented and configuration-driven;
- game engine is deterministic;
- impossible-state count is zero;
- 10,000 tournament games complete;
- 40,000 strategy-game rows exist;
- seat distribution is exact;
- statistical outputs validate;
- representative-game selection is deterministic;
- animation replays actual event data;
- video is exactly 1080 x 1080 / 60 seconds / 30 FPS / 1,800 frames;
- H.264 / yuv420p validation passes;
- no text clipping occurs;
- generated outputs remain ignored;
- CI passes;
- pull request is merged;
- merged main passes final regression.
