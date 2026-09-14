# Sub-step 4.C.C - accelerated internal presentation

This supersedes the rejected 1x motion and static-per-scene contour treatment in
4.C.B. The first15-second factual story and canonical24:00 metrics remain unchanged.
The user authorized presentation-only regeneration of Steps12-14, including a
motion proof followed by complete production outputs. Step15 is not authorized.

## Two clocks

analytics_timebase: ORIGINAL_SOURCE_TIME.
presentation_playback: ACCELERATED_FOR_VISUALIZATION.

Linear display-speed ramps are integrated to obtain original source timestamps,
then floored to actual native10fps source frames. Rendering samples15presentation
frames per second and repeats each twice for30fps; no optical interpolation or
invented detector/tracker observations. The montage contains explicit cuts.

| Display seconds | Source interval seconds | Speed |
|---|---|---|
|0-4|1320-1356|8x to10x|
|4-9|1378-1413|6x to8x|
|9-15|1380-1446|10x to12x|
|15-20|1438-1483|8x to10x|
|20-25|1445-1512.5|12x to15x|
|25-30|1420-1475|10x to12x|
|30-35|1376-1441|12x to14x|
|35-40|1500-1535|6x to8x|
|40-44|1710-1746|8x to10x|
|44-45|1746-1749|8x to0x over0.75s, then0.25s hold|

The state scene deliberately uses12-14x to include the recorded NORMAL/WATCH/
WARNING transitions in five display seconds. Source-time labels distinguish the
current montage state from the fixed episode-result card showing warning24:00.
The configured onsets are never backdated. Warning24:00, null queue onset, null
lead time and canonical numerical window(1380,1440] remain frozen.

## Dynamic layers and causality

At each unique rendered frame, select accepted observations in(t-45,t] for the
contour field and(t-60,t] for trails. No future observations enter either layer.
Histogram:128x72bins,10source-pixel cells; Gaussian sigma1.2bins, log1p normalization,
four contour levels0.25/0.45/0.65/0.85. Smoothing is visualization-only. The field
is rebuilt from current trailing data; topology changes, not merely alpha.

Tracks use actual recorded reference-point segments. Gaps greater than1s are
not bridged. Alpha decreases with source-time age; old segments disappear after
60seconds. Track heads move with accepted observations. Current boxes use the
latest observation no older than0.4source seconds and can show sampling lag.
Sparse footage retains its real track population; no fabricated duplicate paths
are added to satisfy an arbitrary dozens-of-tracks aesthetic.

Crossing events create a3-source-second fading expanding pulse and a transient+1
at the recorded crossing location, emerald forENTRY and gold forEXIT. This is a
per-event annotation, not a newly calculated rolling KPI. No permanent orange
vehicle nodes remain. Direction cues derive from real gap-free image-plane
segments. The small chart cursor follows original source time over frozen charts.

The static ten-minute map deliberately uses full[1200,1800) accepted history,
64eligible track IDs, original background1799.9s and the v3palette. It is the
exception to moving-scene trailing history. Concentration is observation-weighted,
not unique-vehicle/physical density, road speed or a measured congestion hotspot.

## Semantic colors

Original PNG sampling found violet#835CF6 at4630exact pixels, alongside original
emerald#2BA668, amber#F2A93B, coral#E04F4F, white and the existing navy system.
Near-white#F4F7FA detections are separate from electric-violet#835CF6 active trails.
History fades through muted violet#62439A; the field progresses through curated
indigo#30205F, violet#835CF6 and magenta#EC4899. ENTRY is emerald#2BA668;EXIT gold
#F4CC63;WATCH amber#F2A93B;WARNING coral#E04F4F;neutral/queue outlines are gray-purple.
Curated extensions are labeled as extensions, not falsely claimed original samples.
No jet/rainbow/turbo/default color cycling is used. Original preview PNGs remain
unchanged. The old v2combination is marked DEPRECATED_VISUAL_STYLE.

## Evidence and propagation

Motion proof: project6_motion_proof_00_25s.mp4,25seconds, full decoded. It covers
hook, metrics, warning and the20-25s analytical hero. motion_validation.json checks
source changes, contour/trail evolution, time advancement, lifecycle and absence
of static overlays in every proof scene. Separate pixel checks compare real-source
ROIs and thresholded contour geometry, not text/clock changes. Final moving scenes
also pass the same checks; the deliberate final hold is exempt.

Final video contract:1080x1350,30fps,45seconds,H.264,yuv420p,1350frames; master and
web both fully decoded. All production outputs must postdate v3tokens, updated
presentation contract and passing proof motion_validation.json. First15text checks
bind actual rendered strings. Agent visual review is not empirical recruiter
comprehension or human public-release approval.

Canonical implementation: presentation_v3.py and render_v3.py; existing render_v2.py
and report_v2.py retain default-compatible interfaces with explicit source-time and
accelerated-report options. Use the block4cc command ledger for this exact build.
Any later approved presentation change must propagate to all artifacts unless
explicitly requested as diagnostic-only/preview-only work.

Publication remains PENDING_SOURCE_PERMISSION. Internal final-quality footage
is authorized; public clearance, production deployment, physical queue absence,
classifier accuracy and reduced false escalation are not claimed. No analytical
stage execution, threshold change, model/source download or Git mutation is allowed.
Current acceptance is manifests/block4cc_presentation_acceptance.json. Prior
4.C.B presentation acceptance is historical after authorized artifact replacement.
