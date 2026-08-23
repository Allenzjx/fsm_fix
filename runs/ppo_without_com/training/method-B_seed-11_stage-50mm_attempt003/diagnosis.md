# Method B seed-11 50 mm training attempt003 result

- Status: `COMPLETED`.
- Recovery source: attempt002 `checkpoints/agent_6400.pt`, SHA-256
  `e1779b119ac64879ffe87ac4bba6130a55345695bbcb7cc8fdd7a3f598e9e4a8`.
- Durable timesteps before recovery: 6,400.
- Timesteps completed in this run: 12,800.
- Audited cumulative timesteps: 19,200 requested and 19,200 completed.
- Audited cumulative transitions: 1,228,800 requested and 1,228,800
  completed across 64 parallel environments.
- Final checkpoint: `checkpoints/final_agent.pt`, SHA-256
  `0a72d1ae9da70d53d138a00eb440e917a94c2ce9946f0f4a55ef8ab0cb8a467d`.
  Its 77 stored tensors are finite.
- Final periodic checkpoint: `checkpoints/agent_12800.pt`, SHA-256
  `4f637dc04da83560a2c4ac151934229977ed350e750e14c4962c6815f2aac3cf`.
- Training-result SHA-256:
  `4fcbda0bf39d35a2b0f17f519d8bc4646548ef10b7cb1974c74c6440f7b6e557`.
- At the final update TensorBoard recorded finite values: mean instantaneous
  reward `0.586966932`, policy loss `0.004739156`, value loss
  `0.000154079`, policy standard deviation `0.133561522`, and adaptive
  learning rate `0.0002`.
- The two-run recovery chain does not count approximately 45
  post-checkpoint steps from the failed attempt002.

Training completion alone does not promote the curriculum. The deterministic
mean policy must next satisfy the registered 20-episode 50 mm development
gate.
