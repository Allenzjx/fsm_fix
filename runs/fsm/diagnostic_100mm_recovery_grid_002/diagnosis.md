# Recovery grid 002 diagnosis

- Execution completed for all 25 candidates on `development-h100-0000`.
- Strict successes: **0 / 25**.
- First terminal classification, latched at the active-to-done transition:
  `BODY_OR_LINK_COLLISION` for all 25 candidates.
- Therefore a phase-9/10 front-right-only wheel-center offset over
  `dx=[-15, 15] mm`, `dz=[-10, 10] mm` is rejected as a recovery mechanism.

## Evidence limitation

The script correctly latched each candidate's first success flag and failure
classification, so the 0/25 result is valid. It did not copy the detailed
terminal tensors at that transition. Isaac automatically reset completed
environments while the remaining batch continued, and 24 candidates' terminal
tensors were overwritten by a subsequent immediate phase-0 contact
termination. Candidate 6, the last first-episode termination, retained a valid
phase-10 snapshot (`dx=-7.5 mm`, `dz=-5 mm`): front-right support was still
zero and `front_right_bot` contact reached 7.9747 N.

Grid 003 repeats the identical candidates, scenario, controller, physics, and
thresholds after changing only the diagnostic recorder to copy the first
terminal snapshot immediately. No controller parameter is changed.
