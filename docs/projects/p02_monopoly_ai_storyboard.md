# Project 3 — 60-Second Video Storyboard Contract

## Canonical media

- Resolution: 1080 x 1080
- Duration: 60 seconds
- FPS: 30
- Frames: 1,800
- Codec: H.264
- Pixel format: yuv420p

Output:

    outputs/p02_monopoly_ai/video/ai_landlord_arena.mp4

---

## Global geometry

Header:

    x=0 y=0 width=1080 height=90

Main:

    x=0 y=90 width=1080 height=850

Footer:

    x=0 y=940 width=1080 height=140

---

## 0–7 seconds — Opening

**Story:** Establish the experiment.

Headline:

    4 STRATEGIES · 10,000 GAMES

Hook:

    Four landlord strategies.
    10,000 games.
    Which one survives?

Hook region:

    x=70 y=150 width=940 height=500

Strategy strip:

    x=70 y=680 width=940 height=210

---

## 7–14 seconds — Strategy introduction

**Story:** Explain how the investment philosophies differ.

Card region:

    x=30 y=145 width=1020 height=690

Each card:

    width=240 height=690 gap=20

Cards:

- Collector — BUY BROADLY
- Specialist — TARGET GROUPS
- Cash Protector — KEEP CASH
- Aggressive Builder — BUILD FAST

---

## 14–31 seconds — Representative game

**Story:** Convert abstract policy into observable economic decisions.

Board:

    x=30 y=120 width=690 height=690

Dashboard:

    x=740 y=120 width=310 height=690

Event ticker:

    x=30 y=830 width=1020 height=90

Replay real engine events:

- dice
- movement
- purchases
- ownership
- rent
- group completion
- house development
- cash
- reserve warning

---

## 31–39 seconds — Scale-up

**Story:** Move from anecdote to evidence.

Counter:

    x=70 y=180 width=940 height=280

Mini-game field:

    x=70 y=490 width=940 height=390

Counter ends at:

    10,000

Key line:

    One game is a story. 10,000 games are evidence.

---

## 39–50 seconds — Tournament leaderboard

**Story:** Reveal repeated performance.

Leaderboard:

    x=70 y=160 width=940 height=560

Metric strip:

    x=70 y=740 width=940 height=170

Display:

- win rate
- bankruptcy rate
- median finishing cash

---

## 50–55 seconds — Risk versus reward

**Story:** The most successful strategy need not be the safest.

Cards:

    x=60  y=230 width=300 height=360
    x=390 y=230 width=300 height=360
    x=720 y=230 width=300 height=360

Cards show:

- highest win rate
- lowest bankruptcy rate
- highest median finishing cash

Takeaway:

    x=60 y=630 width=960 height=200

---

## 55–60 seconds — Winner reveal

**Story:** End with the result and its actual risk-return lesson.

Headline:

    10,000 GAMES LATER...

Winner source:

    tournament_summary.headline_result

Display:

- winner
- win rate
- 95% confidence interval
- statistically responsible interpretation
- data-driven takeaway

No conclusion is hardcoded before the tournament.

---

## Traceability

Representative gameplay:

    representative_game_events.json

Tournament metrics:

    tournament_summary.json

Final winner:

    tournament_summary.headline_result

The video manifest must hash every result-bearing input.

---

## Disclaimer

Unofficial analytical simulation. Not affiliated with or endorsed by
Hasbro.
