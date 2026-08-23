# Method B seed-11 50 mm partial-reset smoke attempt050 result

- Status: `SMOKE_PASS`.
- Real IsaacLab preflight: 16 parallel environments at 50 mm with nominal
  randomization.
- The smoke explicitly reset exactly two environments (`0` and `15`) after
  the zero-residual rollout. The partial reset completed without a shape
  error and both selected root poses were finite.
- Actor observations, privileged Critic states and values, policy actions,
  contacts, and zero-residual FSM equivalence all remained finite/valid.
- Training-result SHA-256:
  `a0b3e8b15a3cbbd1a934c35ed313a9d54d4a772b5b3b4b5409bf95a6d2827d90`.

This smoke run contributes zero training transitions. It authorizes recovery
from attempt002's finite, hashed 6,400-step checkpoint.
