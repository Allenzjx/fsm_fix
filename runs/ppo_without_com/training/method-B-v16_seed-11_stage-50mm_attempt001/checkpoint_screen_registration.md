# V16 intermediate-checkpoint screen registration

This ordering was frozen after the explicit `final_agent.pt` development
gate failed at 8/20 and before any v16 intermediate checkpoint was evaluated.
It uses training-only TensorBoard data; no validation or locked-test result
was read.

## Ranking rule

For every periodic checkpoint, compute the arithmetic mean of all
`Reward / Total reward (mean)` samples whose steps are in
`(checkpoint_step - 1600, checkpoint_step]`. The 1,600-step window is exactly
one periodic checkpoint interval. Rank descending, exclude the already
evaluated `final_agent.pt`, and retain the first four distinct policy states.

The fixed evaluation order is:

1. `agent_60800.pt`: window mean `-235.333754`, 10 samples,
   SHA-256
   `6ca99caaf950954c7ddcae72801c7333c43d47a96026cbfbac7a70ee2a32d458`.
2. `agent_72000.pt`: window mean `-275.729911`, 12 samples,
   SHA-256
   `65f1a8ae2d06bab95ba08b9e7fa6078a4520d53856421a4783a5708f6c626e1d`.
3. `best_agent.pt` / tensor-identical `agent_76800.pt`: window mean
   `-290.034969`, 12 samples. The evaluated file is `best_agent.pt`,
   SHA-256
   `47666f48aa45db334b9050c88be407f667453f3d2ea9bc9b9ecebbcb0e91e0ea`.
4. `agent_57600.pt`: window mean `-313.477065`, 12 samples,
   SHA-256
   `f90d4b0ceb33f49e53bb3ba5ea2539f117b174c0f75688077542ba56874e024e`.

Each candidate contains 77 tensors / 785,093 elements, all finite. Each is
first subjected to a one-scenario five-second deterministic restore smoke,
then the unchanged 20-scenario 50 mm development gate. The order cannot be
changed based on observed development results. Screening stops only if a
candidate reaches the frozen 16/20 eligibility threshold; otherwise all four
candidates are retained and reported.

Training event SHA-256:
`637492a66f7b3d88c77c3b3329c84c66bfa90bef0f321f5ae810b8bad8e73d52`.
Training result SHA-256:
`05262a3915a9a9ee858e12366099d03dd6d8360c7292f2f547cc46263a7ce951`.
