# Method-B runtime-v10 seed-11 50 mm full-development attempt001

## Disposition

`TRAINING_INTEGRITY_PASS`. The from-scratch run completed exactly **76,800
local timesteps** and **4,915,200 transitions** in 64 real Isaac
environments. Performance remains unproven pending deterministic evaluation.

- Environment Python PID: `101592` (exited normally).
- Final checkpoint SHA-256:
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`.
- Result/event SHA-256:
  `13e54e3fcd40ac9ed374eaa043266816dcd6c8c24317f8af0b93de3ff2bd76ee`
  and
  `9a29737cd266446e710a2c339089ec6f796a92bcb816c7908ae7807c69740ac0`.
- stdout/stderr SHA-256:
  `f747b5a00b60364954498fa58e8a084b610c8a3ff4d9d473cf22a8bd5d7112c8`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

## Integrity evidence

- Requested/completed local and cumulative budgets agree exactly;
  `resume_offset_timesteps=0` and no checkpoint was loaded.
- The final checkpoint contains 77 tensors / 785,093 elements; every
  floating/complex value is finite and the non-finite count is zero.
- All 11 core scalar series contain exactly 1,200 finite updates from step 64
  through 76,800.
- Six repaired episode series contain 364 finite completion windows through
  step 76,736, versus 36 in v9 medium development. Episode length extrema are
  3,822--8,999, with no false 168-step tracker segment.
- Instantaneous reward extrema include success (`+200.017`) and safety
  terminal (`-200.263`) transitions. Rolling maximum total reward improved
  from about `-1292` to `-88.7`; this is a training signal, not a development
  evaluation claim.
- Policy standard deviation remained finite and ended at `0.0710708`.
- All 48 scheduled periodic checkpoints plus final/recovery artifacts were
  written. Provenance records the exact budget, direction signs, source and
  frozen hashes, randomization, reward, versions, and GPU.

## Next action

Restore the explicit final checkpoint in the independent deterministic
evaluator. First run the one-scenario five-second provenance/action-chain
smoke, requiring policy actions to remain nonzero while projected
`executed_action_*` and scaled residuals are exactly zero outside phases 7--8.
Then run all 20 fixed development scenarios if smoke passes.
