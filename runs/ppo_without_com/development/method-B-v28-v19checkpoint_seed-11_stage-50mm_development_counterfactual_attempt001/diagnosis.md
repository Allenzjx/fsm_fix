# Method-B v28/v19-checkpoint 50 mm development counterfactual attempt001

## Disposition

`FAIL`. V28 training is prohibited.

The complete fixed development split remains `13/20`, and the exact v27
success set is preserved. All seven failures terminate as
`BODY_OR_LINK_COLLISION`.

The stronger 6 mm authority is causal negative evidence:

- v27 failures `0005`, `0008`, `0013`, and `0017` reached phase 9 and
  timed out;
- under v28 they collide at 107.50, 108.85, 112.60, and 122.45 s;
- the first three collide in phase 8 and `0017` collides in phase 9;
- therefore applying 6 mm throughout phases 8--10 destroys the useful
  delayed trajectories instead of establishing strict support.

## Runtime audit

- Telemetry is `50,758 x 122`; only `margin_m` has the expected 5,854
  NaNs.
- There are 540 nonzero rows: 527 exact
  `[0,-0.6,-0.6,0]` emergency rows and 13 historical climb rows.
- Emergency rows occur 281/137/109 times in phases 8/9/10. All inactive
  channels are exact zero and no unauthorized phase exists.
- 525/527 emergency rows physically realize the requested target within
  `1e-7 m`.
- The same two late scenario-0003 phase-10 rows at 130.50/130.55 s
  encounter simultaneous front-right/rear-left IK invalidity and fail
  closed through coupled rollback. No new rollback mode appears.
- The 13 successful `34,800 x 122` histories are byte-exact v27
  histories.

## Artifacts

- Result:
  `66189d2cb98a955fc20f95397a32635c86ee7ec05534aa774de6d69ad43c8b03`
- Episodes/status:
  `3b41a61c1fe0e4a6a55c8caca24942898288124766281debe9caa2f69ee53ef4`,
  `a1c269f3d6d2bc411bdd51411e9319281832c2203eb58278e25c8507121a23b0`
- Telemetry:
  `950b222f5777093f020c52d749173ac5e4abe05e0e99a8be8d9ce95e18a556b2`
- Stdout/stderr:
  `b6b97f4ab1bb27bba3cfa5bea3d90dc3d63fb47adaef6c068049d6d0aa400ab6`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID `93492` exited naturally.

## Next action

Do not train v28. Preserve the proven v27 3 mm phase-8 trajectory and
pre-register a phase-selective v29 candidate that raises only phase-9
authority from 3 to 4 mm.
