# Method B seed-11 50 mm smoke attempt 045 diagnosis

- Status: `FAILED` before PPO initialization and before any optimization step.
- Frozen provenance was loaded correctly: FSM SHA-256
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
  and metrics SHA-256
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`.
- Failure: local skrl 2.0.0 constructs its keyword-only `PPO_CFG` dataclass and
  rejected the legacy key `lambda`.
- Local API inspection showed that the installed semantic equivalent is
  `gae_lambda`. The same inspection also showed that
  `clip_predicted_values` is not a supported independent flag; this skrl
  version clips values whenever the unchanged positive `value_clip` is used.
- Minimal compatibility fix: map the frozen YAML `ppo.lambda` value to
  `PPO_CFG.gae_lambda`, remove only the unsupported redundant flag, and reject
  any future unknown PPO configuration keys before agent construction.
- Training-result SHA-256:
  `2bf5192a16c0d3705c91dcee369de04470f052fd112ece516af2d0c014aaed43`.

No checkpoint exists and this run contributes zero training timesteps. It is
preserved as a failed compatibility attempt; retry uses attempt 046.
