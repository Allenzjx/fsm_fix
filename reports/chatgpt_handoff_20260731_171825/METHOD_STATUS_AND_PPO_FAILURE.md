# Method status and PPO failure analysis

## Bottom line

- Frozen FSM development performance: 50 mm 12/20 (60%), 75 mm 7/20 (35%), 100 mm 7/20 (35%).
- Method B is the **without-CoM ablation** (`com_margin=0.0`). All 9 v34 seed×height trainings completed and all 9 final checkpoints were evaluated on 20 development scenarios, but **0/9 gates promoted**.
- Method C (`com_margin=8.0`) has started: seed 11 / 50 mm is `RUNNING` and intermediate checkpoints exist. It has no completed development result at the audit cutoff, so its performance cannot yet be evaluated.
- There is no validation run, no method freeze, and no locked test. A formal FSM-vs-PPO or B-vs-C comparison therefore does not exist.
- The observed Method B final policies largely reproduce the frozen FSM outcome pattern. The principal mechanism is a narrow phase/IMU execution gate plus action projection and strong penalties on **raw** actions, which makes the executed residual effectively zero in the inspected final evaluations.

## Method B v34 completion matrix

| Method | Seed | Height mm | Training | Development | Rate | Threshold | Promote | Gate checkpoint |
|---|---:|---:|---|---:|---:|---:|---|---|
| B | 11 | 50 | COMPLETED | 13/20 | 0.6500000357627869 | 0.8 | False | final_agent.pt |
| B | 11 | 75 | COMPLETED | 7/20 | 0.3499999940395355 | 0.75 | False | final_agent.pt |
| B | 11 | 100 | COMPLETED | 7/20 | 0.3499999940395355 | 0.7 | False | final_agent.pt |
| B | 29 | 50 | COMPLETED | 13/20 | 0.6500000357627869 | 0.8 | False | final_agent.pt |
| B | 29 | 75 | COMPLETED | 7/20 | 0.3499999940395355 | 0.75 | False | final_agent.pt |
| B | 29 | 100 | COMPLETED | 7/20 | 0.3499999940395355 | 0.7 | False | final_agent.pt |
| B | 47 | 50 | COMPLETED | 13/20 | 0.6500000357627869 | 0.8 | False | final_agent.pt |
| B | 47 | 75 | COMPLETED | 7/20 | 0.3499999940395355 | 0.75 | False | final_agent.pt |
| B | 47 | 100 | COMPLETED | 7/20 | 0.3499999940395355 | 0.7 | False | final_agent.pt |

## What “best” and “final” mean

`best_agent.pt` is selected inside installed skrl by the highest tracked `Reward / Total reward (mean)` at checkpoint intervals. It is not selected by development success, collision rate, CoM margin, or the frozen checkpoint-selection rule. `final_agent.pt` is explicitly saved after the final training update. Every development gate in the current curriculum loads `final_agent.pt`.

## Resume semantics

Cross-height warm starts call `agent.load(...)` with `resume_offset_timesteps=0`. Zero here means “start a new height-stage budget at local timestep zero,” not “load policy weights only.” Canonical checkpoint dictionaries contain policy, value, optimizer, observation preprocessor, state preprocessor, and value preprocessor. The policy state includes `log_std_parameter`. The KL-adaptive scheduler is constructed anew and is not registered in skrl’s checkpoint modules, so scheduler state resets across stages.

## Why PPO did not meet expectations

1. The reference itself is weak: FSM is only 60%/35%/35% on development at 50/75/100 mm.
2. v34 permits physical residual execution only in phases 8–10 and only after IMU hazard gates; it then projects 12 raw channels into a very constrained shared correction. All wheel-center x channels are masked.
3. Training penalizes raw action magnitude and left/right asymmetry even in steps where gating prevents any physical residual. This creates a direct incentive to output near zero.
4. Entropy bonus is zero and the Gaussian log standard deviation is constrained to [-5,-4], so exploration is deliberately narrow.
5. Method B has no CoM reward. Its result cannot answer whether the planned CoM-guided Method C improves support margin or pitch stability.
6. Training logs contain no success rate, phase occupancy, KL, entropy, explained variance, clip fraction, gradient norm, reward-component return, executed residual norm, or saturation fraction. This blocks several causal claims.

## Orchestration failure is separate from policy failure

After the final Method B gate completed, earlier `formal_training_recovery_supervisor.ps1` / `full_pipeline_supervisor.ps1` attempts recorded `FAILED` with an empty wrapper exit-code message. A later supervisor attempt proceeded to Method C. Therefore `promote=False` did not block Method C; the empty-exit-code failures were transient orchestration defects and are separate from policy quality. At this audit cutoff the live Method C process is externally owned and must not be interrupted.
