# Method-B v29/v19-checkpoint 50 mm development counterfactual attempt001

## Disposition

`FAIL`. V29 training is prohibited.

The complete fixed development split remains `13/20`, with three
`BODY_OR_LINK_COLLISION` failures and four `FSM_PHASE_TIMEOUT` failures.
The exact v27 success set is preserved.

V29 provides an exact causal comparison with v27:

- both telemetry files are `53,498 x 122`;
- all 13 successful `34,800 x 122` histories are byte-exact;
- all four target environments are byte-exact through phase 8;
- only their 2,524 phase-9 emergency rows change, from 3 to 4 mm;
- all 2,524 changed requests physically realize with zero rollback;
- all four scenarios still time out in phase 9.

Therefore an additional 1 mm vertical target change is physically
executed but does not change the formal outcome.

## Geometry diagnosis

At timeout, the four target scenarios all have:

- contact state `[TOP, TOP, AIR, TOP]`;
- wheel-on-top `[true,true,false,true]`;
- full-wheel-on-top `[true,false,false,true]`;
- front-right y between -0.497 and -0.533 m, outside the full-footprint
  lateral region;
- rear-left z between 0.169 and 0.173 m, well above the top-support
  wheel-center level near 0.10 m.

An axle-midpoint geometry estimate gives phase-9 starting yaw of
-0.229 to -0.278 rad for the four timeouts, versus -0.065 to -0.119 rad
for all successful scenarios. The failed front axle is displaced toward
negative y and the rear axle toward positive y, consistent with excessive
negative yaw. Vertical wheel-center authority is not the direct control
channel for this lateral footprint error.

## Runtime audit

- Telemetry is `53,498 x 122`; only `margin_m` has the expected 5,854
  NaNs.
- There are 3,282 nonzero rows: 745 exact 3 mm emergency rows, 2,524
  exact 4 mm phase-9 emergency rows, and 13 historical climb rows.
- 743/745 3 mm and 2,524/2,524 4 mm emergency rows physically realize
  within `1e-7 m`.
- The only rollbacks are the same two scenario-0003 phase-10 rows at
  130.50/130.55 s. All inactive channels are exact zero and all nonzero
  actions occur only in phases 8--10.

## Artifacts

- Result:
  `ef79b219269c11645c912a8864f042a3644fae0f6a613ad07ae612af42c10023`
- Episodes/status:
  `986a9ff16ff8fe94cbd2a48cc91f6104a7b90bee1c528770e12fbc0f204dba64`,
  `8f343c8191983775a83c0704716ba6b66165762d4fd58ef3345d4f5be81f1139`
- Telemetry:
  `337f274f230048d57fe74e8bd0e7644c48a9e64bf02d6f3f501c8b1938e23dc3`
- Stdout/stderr:
  `5d36fe201ec66f497ffc8a129c7dbab228936a9b0661bc7db3c9cef2bef60f59`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID `169144` exited naturally.

## Next action

Do not train v29. Pre-register a phase-9-only physical-forward
differential wheel-speed correction that counters the measured negative
yaw while retaining the proven v29 wheel-center behavior.
