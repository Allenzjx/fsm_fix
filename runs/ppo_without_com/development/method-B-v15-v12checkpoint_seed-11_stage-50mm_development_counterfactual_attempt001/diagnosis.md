# Method-B v15 / v12-checkpoint 50 mm counterfactual attempt001

`EXECUTION_PASS`, `RETRAINING_EVIDENCE_FAIL`. All 20 fixed 50 mm
development scenarios completed with the exact v12 final checkpoint under
v15. The locked test manifest was not read.

- Success: `9/20`, exactly the same IDs as v14:
  `0000,0001,0002,0010,0011,0012,0013,0016,0019`.
- Failures: six `BODY_OR_LINK_COLLISION` and five `FSM_PHASE_TIMEOUT`, with
  the same scenario IDs as v14. All collision terminations identify
  `front_right_bot`.
- Delay groups remain delay 0 = `2/5`, delay 1 = `2/6`, delay 2 = `5/9`.

All 52,146 x 122 telemetry rows preserve exact phase gating, z-only masking,
front/rear signs, bilateral ties, and four-wheel balance. The action chain is
finite; 5,844 undefined values occur only in `margin_m`. Maximum absolute
policy, executed, and scaled values remain `0.3428333`, `0.0984901`, and
`0.000984901 m`.

V15 physically changed the phase-9 chain: across 4,725 time-aligned v14/v15
samples, mean absolute requested and final wheel-center delta was about
`0.060 mm`, and final servo delta was about `0.000635 rad`. Successful
phase-9 v15 samples averaged `0.428 mm` shared magnitude and timeout samples
averaged `0.332 mm`. Despite those real command changes, the complete
success/failure set and aggregate performance metrics are unchanged.
Phase-9 magnitude is therefore not the remaining bottleneck; v15 is not
authorized for retraining.

Before another action-space revision, pre-existing v12 intermediate
checkpoints will be screened under fixed v15 runtime semantics. The candidate
order is pre-registered from training-only TensorBoard evidence:

1. `agent_59200.pt`, highest checkpoint-window mean episode return;
2. `agent_64000.pt`, second-highest checkpoint-window mean;
3. `agent_75200.pt`, window containing the best individual episode return;
4. `best_agent.pt`, skrl's internal best (tensor-identical to
   `agent_70400.pt`).

Artifact SHA-256:

- `result.json`:
  `0f1b03c0bedcfff81b2ccde909bc514279f726fd2f235dc02ee4600d112a95f8`
- `episodes.jsonl`:
  `937f3c35210c5ee126cbc2b1aa91f4a9e00aa7db3fa6dffc9f903343afe33161`
- `status.json`:
  `fe8a0950e90ef8062e6620e111a130797c16bc45e1157e27c4724073c46275b7`
- `telemetry.csv`:
  `ee8a0ad5371318cbbdf60c4d1fa726ae38499e586e9f53275d0d68a046fded95`
- stdout:
  `d1b11a77aa2856acfa8d605db9ed230f9a8971c892258ee942e9a29f16060e7e`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
