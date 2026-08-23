# V29 phase-selective floor smoke audit amendment

## Status

`REGISTERED_BEFORE_ATTEMPT002`.

Attempt001 established the registered runtime behavior but exposed a
preflight coverage gap: high-drive projection was checked in every phase,
while minimum-floor physical realization was checked only in phase 8.

The training entrypoint now executes a sub-floor positive actor probe
under the real positive-roll gate independently in phases 8, 9, and 10.
For every phase it records and requires:

- exact applied deficient-diagonal floor;
- exact requested wheel-center z delta;
- final-target agreement within `1e-7 m`;
- all four IK legs valid;
- zero IK-invalid counter increment.

No runtime action path, configuration, gate, checkpoint, reward,
optimizer, randomization, curriculum, budget, manifest, or acceptance
criterion changes. `residual_rl_env.py`, `residual_safety.py`,
`evaluate_controller.py`, and the common configuration remain at their
v29 registered hashes.

Compilation and all 160 tests pass.

## Hash change

- `train_residual_ppo.py` attempt001:
  `c6469a6efed3116184e3ae2ee15d34bb8a1902146d45613d1bc720c3692ace47`
- `train_residual_ppo.py` attempt002:
  `99b2aba77d5109bc015fa574780ff46df367fbb48ef87f237226827bfe70c92b`

No attempt002 Isaac result exists at amendment time.
