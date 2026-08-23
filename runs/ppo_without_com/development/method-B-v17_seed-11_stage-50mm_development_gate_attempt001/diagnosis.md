# Method-B v17 seed-11 final-checkpoint development gate attempt001

`EXECUTION_PASS`, `CONSTRAINT_PASS`, `PROMOTION_FAIL`.

- Success: `6/20`
  (`0002,0004,0010,0011,0013,0015`).
- Failures: seven `BODY_OR_LINK_COLLISION` episodes
  (`0001,0003,0008,0009,0012,0018,0019`), four `FSM_PHASE_TIMEOUT`
  episodes (`0005,0006,0016,0017`), and three `TIMEOUT` episodes
  (`0000,0007,0014`).
- Relative to the frozen FSM's 12/20, v17 retains five successes
  (`0002,0004,0010,0011,0015`), rescues `0013`, and loses seven frozen-FSM
  successes (`0000,0001,0007,0012,0014,0016,0018`).
- Development-only mean minimum margin changes from the FSM's
  `-0.2810707 m` to `-0.1525892 m` (`+128.482 mm`), while mean pitch-rate
  RMS changes from `0.0615402` to `0.0618396 rad/s` (`0.4865%` worse).
  These are diagnostic development values, not locked-test claims.

All `52,354 x 122` telemetry rows have uniform width. The only non-finite
values are 5,840 geometrically undefined `margin_m` samples. Every other
numeric value is finite and the action chain preserves:

- exact physical zero outside phases 7--9;
- exact z-only authority and zero wheel-speed residual;
- exact front/rear bilateral ties and four-wheel balance;
- exact configured physical scaling.

Maximum absolute policy/executed/scaled z values are `0.1787840`,
`0.0751510`, and `0.000751510 m`. The deterministic physical gate is off in
only `1,698/15,807 = 10.7421%` of execution-window rows, versus 71.6845%
for the v16 final checkpoint.

V17 therefore resolves v16's stochastic-rollout versus deterministic-off
mismatch but over-corrects: the deterministic gate is nearly always on and
does not conditionally separate safe from unsafe states. Its learned drive
is nevertheless strongly phase-separated: medians are 0.026666 in phase 7,
0.010053 in phase 8, and 0.007851 in phase 9. A confidence threshold equal
to two registered shared-drive standard deviations,
`2 * exp(-4) / 2 = exp(-4) = 0.0183156`, is analytically defined before any
new runtime evaluation. On the recorded v17 actions it would retain 90.10%
of phase-7 rows while turning off 98.46% of phase-8 and 94.19% of phase-9
rows. This authorizes a separately numbered v18 runtime counterfactual with
the unchanged v17 checkpoint before any retraining.

Artifact SHA-256: result
`85dc0198685db052f2bea2c1a81307a87867b1b9cc7abf2824a0fcf720e25f42`,
episodes
`d75f4b038a9f74c355ceff43283771fbb4a7c7704579bb698a5cb53491b17e5b`,
status
`ae416c0ed269477befe9dd819db7037b65852dd3cfd82c1f9da9066327eb7bf4`,
telemetry
`169c50dae2efa49ec978bae33aa0ba03bfa26b059d7f277839eceaa16de03f44`,
stdout
`7527d3a3c2087e8e4a9f6f28fd6e3d3c16813cbfb4c7ea7f43a0d3619d6207d4`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: reject v17 as a trained method; register and implement v18
two-sigma confidence gating, then require real-Isaac smoke and a full
development-only checkpoint counterfactual before deciding whether
retraining is justified.
