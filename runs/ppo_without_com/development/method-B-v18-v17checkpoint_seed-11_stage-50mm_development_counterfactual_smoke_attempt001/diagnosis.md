# Method-B v18 / v17-checkpoint deterministic restore smoke attempt001

`RESTORE_PASS`, `CONSTRAINT_PASS`, `PERFORMANCE_EXCLUDED`.

- The unchanged v17 final checkpoint restored with SHA-256
  `e29c94d54a12e895c8a8e3ba1c2aea726df3b5559d5ce693dbc09ac439f5a102`.
- The deliberate one-scenario five-second timeout produced exactly
  `100 x 122` fully finite telemetry.
- Maximum absolute deterministic policy action was `0.08164108`. Phases
  0/1 produced exact zero executed and scaled physical residuals.
- The telemetry is byte-identical to the v17 restore smoke because this
  short scenario did not enter the phase-7--9 execution window. This
  confirms checkpoint/model restoration and excluded-phase equivalence,
  but does not claim confidence-gate performance.
- Provenance records the v18 common config, confidence projection and exact
  threshold, v18 evaluator/safety/environment sources, and frozen
  asset/FSM/metrics hashes. Environment Python PID `156268` exited
  naturally.

Artifact SHA-256: result
`ce309d690fd488296b0d061f3e2584b48dfbbd96a26fff794f8e5dded280c47f`,
episodes
`3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
status
`4082371a90c4e6b798b215acb3d30629fe8a392d49a9c708f28456eb417e2647`,
telemetry
`cff4b69b6653858982baa724a0b00c59c7b853d0d85dc96e52b96c8de012cea7`,
stdout
`989d39b3f0fd8ae86359dd3f0baf1d4319e4e075849d5a3931f3bdf40c517c05`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: execute the pre-registered v18 counterfactual on all 20 fixed 50 mm
development scenarios.
