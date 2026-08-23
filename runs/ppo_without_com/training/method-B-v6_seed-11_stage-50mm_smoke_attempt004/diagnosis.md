# Method-B reward-v6 seed-11 50 mm smoke attempt004 diagnosis

## Disposition

`FAIL_TARGET_PREDICATE_NOT_REACHED`. The diagnostic serialization closed
attempt003's evidence gap:

- returned termination: `true`
- total terminal reward: `-200.00990295410156`
- total reward finite: `true`
- raw/weighted fall term: `0.0 / 0.0`
- terminal fall snapshot: `false`

Lowering the root to 0.01 m caused real non-wheel contact/body collision before
the root-height fall predicate became true. Thus attempt004 successfully
exercised and numerically confirmed the -200 body-collision safety path, but it
did not test the requested fall term and correctly failed the narrow
assertion.

Attempt005 changes only the smoke-only stimulus: lift the selected robot
0.25 m and set a 1.4 rad roll quaternion, above the frozen fall-tilt threshold,
so the fall predicate is isolated from ground collision. The training
environment, reward, and all experiment controls are unchanged. Attempt004
result SHA-256 is
`7cd5ac10f48e8b224f7fb8b9c915190f5b9be3d8176e1d70888305130e8b6b53`;
event SHA-256 is
`98484e389a7833378ee08d2e3eb1ce1cb0778c93472fe02bb6fe8bde415f5676`.
