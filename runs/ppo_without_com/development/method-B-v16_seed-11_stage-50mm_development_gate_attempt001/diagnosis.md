# Method-B v16 seed-11 final-checkpoint development gate attempt001

`EXECUTION_PASS`, `CONSTRAINT_PASS`, `PROMOTION_FAIL`.

- Success: `8/20`
  (`0001,0002,0010,0011,0012,0014,0016,0018`).
- Failures: eight `front_right_bot` body/link collisions
  (`0003,0004,0005,0006,0008,0009,0013,0019`), three phase-9
  `FSM_PHASE_TIMEOUT` results (`0007,0015,0017`), and one phase-10 global
  `TIMEOUT` (`0000`).
- Relative to the frozen FSM result (`12/20`), the checkpoint rescued no
  baseline failure and lost baseline-success scenarios
  `0000,0004,0007,0015`. It therefore fails the pre-registered `16/20`
  promotion threshold.
- Development-only all-episode mean minimum margin changed from the FSM's
  `-0.2810707 m` to `-0.2417523 m` (`+39.3184 mm`), while mean pitch-rate
  RMS changed from `0.0615402` to `0.0622841 rad/s` (`1.209%` worse).
  These are diagnostic development values, not locked-test claims.

All `50,598 x 122` telemetry rows have uniform width. The only non-finite
values are 5,854 geometrically undefined `margin_m` samples. The complete
policy/action/target chain is finite and preserves:

- exact physical zero outside phases 7--9;
- exact z-only action and zero wheel-speed residual;
- exact four-wheel front-negative/rear-positive balance;
- exact `0.01 m` physical scaling.

Maximum absolute policy/executed/scaled wheel-center values are
`0.3845858`, `0.2126572`, and `0.002126572 m`. The deterministic gate is
exactly off for 10,605 of 14,794 execution-window rows (`71.6845%`).

The learned policy did not acquire a useful deterministic gate separator.
Its four active z standard deviations are about `0.0692--0.0708`, giving
the shared signed drive a training-time standard deviation of `0.03503`.
Although deterministic mean drives are predominantly negative/off, the
estimated stochastic on-probability remains about `38.4--41.3%` across
success, collision, phase-timeout, and global-timeout groups. This is
consistent with a train/evaluation mismatch in which exploration noise
activates the one-sided gate during PPO rollouts but the required
deterministic mean action does not conditionally separate outcomes.

Artifact SHA-256:

- result:
  `c363bd419bf2c9ac730be6aabc229c09e2f0ad96324ae38386b320052a32d136`
- episodes:
  `d99d19c3d2eb243dc5a973df5e09c6c5cbac87912902beb0bfe9c7021865c421`
- status:
  `ef6425a3ff93cf48f8341854d63729977713795cd03502bb8efead1ace40d74e`
- telemetry:
  `ffc1495c9094f4a9bcaab96f42461d13b07a53f185acf45fee99190ef6ae271c`
- stdout:
  `f822311e7ba17cfac6bd3d45f62fb68c1d49d4d150cb25e904e796e17b66e028`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: execute the separately pre-registered training-only intermediate
checkpoint screen. If none reaches 16/20, reject v16 and address the
stochastic-gate/deterministic-evaluation mismatch in a new numbered method.
