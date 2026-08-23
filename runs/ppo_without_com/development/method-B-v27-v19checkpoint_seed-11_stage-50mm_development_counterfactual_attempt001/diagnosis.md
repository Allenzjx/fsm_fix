# Method-B v27/v19-checkpoint 50 mm development counterfactual attempt001

## Disposition

`FAIL`. V27 training is prohibited.

The complete fixed development split remains `13/20`. The exact prior
success set is preserved, but no new scenario reaches the formal success
predicate.

V27 is nevertheless a strong directional improvement over v26:

- collisions decrease from seven to three;
- `0005`, `0008`, `0013`, and `0017` remain active until phase timeout;
- the early critical point has only 2 terminated environments at 110 s,
  versus 5 under v26;
- all four delayed scenarios reach phase 9.

Their terminal full-wheel pattern remains `[true,false,false,true]`. The
3 mm downward authority is therefore directionally useful but insufficient
to establish the two missing strict full-wheel supports.

## Runtime audit

- Telemetry is `53,498 x 122`; only `margin_m` has the expected 5,854 NaNs.
- There are 3,282 nonzero rows: 3,269 exact
  `[0,-0.3,-0.3,0]` emergency rows and 13 historical climb rows.
- All inactive channels are exact zero; no unauthorized phase exists.
- 3,267/3,269 emergency rows physically realize the request within
  `1e-7 m`.
- Two late scenario-0003 phase-10 rows at 130.50/130.55 s encounter
  simultaneous front-right/rear-left IK invalidity after severe trajectory
  divergence, and fail closed through the coupled rollback. This is
  retained as negative evidence.
- The 13 successful `34,800 x 122` histories are exact v26 histories.

## Artifacts

- Result:
  `e19c8042e8405c8f6d6efb38acf37c0fd2d03cb5b537fbbdeb8b8ff137f902af`
- Episodes/status:
  `adee5903f7c2ae9e907a082a608bdee30ad97b1201913b445eb183327b591124`,
  `d872773d1449d4407aaee1c8ee1b91162a02ee742bbe2cb528a40ff0e6e1307a`
- Telemetry:
  `0da7d251c98acc5b4e9eb6ff318b216fad9aa6f4317890f7089ba7d982c8df53`
- Stdout/stderr:
  `b1fb0ff4f4ee975c9d315732ff8f9488c675041dea20b4bef25289258b8f48d6`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID `164032` exited naturally.

## Next action

Do not train v27. Pre-register a stronger but still bounded 6 mm
deficient-diagonal downward floor after offline IK reconstruction.
