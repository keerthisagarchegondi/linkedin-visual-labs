# Project 9 Video Storyboard

## Technical and safe-area contract

The final video is 1080 x 1350 portrait, 30 fps, H.264, yuv420p, and approximately 45 seconds. Safe area is stricter than the shared 60-pixel plotting margin: left/right 96 px, top 120 px, bottom 150 px; all text is constrained to x=96..984. Headings wrap by measured bounds; formulas use their own bounded zone; footer content remains above y=1200. Later validation requires layout-bounds tests, extracted keyframes, a contact sheet, and no clipping of headings, formulas, metrics, or footers.

## Frozen narrative

| Seconds | Purpose |
|---|---|
| 00-05 | Nontechnical analogy: a scoring rule can grant more credit than the alert earned. |
| 05-10 | Explain anomaly detection and anomaly events. |
| 10-15 | Show raw pointwise scoring. |
| 15-20 | Show PA with the same predictions. |
| 20-25 | Explain event-hit probability and event length. |
| 25-30 | State the controlled experiment. |
| 30-35 | Show the validated headline result from frozen release data. |
| 35-40 | Explain meaning and limits. |
| 40-45 | Close with reproducibility, research artifact, and manuscript/preprint route. |

No dummy or preview number may enter a public output.
