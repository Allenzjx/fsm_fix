# Method B reward-v4 seed-11 50 mm training attempt001

- Status: `COMPLETED`.
- Initialization: random; no v1, v2, or v3 checkpoint was reused.
- Training scale: 64 parallel environments, 300 iterations, 64-step
  rollouts, 5 learning epochs and 8 mini-batches.
- Audited timesteps: 19,200 requested and 19,200 completed.
- Audited transitions: 1,228,800 requested and 1,228,800 completed.
- Final checkpoint: `checkpoints/final_agent.pt`, SHA-256
  `e23b091a4a3f05b2092963a3960df7b1a2539a3e62072cb095b375e8587b87f0`.
  Its 77 stored tensors (785,093 elements) are finite.
- Direct effective residual bounds are 0.0075 m x, 0.010 m z and 0.10 rad/s
  wheel speed. Normalized residual-magnitude and left/right-asymmetry weights
  are -2.0 and -3.0.
- Training-result SHA-256:
  `5876b3c45914bc492955b5599eadcfe758a674c14ffb1d8004cd1a5af9140150`.
- TensorBoard event SHA-256:
  `4c98922a1f7bfc71274a34f833e531959ac4e57ed2b3da615121cf680db3234a`.
- All scalar events are finite. Each core training scalar has exactly 300
  updates and terminates at timestep 19,200. At the final update TensorBoard
  recorded mean instantaneous reward `-0.134030506`, policy loss
  `0.000141890`, value loss `0.003282695`, policy standard deviation
  `0.103434622`, and adaptive learning rate `0.000200000`.
- The final periodic checkpoint and `final_agent.pt` are distinct save points.
  The evaluator must use the final checkpoint path and hash recorded by
  `training_result.json`.

Training completion alone does not promote the curriculum. The deterministic
mean final policy must pass an evaluator/provenance smoke and the registered
20-episode 50 mm development gate.
