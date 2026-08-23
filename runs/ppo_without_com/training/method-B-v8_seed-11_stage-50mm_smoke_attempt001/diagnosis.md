# Method-B runtime-v8 seed-11 50 mm smoke attempt001

## Disposition

`SMOKE_PASS`. This run used 16 real Isaac environments with full registered
50 mm randomization and contributes zero accepted optimization transitions.
It authorizes a new from-scratch full-budget v8 training run.

- Environment Python PID: `95928` (exited normally).
- `training_result.json` SHA-256:
  `2f0f865cc9f4f8f41aa0e3f6a697d24e2c4ed7fd3f8eed42442b6b637ad48f33`.
- TensorBoard event SHA-256:
  `6d0f1d18b5e2d0e0fe087d45d001703ff8afcd4dc37d5bb3f18a51ac64aed8d8`.
- Common config SHA-256:
  `e97d76f169b08d4b3503a5ad74c26e9077664fb2aef7c92fb74874d4a6dc0333`
  (canonical
  `a571f9c16d30593b133d1cd78adf33288fe9ce1f4bffb3bd749d22ac117b0200`).

## Runtime evidence

- Actor/critic/action shapes were `16x96`, `16x146`, and `16x12`; all
  observations, values, actions, contacts, rewards, and 22 raw reward terms
  were finite.
- Runtime agent class was `AuditablePPO`; the synthetic done-row audit
  preserved env 0 while envs 5 and 7 ended.
- Physical scaled-residual maxima for phases 1/2/10 were exactly
  `0 / 0.0500000007 / 0`, directly verifying the common phase-2--9 execution
  window.
- The isolated real tilt fall terminated with raw fall `1`, weighted fall
  `-200`, finite total reward `-404.904999`, and a true terminal snapshot.
- The next post-terminal step returned env 0 to target/actual front distance
  `0.266813397 / 0.265486181 m`, an error of `1.327 mm`, with no immediate
  success or done.
- Effective integrated residual weights were `-120/-180`; physical residual
  bounds remained `7.5 mm / 10 mm / 0.10 rad/s`.
- Frozen FSM, metrics, and asset hashes remained
  `3e4b65ee...e4e9`, `6a02b1c0...30ab`, and `98103315...81dd`.

## Next action

Train Method B seed 11 at 50 mm from random initialization for exactly
19,200 local timesteps / 1,228,800 transitions with 64 environments and full
registered randomization. No v7 checkpoint is reused.
