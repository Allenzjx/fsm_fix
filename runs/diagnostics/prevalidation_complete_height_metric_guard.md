# Prevalidation complete-height metric guard

## Finding

Before validation and method freeze, a boundary audit found that
`summarize_episode_rows` computed an equal-height continuous mean from the
non-empty height groups. If every margin or pitch-rate value at one complete
50/75/100 mm height were missing, the generic aggregate could therefore
average only the other two heights.

The final report's stricter stratified implementation already returned
unavailable in this case, but validation summary construction used the
generic aggregate. This was a fail-open inconsistency.

## Correction

The equal-height margin and pitch-rate aggregates now require at least one
valid value in every registered height. If any height is empty, the aggregate
is `None`, and `validation_selection.build_validation_summary` rejects the
candidate because its primary validation stability metrics are incomplete.
No missing value is filled with zero and no remaining-height estimate is
silently substituted.

This changes no raw metric, evaluator, scenario, training, reward, PPO,
checkpoint, or selection order. It only closes an incomplete-data path before
validation begins. The locked-test manifest remained unread.

## Verification

- `src/resume_validation/aggregate_results.py` SHA256:
  `0a0f4567a9f44c4d2fc40803d52bee8175ef30630f56dace9519ae1928edb684`
- Complete CPU regression: 186 tests, 0 failures.
- Added regression: a missing entire height returns unavailable for both
  equal-height continuous aggregates.
