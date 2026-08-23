# Method B seed-11 50 mm smoke attempt 046 diagnosis

- Status: `SMOKE_PASS`.
- The local skrl compatibility change allowed the PPO agent to initialize.
- Sixteen real Isaac environments produced finite contact forces and eight
  finite zero-residual control steps.
- Actor observation shape was 16×96 and asymmetric Critic state shape was
  16×146.
- Zero residual exactly reproduced the frozen FSM baseline.
- Frozen provenance matched FSM SHA-256
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
  and metrics SHA-256
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`.
- Training-result SHA-256:
  `9d89a838fe4f78616e222901713365036e702c246ee326015a6facdfabdd666a`.

This is an integration preflight only and contributes zero optimization
timesteps. The next run is the registered 300-iteration method-B stage.
