# Project 6 visual system

## Authority and pre-edit audit

The 2026-09-13 Block 4 Sub-step 4.A request supersedes the interrupted Project 5
alignment attempt. Only reference/project6/previews controls this repair. All 18
files were found; all 10 video PNGs and 5 tab PNGs were individually inspected,
along with both reference and prior output contact sheets and the prior trajectory.
The reference contract specifies video1080x1350 and report1600x1000. Reference
imagery and analytical values remain PREVIEW_ONLY; reference files are unchanged.

| Mapping | Old gap | Repair composition |
|---|---|---|
| 00s hook | Oversized header, small diagram, upper title | Header0-103; derived hero103-851; lower white/amber hook |
| 05s detection | Tiny markers, no hero framing | Same hero; cyan editorial markers at actual coordinates; lower-left process chip |
| 10s teaser result | Three generic full-width cards | Right timeline x676-1040,y151-813; actual warning/null outcome/null lead |
| 15s metric definition | Generic line charts | Right dark definition panel x560-1034; four white definition tiles |
| 20s tracking challenge | Counts replace traffic | Derived traffic remains; right challenge/reconciliation overlay; aggregate counts |
| 25s metrics | Three sparse charts | Right journey eligibility panel; three lower white KPI cards |
| 30s warning | Generic full-width state cards | Left state progression; right four white chart panels |
| 35s lead time | Repeated result cards | Configured geometry emphasis; lower cream null-result callout; no invented hotspot |
| 40s action | Unstructured text | Right dark recommendation panel with amber conditional response |
| Close | Vertical word list | Hero retained; lower horizontal process message and colored circle icons |
| Dashboard | Uniform dark generic grid | Light canvas; six overview cards; wide flow map; chart column; green action strip |
| Video | Centered video and button row | Dark player/storyboard panel left; five source/time cards right |
| Method | Generic four text cards | Seven pipeline cards; two contract panels; five privacy/technical cards |
| Results | Generic KPI/table/plot stack | Dark lead card; horizontal event timeline; four metric cards; interpretation/check columns |
| About | Generic four-card grid | Dark problem and white challenge panels; four capabilities; stack/limits row |
| Static | Oversized header and plain summary | Compact header; dark derived map; warning timeline; white metric cards |

This gap matrix was communicated before rendering or changing presentation code.
State was changed to VISUAL_REPAIR_IN_PROGRESS; prior acceptance is historical.

## Sampled palette

Exact RGB frequency inspection of all references recovered these tokens:
video background #091522; header #0B1A2A; analytical panel #081623;
white #FFFFFF; amber #F2A93B; cyan #1CBCDD; blue #2F80ED; green #2BA668;
red #E04F4F; purple #8655FF; cream #FFF6E1; report canvas #F4F7FA;
report ink #152738; report borders #DAE2EA. Secondary text #526B82 is a darker,
accessible adaptation of the reference muted gray; dark-panel text uses #B7C7D5.
Video/static remain dark. The report is light with dark analytical panels, as its
own Project 6 references require. No matplotlib default styling is used for new visuals.

## Typography and components

Raster font: repository-installed matplotlib DejaVu Sans Regular/Bold, no private
font redistribution. HTML uses a system fallback stack and embeds no fonts.
Video header29px, primary caption45px, amber caption43px, body24px, labels18-26px,
KPI29px, disclaimer17px. Report title30px, section25px, body15px, KPI22-28px,
labels12-14px. Exact fonts differ, hierarchy and placement follow references.
Video margins42/55px; cards15-20px radius, thin borders, flat white/dark fills.
Report padding30px; grid gaps22/34px; cards16px radius; active blue underline tabs.
Mobile collapses grids and preserves keyboard-accessible tabs and readable hierarchy.

## Evidence and allowed differences

No photographic pixels, invented airport context, persistent identity or detector
boxes are copied. The hero is a labelled schematic using verified normalized
geometry and trajectories; editorial markers do not claim detector box sizes.
Uniform mapping retains source aspect ratio. Paths never connect observation gaps
above1second; incomplete tracks remain dashed. Geometry is configured, not a
measured hotspot. Full-episode counts are explicitly separate from the ten-minute map.

Actual classification NO_VISIBLE_QUEUE_EVENT; warning24:00; queue and lead null.
Density/imbalance/trend drive the warning. Throughput and movement increased and
remain visible as mixed evidence. Unavailable baseline dwell is not fabricated.
Recommendations retain conditional review wording and illustrative status.

## Implementation and acceptance

Shared tokens/mappings: design_system.py. Raster: visualization.py and video.py.
Portable report: reporting.py and report_design.py. Structural measurements:
visual_fidelity.py. Existing analytical presentation.py is unchanged. The old
report narrative remains accessible in expandable evidence sections; new primary
charts read the admitted metrics without overwriting original diagnostic charts.

Automated measurements inspect dominant palette, brightness, edge/content density,
canvas and header regions. They exclude photographic hero pixels from color
acceptance and explicitly require visual review of composition. They do not certify
perceptual equivalence by themselves. Reference overlays are mapped in code/manifests.
Final review and gate results are recorded separately in BLOCK4A_VISUAL_REVIEW.md.
Step15 and public publication approval are outside this repair.
