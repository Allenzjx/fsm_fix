# Method-B v12 seed-11 50 mm development gate attempt001

`FAIL_PROMOTION`. The exact final checkpoint completed all 20 deterministic
development scenarios under environment Python PID `134124`, but achieved
only `7/20` successes (`35%`) versus the frozen eligibility requirement of
`16/20`.

- Successes: `0000`, `0001`, `0010`, `0011`, `0015`, `0016`, `0019`.
- Failures: seven `BODY_OR_LINK_COLLISION`, three `FSM_PHASE_TIMEOUT`, and
  three `TIMEOUT`.
- Every collision was on `front_right_bot`.
- Delay groups (success/total): delay 0 = `1/5`, delay 1 = `1/6`, delay 2 =
  `5/9`.
- Relative to the v11 final gate (`6/20`), v12 retained three successes,
  gained four, and lost three.
- Relative to the v11-checkpoint/v12-projection counterfactual (`9/20`), the
  freshly trained v12 policy retained five successes, gained two, and lost
  four.

The 51,746 x 122 telemetry table contains no non-finite action-chain value.
Its 5,843 non-finite values occur only in `margin_m`, where support margin is
undefined and episode records separately count valid/invalid samples. Phase
gating, z-only masking, front-negative/rear-positive signs, and bilateral ties
hold exactly on every row.

Maximum absolute policy action, projected action, and scaled wheel-center
residual were `0.3412165`, `0.1685281`, and `0.00168528 m`. In phase 8,
successful trajectories averaged scaled z residuals
`[-0.00012316, -0.00012316, +0.00064973, +0.00064973] m`. The comparable
v11-checkpoint/v12 counterfactual success mean was approximately
`[-0.00029373, -0.00029373, +0.00031839, +0.00031839] m`. Training therefore
preserved bilateral symmetry but learned a roughly 1:5 front/rear magnitude
ratio and regressed from 9/20 to 7/20.

Artifact SHA-256:

- `result.json`:
  `53354bfd26da1140406ae16babb7435e3f3548aa825558f72376bf8c8caa3487`
- `episodes.jsonl`:
  `bab9635275ee91dd36f2dc1f4f7167f894ffb921c2814b6219058f130854fe84`
- `status.json`:
  `ccbb905818abd8a7b62937ea34e2c5c0463190bfb8768580094b2fa33697ec7b`
- `telemetry.csv`:
  `6ad03f988bebf8108e8f523fa22d9326fba52afeab044563bf8266f59184f253`
- stdout:
  `aadad388a5cd5f970745599ea9f05e3481ab356655935db05795bb5e65139766`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Provenance exactly matches final checkpoint
`a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`,
v12 common config
`f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`,
the frozen FSM/metrics/asset hashes, and development manifest
`f3d10d7340c06f78c200c44119bb2e17c81e587bd314b342ac90b49019ea2cdc`.

Next: register runtime v13 with one shared absolute z magnitude across all
four wheels, applied negative at the front and positive at the rear. This
removes the observed front/rear ratio degree of freedom while retaining the
same 12-D policy, bounds, phase window, reward, PPO, randomization, and
training budget. Require real-Isaac smoke and a development-only
counterfactual with the v12 final checkpoint before any retraining.
