# Method-B runtime-v9 seed-11 50 mm smoke attempt001

## Disposition

`SMOKE_PASS`. This run used 16 real Isaac environments with full registered
50 mm randomization and contributes zero accepted optimization transitions.
It authorizes a new from-scratch full-budget v9 training run.

- Environment Python PID: `54424` (exited normally).
- `training_result.json` SHA-256:
  `691f7b2fce5c25a62deb900691ed241338e6f367b843d8936b21efbe5600566d`.
- TensorBoard event SHA-256:
  `fa651e72b5c896cada7302b2952ede82d78a18e66bab16c5b854ae35b29abdf5`.
- stdout/stderr SHA-256:
  `b909ac923bdee660a184fb332cf2220700e9782dbd0fbd0b67ef9aa3b738fab8`
  and
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
- Common config SHA-256:
  `52311feb78d8ad1ef2741c7bc0408a24af8e9cbefc4970e3929c698035f9d138`
  (canonical
  `1f82953b32dd6c39dfba43841f09e5610e7d0a399777f70ab80eb8334ac064af`).

## Runtime evidence

- Actor/critic/action shapes were `16x96`, `16x146`, and `16x12`; all
  observations, values, actions, contacts, rewards, and 22 raw reward terms
  were finite.
- Runtime agent class was `AuditablePPO`; the synthetic done-row audit
  preserved env 0 while envs 5 and 7 ended.
- The window-derived physical scaled-residual maxima for phases 6/7/8/9 were
  exactly `0 / 0.0500000007 / 0.0500000007 / 0`. This directly proves that
  the real vectorized environment executes residuals only in phases 7--8.
- The isolated real tilt fall terminated with raw fall `1`, weighted fall
  `-200`, finite total reward `-404.904999`, and a true terminal snapshot.
- The next post-terminal step returned env 0 to target/actual front distance
  `0.266813397 / 0.265486181 m`, an error of `1.327 mm`, with no immediate
  success or done.
- Effective integrated residual weights remained `-120/-180`; physical
  residual bounds remained `7.5 mm / 10 mm / 0.10 rad/s`.
- Frozen FSM, metrics, and asset hashes remained
  `3e4b65ee...e4e9`, `6a02b1c0...30ab`, and `98103315...81dd`.

## Next action

Train Method B seed 11 at 50 mm from random initialization for exactly
19,200 local timesteps / 1,228,800 transitions with 64 environments and full
registered randomization. No prior checkpoint is reused.
