# RoundaboutHD source screening — Block 1

## Decision

SOURCE_REJECTED_EPISODE. Cam02 is the highest-ranked screened candidate, not an approved primary. No baseline/buildup/degraded interval is frozen. No geometry or calibration preview is generated. This is a bounded screening decision, not proof that no queue exists anywhere.

## Metadata

Each video fully decodes to 9000 frames, 600.000 seconds, 3840x2160, MPEG-4 Simple Profile, 15 nominal/decoded-average fps, CFR, time base 1/15360, no audio. PTS starts at 0, ends at 9214976, every step 1024. Raw files were neither transcoded nor changed.

| Camera | Bytes | SHA-256 |
|---|---:|---|
| cam01 | 2258398838 | cfa1d418c5e3943e0eabba3f7325771c9fa205cdd8c1470bd3424824b9184fb6 |
| cam02 | 1248996690 | e825f236260a06c59933acf1899f50e95ecc478a5582fedd6335011c9562778f |
| cam03 | 1945000914 | 4e45abb1a63891c1f5b795c681ba29718ffa1fbcb219794d2140c48f73c081ae |
| cam04 | 1435846191 | d43ca48eae06ad5d4ece2547d9ba35c77237d296c31a6f6fce07dbe57662b235 |

## Annotation findings

All three ZIP types contain six-column pixel XYXY rows: class-like ID, xmin, ymin, xmax, ymax, score-like value. They are not normalized YOLO center/width/height rows. labels_GT uses labels_filtered (cam01/02) or labels_corrected (cam03/04). labels_xy uses the same geometry with more score precision and sometimes additional boxes. Its name does not imply another coordinate system.

labels_test uses labels_sct2det, with score 1 in inspected samples. Coordinates predominantly match SCT frame number +1, consistent with a conversion; it is not established as independent predictions or independent ground truth. Some cam01/02 sample boxes do not match even at this offset. Retain that mismatch for later validation. Cam04 labels_test has 8870 frame members rather than 9000; missing members are unavailable, not empty-vehicle frames. Other inspected archives have 9000 members.

SCT has seven whitespace-delimited fields: frame, track, xmin, ymin, xmax, ymax, final integer (observed 2). The public README describes six fields and zero-based frame wording, whereas local SCT begins at 1 and sampled coordinates align to ZIP filename+1. Cam02 has the supplied double .txt.txt suffix. Files are track-grouped rather than globally frame-ordered. Duplicate frame/track keys and edge/out-of-frame boxes remain in raw data; all affected observations are excluded from derived screening. No clipping or ground-truth correction is performed.

SCT/detection annotations may support later Steps 5/6 after coverage, alignment, class and label-quality review. Their filenames do not establish independent validation. No detector comparisons or cross-camera identity joins were performed.

## Screening and ranking

The fourteen factors are fixed-camera quality, visibility, scale, direction, entry/exit potential, queue-zone potential, density variation, normal interval, buildup evidence, sustained degradation, track continuity, limited occlusion, analytical clarity and visual clarity. Each reviewer rating is 0 absent, 1 limited or 2 strong, equally weighted; ties use camera ID. Missing sustained degradation blocks approval regardless of score.

| Camera | Score /28 | Mean count | Median | Variance | Tracks | Median track span s | Excluded rows | Longest 2-low-motion run s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cam02 | 23 | 6.076 | 6 | 7.873 | 244 | 13.867 | 0 | 1.067 |
| cam01 | 22 | 6.855 | 7 | 7.717 | 262 | 14.900 | 12 | 0.000 |
| cam03 | 22 | 6.562 | 6 | 8.485 | 279 | 12.600 | 760 | 3.667 |
| cam04 | 22 | 6.300 | 6 | 6.856 | 257 | 14.333 | 28 | 5.333 |

These are SCT coverage indicators, not final Project 6 metrics. Counts include supplied annotation coverage across the image; parked/omitted vehicles and perspective limit interpretation. Track span is not completed zone dwell. Motion uses normalized bottom-center displacement over one complete original second. Low-motion screening uses <0.002 image diagonals/s, box height >=60 px, bottom point below 25% frame height; these assumptions are not final warning/outcome thresholds. Thirty-second bins retain counts and median motion.

Closest reviewed candidates: cam02 205–250s (individual right-side yielding, longest observed stop 217–233.2s); cam03 390–435s (busy circulating traffic with brief entry yielding); cam04 170–200s (short simultaneous yielding). Reviewed frames do not establish a sustained degraded state. Twelve full-episode frames per camera and twelve targeted frames per candidate were reviewed; no exhaustive human review claim is made.

## Provenance and publication

Supplied local package has no LICENSE/README. The matching documented structure and metadata corroborate RoundaboutHD, but no upstream per-file checksum was supplied. Bath archive DOI 10.15125/BATH-01574 lists creators Yuqiang Lin, Sam Lockyer and Starwit Technologies GmbH and the exact wording "Software: MIT License". That label is preserved rather than inventing license text. Internal screening is explicitly authorized; public raw-video and derivative release remain review-required, including source-visible businesses/plates/faces. Neutral wording: "Fixed-camera traffic footage from the RoundaboutHD dataset."

Official documentation: https://researchdata.bath.ac.uk/1574/ ; https://github.com/siri-rouser/RoundaboutHD ; https://huggingface.co/datasets/yl4300/RoundaboutHD . Earlier source attempts were not reopened.

## Outputs and resumption

Ignored outputs: manifests/source_screening_summary.json, annotation_format_report.json, source_provenance.json and blocked source_manifest.json; images/source_screening/cam01_contact_sheet.png through cam04_contact_sheet.png and targeted review PNGs. Exact command/probe/PTS logs, source hashes and final regression evidence are under .cache/p05_traffic_operations_early_warning/roundabouthd-block1/.

A full [0,600) interval and "Ten minutes of traffic in one frame" are physically supported as candidate coverage, but not approved analytical/static deliverables. ROI, queue zone, entry/exit/direction/exclusions and calibration preview remain unset because Step 3 has not passed. RELATIVE_ONLY remains the future default. No physical mapping was supplied or used.

Next: review evidence and either establish a defensible qualifying episode or explicitly revise the episode scope. Block 2 and Git checkpoint actions remain unauthorized.
