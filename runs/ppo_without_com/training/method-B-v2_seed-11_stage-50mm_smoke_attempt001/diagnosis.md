# Method B reward-v2 seed-11 50 mm smoke attempt001

- Status: `SMOKE_PASS`.
- Real IsaacLab preflight: 16 environments, finite 96-D Actor observations,
  finite 146-D Critic states/values, finite bounded 12-D policy samples,
  finite contacts, exact zero-residual FSM equivalence, and a successful
  explicit two-environment partial reset.
- Effective reward provenance includes all 18 common weights and the rule that
  top-contact/recovery occupancy terms integrate using control `step_dt`.
- Common PPO config SHA-256:
  `034019e479cbe64fd5b1b8d5207a55920a72cadb094f394dcbbffcdd9e5d127e`.
- Training-result SHA-256:
  `7d60820be19e12e59cac5c08f384d389de2df21544961936dbe0587fed04b021`.

The smoke contributes zero training transitions. Full reward-v2 training must
start from random initialization and may not resume the incompatible v1
checkpoint.
