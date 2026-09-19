# Project 7 ? Step 6 ? Visual Contract V1.0

Status: **FROZEN**

This document is the human-readable companion to:

`assets/p27_prediction_time_integrity_auditor/style/p27_step6_visual_contract.json`

Contract SHA256: `1458c71f6853afddae5a0da7a73870ba3230eee2144daf5189b6ca207f280469`

## Purpose

Freeze the exact visual system for the replacement Step 6 research figures and 45-second animated video before renderer implementation begins.

The prior Step 6 release remains a historical PASS. This contract governs the visual-uplift replacement.

## Immutable canvas / export contract

- Canvas: **1080 ? 1350 px**
- Aspect ratio: **4:5**
- Internal supersampled canvas: **2160 ? 2700 px**
- Final downsample: **LANCZOS**
- Frame rate: **30 fps**
- Target duration: **45.0 seconds**
- Primary codec: **H.264 / libx264**
- Pixel format: **yuv420p**
- Keyframes: **10**

## Frozen typography

- Headline: `InterTight-Bold.ttf`
- Heavy headline / metric: `InterTight-ExtraBold.ttf`
- Body: `Inter-Medium.ttf`
- UI semibold: `Inter-SemiBold.ttf`
- UI bold: `Inter-Bold.ttf`
- Technical / timestamp: `JetBrainsMono-SemiBold.ttf`

Typography sizes, line heights, tracking and wrapping behavior are defined in the JSON contract and may not drift.

## Frozen presentation system

- Background: `#F4F7FB`
- Dark navy header/footer: `#0F2033`
- Primary blue: `#3C82F6`
- PASS green: `#1F9E62`
- WARN amber: `#CC7A00`
- BLOCK red: `#E45858`
- Cards: 16 px radius, 1 px light border, two-layer soft shadow
- Base safe margins: 48 px
- Baseline grid: 8 px
- Header: 84 px
- Footer progress chrome: fixed across scenes

## Frozen motion / rendering primitives

- 2? antialiasing supersampling
- 14 px active-element glow radius
- 14 px Gaussian glow blur
- 20 px Gaussian shadow blur
- Neural-flow particles: 5 px, 5 px/frame
- Release-gate conveyor motif
- Rounded minimal outline icon grammar

## Scene timing contract

| # | Scene | Start | End | Duration | Template | Headline |
|---:|---|---:|---:|---:|---|---|
| 1 | S1 | 0.0s | 4.5s | 4.5s | `hero_metrics` | The model looked / production-ready. |
| 2 | S2 | 4.5s | 8.5s | 4.0s | `single_violation_card` | It had already seen / the answer. |
| 3 | S3 | 8.5s | 12.5s | 4.0s | `feature_contract_checklist` | Step 1: define the prediction moment |
| 4 | S4 | 12.5s | 17.0s | 4.5s | `five_leakage_cases` | Five ways a model can / accidentally see the future |
| 5 | S5 | 17.0s | 21.0s | 4.0s | `split_comparison` | The split changed the answer. |
| 6 | S6 | 21.0s | 25.0s | 4.0s | `headline_metric_rewrite` | Honest evaluation changed / the headline metric. |
| 7 | S7 | 25.0s | 29.5s | 4.5s | `business_impact_compare` | The metric error became / a campaign-planning error. |
| 8 | S8 | 29.5s | 34.0s | 4.5s | `gate_not_patch` | The fix was a release gate, / not one deleted column. |
| 9 | S9 | 34.0s | 40.0s | 6.0s | `deployment_decision_dark_panel` | Automated deployment decision |
| 10 | S10 | 40.0s | 45.0s | 5.0s | `closing_recap` | Accuracy is not evidence / until evaluation matches deployment. |

Total scene duration: **45.0 seconds**

## Scene motifs

- S2 / S8: neural-network / signal-flow language
- S8 / S9: release-gate conveyor language
- S5 / S6 / S7: real metric comparison / distortion visuals
- S9: dark deployment-decision panel
- S10: polished product-explainer close

## Text wrapping contract

- Balanced greedy word wrapping
- No hyphenation
- No ellipsis
- Avoid single-word final lines
- Main headline maximum: two lines
- Subhead maximum: four lines
- Maximum one accent span per headline

## Change-control rule

Do not modify typography, spacing, palette, card geometry, motion primitives, scene timing, status language, export dimensions or antialiasing behavior without an explicit new visual-contract version.

## Current execution checkpoint

- 6.19.C ? Visual contract freeze: PASS
- 6.19.D ? Design tokens + typography helpers: NOT_STARTED
- Step 7: NOT_STARTED
- Automatic advance: FALSE
