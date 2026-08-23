# Residual RL design

## Actor

The actor receives 96 normalized values that are, in principle, measurable or
estimable on a physical robot:

- simulated-perception obstacle height, relative front distance, lateral
  offset, relative top height, validity, and age;
- FSM phase one-hot, phase progress, normalized elapsed time, reference wheel
  centers, and reference wheel speeds;
- projected gravity, roll/pitch, body angular/linear velocity, finite-difference
  IMU acceleration, and base height;
- normalized joint position/velocity, measured wheel speed, previous residual
  action, position tracking error, and joint-limit distance.

Exact simulated contact state, contact force, contact point, whole-body CoM,
support margin, exact geometry, and domain-randomization state are excluded
from the actor.

The Actor MLP is `96 -> 256 -> 256 -> 128 -> 12` with ELU activations and a
bounded `tanh` mean. Its final mean layer is initialized to exactly zero, so
the initial deterministic policy is the frozen FSM. The registered initial
Gaussian `log_std` is `-2.0`; the same model class is used for B, C, training,
checkpoint reload, and deterministic evaluation.

## Asymmetric critic

The critic receives the 96 actor values plus 50 privileged values:

- exact obstacle height and position;
- four-state contact one-hot values for each wheel;
- four ContactSensor force magnitudes;
- four 3-D wheel positions relative to the base;
- whole-body CoM-relative state and signed longitudinal margin validity/value;
- exact root velocity;
- friction, actuator-delay, and mass-scale parameters.

The DirectRLEnv advertises separate 96-D `policy` and 146-D `critic` spaces.
The skrl wrapper passes the latter through `env.state()` and the PPO value
model is constructed with the 146-D state space.

## Ablation

Method B and Method C share the same environment, actor, critic, PPO
hyperparameters, seeds, curriculum, residual bounds, and all reward weights.
Only `com_margin` changes:

- B: `0.0`
- C: `8.0`

The CoM term is active only when the margin is valid, the FSM is in a support
transfer phase, and forward progress is positive. It uses a capped positive
margin and a stronger signed negative-margin penalty, preventing a policy from
earning stability reward by waiting in front of the step.

Every environment step retains raw, scalar weight, weighted, and episode-sum
reward terms. `test_reward_ablation.py` verifies that B/C differ only in the
declared CoM term for an identical fixture.

Reward v3 keeps the v2 terminal success/collision scale and time-integrated
occupancy terms. After the v2 Method-B final policy failed all 20 development
episodes in late right-link collisions, v3 strengthens the common normalized
residual-magnitude penalty, adds a common left/right residual-asymmetry
penalty, and reduces the wheel-speed residual bound from 0.35 to 0.20 rad/s.
The symmetry term compares only residual corrections (front left versus front
right, rear left versus rear right); it does not penalize or alter the frozen
FSM reference itself. These changes are shared by B and C, whose only method
difference remains the CoM-margin weight.

Reward v4 follows a second registered development failure. V3 reduced
phase-8 action magnitude and collisions but reached only 2/20 versus the
frozen FSM's 12/20. V4 therefore treats baseline preservation as a safety
constraint: normalized residual magnitude/asymmetry weights become -2/-3 and
the x/z/wheel residual bounds become 7.5 mm, 10 mm and 0.10 rad/s. The action
dimension, policy network, FSM reference, success metrics, PPO budget, seeds,
and B/C-only CoM difference remain unchanged.

Reward v5 follows v4's 5/20 development result. V4 training used only the
single nominal scenario, and all nine development scenarios with two-step
actuator delay failed. V5 retains v4's residual bounds and safety
regularization but trains the 50 mm stage with bounded full variation in
initial distance/pitch, friction, 0--2 step delay, and sensor noise. It also
corrects two common reward-credit defects: stuck occupancy is integrated in
seconds instead of charged at 60 Hz, and phase progress is the non-negative
delta of the monotonic `fsm_phase + phase_progress` coordinate rather than a
phase-local value that drops at each transition. B and C receive these
identical fixes and continue to differ only in the CoM-margin weight.

Evaluation manifests also retain an `environment_seed` field as a paired
scenario identifier reserved for future environment-side stochasticity. The
current deterministic evaluator does not consume that field: the applied
scenario variation is exactly the explicit initial distance, initial pitch,
friction, actuator delay, and the fixed observation bias drawn from
`noise_seed`. Consequently, no result or report may describe
`environment_seed` as an applied physics-randomization seed.

Reward v6 follows an objective audit of the partial v5 training run. A
168-step unsafe termination received a return of -17.6176 while long-lived
episodes averaged -1486.234. V6 therefore integrates continuous state/rate
costs by the control `step_dt` and adds one-shot -200 terms for fall, numerical
failure, phase timeout, joint-limit termination, and body collision. Event
terms (progress deltas, success, impact, action change, and the intentional
per-step time cost) retain their discrete definitions. V6 changes no FSM,
metric, observation, action, network, PPO, randomization, seed, or B/C
ablation control.

Runtime v7 retains the complete v6 reward. It fixes a separate reset-state
defect found during v6 training: the old randomized reset combined a newly
written default root pose with link positions that could still be cached from
the terminal state. V7 caches settled standing root-to-wheel geometry once and
computes every randomized root pose directly from that cache, the asset
default root, environment origin, obstacle front, sampled distance/pitch, and
wheel radius. No current terminal root or link pose participates in reset
placement.

Runtime v8 follows v7's 2/20 development gate. V7 retained none of the frozen
FSM's 12 successful scenarios, and all nine global timeouts stopped in phase
10 with the rear-right wheel not fully on top. Physical residual execution is
therefore enabled only during FSM phases 2--9; approach and phase-10 terminal
settling use the exact frozen FSM command. The time-integrated residual
magnitude/asymmetry weights become -120/-180 per second, which is exactly the
prior v4 -2/-3 per-control-step strength at 60 Hz. This restores baseline
anchoring without reverting the corrected timebase. A local `AuditablePPO`
subclass also repairs only skrl 2.0's rolling display accumulators after each
unmodified PPO memory write. It does not alter rollout memory, GAE, losses, or
parameter updates.

Runtime v9 follows v8's valid but non-promotable 10/20 development gate. V8
retained eight frozen-FSM successes and rescued two failures, but no episode
failed before phase 8, and its remaining terminal failures were three phase-9
timeouts plus four phase-10 timeouts with strict top flags `1110`. Phase-9
policy corrections were systematic. V9 consequently narrows physical
residual execution to phases 7--8 only: the frozen FSM exclusively controls
the failure-free approach in phases 0--6 and terminal placement/settling in
phases 9--12. Policy outputs remain observable and regularized outside the
window. Reward, action bounds, architecture, PPO, budget, and randomization
are unchanged.

Runtime v10 follows v9's 6/20 gate, which included eight front-right
lower-link collisions. V9 used positive front wheel-center z residuals and
weak rear lift, opposite the vertical pattern in safer v8 phase-8 successes.
V10 projects delayed, phase-enabled physical actions into a vertical
direction cone: both front z residuals are non-positive and both rear z
residuals are non-negative. Raw 12-D policy outputs remain observable and
regularized, and telemetry records the projected applied action separately.

A direct correction to the v8/v9 diagnosis found that frozen-FSM successes
also take 133--134 seconds. The prior 19,200-step medium runs therefore
provided only about 2.1 full episode horizons per environment. V10 registers
76,800 local steps per stage, about 8.5 horizons, as the full-development
budget. B and C use the identical budget.

Runtime v11 follows v10's 2/20 gate, which included ten collisions and nine
phase-8 `front_right_bot` events. V10's policy means occupied the rejected
front-up/rear-down z half-space, so the clamp mapped many distinct actions to
the same near-zero vertical correction. PPO instead used unrestricted x and
wheel-speed channels; collision rows carried about -0.36 mm front-right x,
whereas v8 successful rows carried about +0.2 mm.

V11 narrows physical residual authority without changing the 12-D actor. In
phases 7--8, only wheel-center z channels execute: front z is `-abs(raw)` and
rear z is `+abs(raw)`. All wheel-center x and wheel-speed residuals are masked
to exact zero. All 12 raw outputs remain in observations, telemetry, action
rate, magnitude, and asymmetry regularization. Outside phases 7--8 the exact
frozen FSM still executes. This signed-magnitude map folds both raw
half-spaces into the registered safe direction; it is an exploration and
authority-allocation change, not a claim that PPO differentiates through the
simulator.

Runtime v12 follows v11's 6/20 gate, whose ten failures in phase 8 were all
`front_right_bot` collisions. Although the z-only mask and signs were exact,
the final policy lifted the rear-right wheel center by about 0.52 mm versus
0.22 mm at the rear-left in collision rows. The soft raw-action asymmetry
cost did not guarantee physical symmetry after the absolute-value map.

V12 therefore ties bilateral physical magnitudes: both front z channels use
the negative mean absolute front raw z magnitude, and both rear z channels
use the positive mean absolute rear raw z magnitude. X and wheel-speed
residuals remain exactly zero. This removes residual-induced roll authority
while preserving separate front/rear vertical correction, the 12-D actor,
raw-action observation/regularization, phase window, rewards, PPO,
randomization, and B/C-only CoM ablation.

Runtime v13 follows v12's exact 76,800-step training and 7/20 gate. V12
removed left/right imbalance, but successful phase-8 rows learned about
0.123 mm front down versus 0.650 mm rear up. This approximately 1:5 ratio
regressed from the 9/20 v11-checkpoint/v12-projection counterfactual, whose
successful means were about 0.294 mm front down and 0.318 mm rear up.

V13 removes this last relative-magnitude degree of freedom. All four raw z
channels contribute to one shared mean absolute magnitude; both front
channels execute its negative value and both rear channels execute its
positive value. X and wheel-speed residuals remain exactly zero. The change
preserves the 12-D actor, raw-action observation and regularization, phase
window, bounds, rewards, PPO, randomization, seeds, and B/C-only CoM
ablation. A real-Isaac smoke and a development-only counterfactual with the
v12 final checkpoint are required before any v13 retraining.

The v13/v12-checkpoint counterfactual reached 8/20 versus 7/20 with v12
semantics. It reduced `front_right_bot` collisions from seven to six and
global timeouts from three to one, but produced five FSM phase timeouts. The
paired +1 gain does not justify v13 retraining.

Runtime v14 retains v13's exact four-wheel shared signed-magnitude projection
and changes only its execution window from phases 7--8 to phases 7--9. Raw
actions remain observable and regularized in every phase; phases 0--6 and
10--12 retain exact frozen-FSM physical authority. Bounds, rewards, network,
PPO, randomization, seeds, budget, and B/C-only CoM ablation are unchanged.
A real-Isaac phase-gate smoke and a development-only v12-checkpoint
counterfactual are required before any v14 retraining.

The v14/v12-checkpoint counterfactual reached 9/20. It converted only one
v13 global timeout to success; all six collisions and five phase timeouts
were unchanged. Successful phase-9 episodes averaged about 0.286 mm shared
physical magnitude, while the timeout group averaged about 0.223 mm and
ended with the same diagonal full-wheel flags.

Runtime v15 retains v14's projection and phases 7--9 window. Its aligned
normalized-action gains are `[1.0,1.0,1.5]`, so only phase 9 is multiplied
by 1.5 before clamping to `[-1,1]` and applying the unchanged 10 mm z bound.
Zero input remains exact zero; signs, z-only masking, bilateral ties, and
four-wheel balance are invariant. Rewards, actor/PPO, randomization, seeds,
budget, and the B/C-only CoM difference are unchanged. A real-Isaac gain and
bounds smoke plus a development-only same-checkpoint counterfactual are
required before any v15 retraining.

## Curriculum and randomization

For each seed, both methods use the same checkpoint chain:

1. 50 mm with the registered full bounded randomization;
2. 75 mm with light randomization;
3. 100 mm with the registered full bounded randomization.

Each stage runs the complete 20-scenario development height split before
promotion. The pre-registered minimum success rates are 0.80, 0.75, and 0.70.
The promotion checker also verifies the method, height, episode count, and
checkpoint SHA256; reaching a training iteration count alone cannot promote a
stage.

Randomization is sampled on every reset from the training-only config using a
deterministic function of training seed, environment ID, and episode index.
The full bounds are initial distance ±25 mm, initial pitch ±0.020 rad,
friction 0.90–1.20, command latency 0–2 control steps, and sensor-noise
standard deviation 0–0.005. The validation and locked-test manifests provide
their own fixed scenario values and do not enable this training hook.

## Checkpoint selection

Training checkpoints are evaluated only on the validation manifest. The
selection rule is lexicographic after safety and minimum-success eligibility:

1. larger mean episode-minimum signed longitudinal support margin;
2. lower support-transfer pitch-rate RMS;
3. lower slip distance;
4. lower residual saturation rate.

The locked-test manifest is not available to training or checkpoint selection.
