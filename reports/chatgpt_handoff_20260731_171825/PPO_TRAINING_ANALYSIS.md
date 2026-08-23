# PPO training-curve and learning-quality audit

TensorBoard was found for all 9 canonical Method B v34 seed×height runs. Available scalar tags are:

- Episode / Total timesteps (max)
- Episode / Total timesteps (mean)
- Episode / Total timesteps (min)
- Learning / Learning rate
- Loss / Policy loss
- Loss / Value loss
- Policy / Standard deviation
- Reward / Instantaneous reward (max)
- Reward / Instantaneous reward (mean)
- Reward / Instantaneous reward (min)
- Reward / Total reward (max)
- Reward / Total reward (mean)
- Reward / Total reward (min)
- Stats / Algorithm update time (ms)
- Stats / Env stepping time (ms)
- Stats / Inference time (ms)

Missing instrumentation: success rate, reward components, entropy, KL, explained variance, clip fraction, gradient norm, residual norm, saturation fraction.

The curves support only statements about tracked return, episode length, policy/value loss, standard deviation, and adaptive learning rate. They do not prove task learning. In particular, a longer mean episode can be caused by more global timeouts. `best_agent.pt` is a training-return checkpoint, not a development-success checkpoint.

Observed curve patterns:

- At 50 mm, tracked total return rises from roughly -186 to +241/+244/+243 across seeds while mean episode length rises from about 6,450 to 8,058-8,086 steps. The fixed development gate still reaches only 13/20, so this return increase is not evidence of passing task learning.
- At 75 mm, episode-return samples are sparse because episodes are roughly 8,884-8,999 steps. Seed 47 regresses from about +227 to +34 while the other two seeds improve only modestly; there is no consistent cross-seed learning signal.
- At 100 mm, final tracked returns are mixed: seed 11 about -96, seed 29 about +190, and seed 47 about -214 from starts near -205/-206. All three final gates nevertheless produce the same 7/20 outcome.
- Policy standard deviation changes only slowly (approximately 0.0183 toward 0.0171-0.0180) and is already constrained by `log_std` clipping; there is no abrupt numerical collapse in the available scalar.
- Policy/value losses remain finite and value loss is modest, but explained variance is not logged. These curves cannot establish that the value function learned a useful task model.

The final development evidence is more decisive than TensorBoard: all three seeds have the same success counts at each height (13/20, 7/20, 7/20), all gates fail, and inspected final evaluations show near-zero executed residual. This is consistent with a policy that largely leaves the weak FSM unchanged, not with NaN/OOM/policy-process failure.

See `plots\training_return_by_stage.png`, `episode_length_by_stage.png`, `policy_value_loss.png`, `entropy_kl.png`, `reward_components.png`, and `residual_action_statistics.png`. Missing charts are rendered as explicit instrumentation-gap panels rather than invented data.
