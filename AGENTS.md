# Repository operating rules

These rules apply to all work in this repository.

- Work only inside `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Never modify `D:\linkedin-visual-labs`.
- Never modify unrelated project packages.
- Never access ChangeGraph or job_hunter.
- Preserve the existing repository architecture.
- Use complete, coherent deterministic file edits.
- Preserve all existing quality gates.
- Use full type annotations for Python implementation.
- Use fixed deterministic seeds.
- Keep raw datasets, caches, fitted models, preview media, and generated large media out of Git.
- Never weaken or delete tests merely to make checks pass.
- Run the relevant tests after every implementation step.
- Report every file created or changed.
- Report every command run and its result.
- Stop after the explicitly requested implementation step.
- Do not stage, commit, push, force-push, or rewrite Git history unless explicitly instructed later.
- Keep `reference/project5/` local-only and unstaged. Preserve its exact exclusion in `.gitignore`; do not broaden it to unrelated reference content.
- Do not modify `contracts/repository_continuity.json` unless an existing continuity gate explicitly requires a compatible Project 5 update and the reason is explained first. Preserve repository identity, ancestry, and all earlier-project baselines.

## Project 5 identity and scope

- Active project branch: `project/p26-quick-commerce-control-tower`.
- Internal package: `p25_quick_commerce_control_tower`.
- The approved implementation plan is `docs/projects/p25_quick_commerce_control_tower/IMPLEMENTATION_PLAN.md`.
- The authoritative analytical and recruiter-facing narrative contract is `docs/projects/p25_quick_commerce_control_tower/PRODUCT_CONTRACT.md`.
- A plan describes future work; it does not authorize that work. Implement only the step explicitly requested by the user.
