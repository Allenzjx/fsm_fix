# Method-B reward-v6 seed-11 50 mm training attempt001 diagnosis

## Disposition

`ABORTED_INVALID_RESET_DISTRIBUTION`. This run contributes zero accepted
training budget. All checkpoints are retained as negative evidence and are
ineligible for warm start, development/validation evaluation, promotion, or
locked testing.

Only the exact verified environment Python PID 126496 was terminated. The
process command line contained the unique run name and its executable was
`env_isaaclab\python.exe`. No broad Python/process-name kill was used.

## Evidence

- The run reached progress 10,057/19,200. The latest durable checkpoint is
  `agent_9600.pt`, SHA-256
  `10e4f9480957e1553087d721e2d723a65bf07198d0c079cb4183ba7666318bcf`.
- At TensorBoard step 9,024, skrl's rolling completed-episode arrays reported
  lengths min/mean/max `168 / 8623.375 / 8991` and returns
  `4.773005 / 61.238159 / 67.416283`.
- Inspection of `skrl.agents.torch.base.Agent.record_transition` confirms
  `_track_rewards` and `_track_timesteps` are appended from the same
  `finished_episodes` indices. The 168-step signal therefore cannot be
  dismissed as a separately sampled current-episode length.
- Reward-v6 itself was effective: earlier first-pass failures around
  6,443--6,609 steps returned about -213 to -211, and the real-Isaac forced
  fall smoke produced an exact -200 fall component. The later short positive
  episode instead exposed a reset-distribution defect.

## Root cause

`WLRResidualRLEnv._reset_idx()` calls the legacy reset, which writes the
default root/joint state, and immediately calls
`_apply_training_randomization()`. That function read:

1. the newly written/default `root_pose_w`, but
2. link-derived `body_pos_w`/wheel positions that can still represent the
   just-terminated pose until the next scene update.

It then combined those inconsistent caches to compute
`root_pose.x += current_distance - desired_distance`. After a long episode
ended on/near the obstacle, the next episode could be initialized from
terminal wheel geometry rather than the registered pre-obstacle distribution.
The resulting short positive episodes are invalid training samples.

## Retained artifact hashes

- partial `training_result.json`:
  `72e267b8765f47e26735fe9498d3ff553a34bb7870a465bc3824195f352909ef`
- TensorBoard event:
  `02c26fe0bc883b1caf3cf6fa537500834fabc1f323a79870c4d13993eb3a1b2a`
- stdout:
  `c1f8591deeeca32df390b18ad18b5295095a33ea655867ded55d46c771027357`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

The original partial `training_result.json` remains `RUNNING`; this sidecar
records the truthful aborted disposition without fabricating normal
completion.

## Registered next action

Register runtime v7. Cache the standing root-to-wheel geometry once from the
settled construction state. On every randomized reset, build the root pose
from the asset default root state, environment origin, desired pitch,
registered obstacle front, desired distance, cached relative wheel geometry,
and wheel radius only. Do not read current root/body pose to place a reset.

Add a regression proving the computed front-wheel distance and ground
clearance are independent of any terminal pose. Extend real-Isaac smoke by
forcing a tilted terminal pose over the obstacle, allowing auto-reset, then
requiring the next physics step to recover the sampled pre-obstacle distance
without immediate success/termination. Retrain from scratch only after it
passes.

## Subsequent correction

The 168-step positive segment was later reproduced after the cache-independent
v7 reset passed a terminal-over-obstacle smoke. A minimal tensor reproduction
then proved the segment comes from skrl 2.0's display tracker: for `[N,1]`
done tensors, `nonzero()` returns `[env, column]`, and using that two-column
tensor to reset a cumulative `[N,1]` array also resets environment 0 through
the constant `column=0` entries. Thus the 168-step statistic did not prove a
physical reset contamination.

The old reset code nevertheless did combine current root/link caches and was
replaced by the safer cache-independent v7 geometry. The v6 run remains
incomplete and ineligible, but its original root-cause attribution is
superseded by this correction.
