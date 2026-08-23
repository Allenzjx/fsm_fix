# Method B seed-11 50 mm smoke attempt 049 result

- Status: `SMOKE_PASS`.
- Real IsaacLab preflight: 16 parallel environments at 50 mm with nominal
  randomization.
- Actor observation shape: `16 x 96`.
- Asymmetric Critic state shape: `16 x 146`.
- Sampled policy action shape: `16 x 12`; all values finite and maximum
  absolute magnitude `0.42357566952705383`.
- Critic value shape: `16 x 1`; all values finite.
- Contact force finite: yes.
- Zero residual exactly reproduces the frozen FSM command: yes.
- Frozen FSM SHA-256:
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`.
- Frozen metrics SHA-256:
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`.
- Training-result SHA-256:
  `7c009c41a19b09a348db65e196a162c018b16378bb18c504d5e3aff80ddf8f40`.

This smoke run performs no optimization and contributes zero training
transitions. It authorizes full Method-B seed-11 50 mm training attempt002.
