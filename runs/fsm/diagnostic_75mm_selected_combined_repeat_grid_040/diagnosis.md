# Diagnostic 75 mm selected-candidate repeat grid 040

## Immutable result

- The exact environment process (`PID 144184`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 exact repetitions of one controller
- Strict success: **4/25 (16%)**
- Other outcomes: **21/25 global timeouts**
- Result SHA-256:
  `641275183c48ab5ff76b8a23e166ee5e09e7f13844ae21d31612cf9e5a978562`

All 25 repetitions retained 0/0/0/0 analytic-IK fallback and zero clamp.
Every branch reached exactly 2/0/0/2 mm terminal shortening in
front-left/front-right/rear-left/rear-right order. Median diagnostic strict
dwell was 1.0333 s and mean dwell was 0.8240 s.

The four successful repetitions terminated at
149.933/149.933/149.733/149.767 s. Their terminal upward-force vectors were:

- 7.482/6.396/6.840/7.843 N
- 6.522/7.243/7.556/7.223 N
- 7.747/6.227/6.812/7.724 N
- 8.531/5.212/5.599/8.962 N

All four had approximately 0.285--0.286 m longitudinal margin and zero
non-wheel contact.

## Decision

The exact candidate has repeatable nonzero strict success and no engineering
fallback. Promote it into height-conditioned formal policy at 75 mm only:

- phase-7/8 physical-forward wheel speed:
  front-left/front-right/rear-left/rear-right = 0/0/0.3/0.3 rad/s;
- phase-9/10 pre-capture forward speed: 0.075 rad/s;
- high-load shortening: 2 mm maximum at 0.75 mm/s, with unchanged 4/8 N
  hysteresis;
- support geometry: existing reachable half-scale
  0/9.25/5.625/7.5 mm at phase-9 progress 0.4.

The 50 and 100 mm anchor policies remain behaviorally unchanged. First run a
formal single-scenario 75 mm evaluator, then all 20 development 75 mm
scenarios. These formal runs, not this diagnostic repeat, determine the
reported FSM baseline.
