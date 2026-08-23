# Front-right diagnostic-limit grid 022 diagnosis

- Fixed rear-left/rear-right extension: 11.25/15 mm.
- Varied front-right extension: 17/17.75/18.5/19.25/20 mm.
- Fixed common phase-9 ramp start: 0.4.
- Result: **2 / 25 strict successes**, 12 collisions, 11 timeouts.
- Engineering-admissible result: **2 / 25**.
- Result SHA256:
  `8ef8c0c9c4e16f9582063605edd233eb22cf46a45163456394277decca348b58`.

Both environment successes passed the engineering filters:

- candidate 19, front-right 18.5 mm: 0/0/0/0 per-leg IK fallback, zero
  clamp, 3.4795 N best simultaneous minimum;
- candidate 20, front-right 20 mm: 0/0/0/0 per-leg IK fallback, zero clamp,
  5.3765 N best simultaneous minimum.

The diagnostic accumulator reports 1.4833 s for both because its update
occurs after the environment has consumed and terminated on the final
qualifying step. The environment's authoritative strict-success termination
requires and observed the complete 1.5 s dwell; this is not a relaxed metric.

The 18.5 mm candidate was selected because it is the lower successful
amplitude and retains 1.5 mm margin below the enforced 20 mm diagnostic
limit. Its best ordered FL/FR/RL/RR force snapshot was
4.520/10.897/9.889/3.479 N. The selected formal geometry is:

- front-left: [0, 0] mm;
- front-right: [0, 18.5] mm;
- rear-left: [0, 11.25] mm;
- rear-right: [0, 15] mm;
- phase-9 start progress: 0.4 for every leg.

This geometry is promoted into `configs/fsm.yaml` and consumed by both the
formal evaluator and PPO trainer. Attempt 023 will run the formal FSM evaluator
on a single 100 mm development scenario before any multi-scenario claim.
