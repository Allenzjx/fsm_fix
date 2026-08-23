# Pre-locked environment-seed semantics audit

## Status

`PASS_WITH_DISCLOSURE_BEFORE_METHOD_FREEZE`.

The locked-test manifest was not opened, hashed, enumerated, or otherwise
read during this audit.

## Finding

`scenario_manifest.py` generates both `environment_seed` and `noise_seed`.
The evaluator copies the complete scenario row into `episodes.jsonl`, so the
former is preserved as a paired scenario identifier. However,
`evaluate_controller.py` does not consume `environment_seed` to seed a
per-environment simulator-side random process.

The current evaluator applies these manifest-defined variations:

- initial wheel-to-obstacle distance;
- initial base pitch;
- contact friction;
- actuator delay in control steps; and
- a deterministic fixed observation bias generated from `noise_seed` and
  `sensor_noise_std`.

The Isaac environment is otherwise evaluated deterministically under the
manifest-level seed. Therefore `environment_seed` is a reserved field, not an
applied physical-randomization input.

## Decision

No evaluator, manifest, checkpoint, reward, FSM, metric, or experimental
definition is changed. This avoids silently adding a new stochastic factor
after formal training registration. The field's real semantics are disclosed
in `docs/rl_design.md`, and downstream claims must not call it an applied
physics-randomization seed.

This does not impair paired comparison: FSM, B, and C receive the same
explicit scenario rows and fixed observation biases. It does narrow the
allowed robustness claim to the variations actually applied above.

## Evidence hashes

- `src/resume_validation/evaluate_controller.py`:
  `c082f724b957105129de7664d0cf869919e93cc95179c8657577f69baff984e4`
- `src/resume_validation/scenario_manifest.py`:
  `30dc4ef57db75498eda03f469be610413e20d4dbcf556aa653792dd4f0c18a91`
