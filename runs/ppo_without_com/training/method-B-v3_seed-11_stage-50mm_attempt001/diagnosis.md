# Method B reward-v3 seed-11 50 mm training attempt001

- Status: `COMPLETED`.
- Initialization: random; no v1 or v2 checkpoint was reused.
- Training scale: 64 parallel environments, 300 iterations, 64-step
  rollouts, 5 learning epochs and 8 mini-batches.
- Audited timesteps: 19,200 requested and 19,200 completed.
- Audited transitions: 1,228,800 requested and 1,228,800 completed.
- Final checkpoint: `checkpoints/final_agent.pt`, SHA-256
  `d3509ab1dbebc658cefdbf00aef77766e4ec574263c5c8c99ca3dfef1ad62a2e`.
  Its 77 stored tensors (785,093 elements) are finite.
- Direct effective residual bounds are 0.015 m x, 0.020 m z and 0.20 rad/s
  wheel speed.
- Training-result SHA-256:
  `35825378ae5bb35ce2f1988bf97997e6ad85a14fa69f8e1f051d45b39042a0e1`.
- TensorBoard event SHA-256:
  `48c63326f66e7f9717fcf37a6ae125d79a59e822e14e6d4ec6a50a9f1cc3ad00`.
- At the final update TensorBoard recorded finite values: mean instantaneous
  reward `-0.088295378`, mean completed-episode reward `-731.880981`,
  policy loss `-0.008480979`, value loss `0.000351825`, policy standard
  deviation `0.120307535`, and adaptive learning rate `0.000133333`.

Training completion alone does not promote the curriculum. The deterministic
mean final policy must pass an evaluator/provenance smoke and the registered
20-episode 50 mm development gate.
