# Method B reward-v2 seed-11 50 mm training attempt001

- Status: `COMPLETED`.
- Initialization: random; no reward-v1 checkpoint was reused.
- Training scale: 64 parallel environments, 300 iterations, 64-step
  rollouts, 5 learning epochs and 8 mini-batches.
- Audited timesteps: 19,200 requested and 19,200 completed.
- Audited transitions: 1,228,800 requested and 1,228,800 completed.
- Final checkpoint: `checkpoints/final_agent.pt`, SHA-256
  `c02026df0f913c6761e1354f6026928421896d5e570dd1e1c848ce13852d8706`.
  Its 77 stored tensors (785,093 elements) are finite.
- Final periodic checkpoint: `checkpoints/agent_19200.pt`.
- Training-result SHA-256:
  `7515dc38b48462ca437d17dbad7d701f2b477c075d8f38a32088da4f339afae8`.
- TensorBoard event SHA-256:
  `a747f79abcd6785de50d660a19faa4627a60b76f65ea3ac0a12cce33de395107`.
- At the final update TensorBoard recorded finite values: mean instantaneous
  reward `-0.037766565`, policy loss `-0.008938177`, value loss
  `0.000357935`, policy standard deviation `0.133027062`, and adaptive
  learning rate `0.0000592593`.
- The reward-v2 stream included terminal-scale collision samples (for example
  an instantaneous minimum near `-200.15` at step 13,056), confirming that
  terminal safety is no longer hidden by per-step occupancy rewards.

Training completion alone does not promote the curriculum. The deterministic
mean final policy must next pass a one-scenario telemetry smoke and the
registered 20-episode 50 mm development gate.
