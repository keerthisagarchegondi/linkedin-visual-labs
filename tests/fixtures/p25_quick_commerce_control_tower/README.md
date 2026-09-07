# Project 5 deterministic test-only fixture

These files are synthetic test inputs, not portfolio evidence. Real-data commands never fall back to them. `commerce prepare-data --fixture` is explicit and writes beneath `data/fixture/`, separate from the real prepared file.

The sales fixture has 112 observed days and 50 item rows: two items for each of the 20 selected store-category series and one excluded HOBBIES item per store. The calendar has 117 days so tests prove that future calendar dates do not extend the observed-demand holdout. The final 28 observed days produce 560 holdout observations; full aggregation produces 2,240 rows.

The independent expected table was constructed from this closed-form formula, not the DuckDB implementation. Let `s` be the zero-based store index in CA_1, CA_2, CA_3, CA_4, TX_1, TX_2, TX_3, WI_1, WI_2, WI_3 order, `c` be 0 for FOODS and 1 for HOUSEHOLD, and `d` be the one-based day number:

- Item 1: `s + 1 + c + 2*(d modulo 7)`.
- Item 2: `2*s + c + 3`.
- Both items are zero when `d` is divisible by 17.
- Independent expected series total: zero on those days; otherwise `3*s + 2*c + 4 + 2*(d modulo 7)`.
- Excluded HOBBIES item: 999 each day.

Dates begin 2016-01-01. Event 1 occurs on days divisible by 13; event 2 occurs on days divisible by 19. SNAP uses `(d + state_offset) modulo 10 < 3`, with offsets 0, 3, and 6 for CA, TX, and WI. `fixture_manifest.json` records dimensions, classification, formula, and SHA-256 hashes. Tests independently compare every aggregate cell and the state-specific SNAP mapping.
