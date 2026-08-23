# Method-B v26/v19-checkpoint 50 mm development counterfactual attempt001

## Disposition

`FAIL`. V26 training is prohibited.

The unchanged v19 final checkpoint reached `13/20` on the complete fixed
50 mm development split. It retained exactly the prior 13-success set,
including all 12 frozen-FSM successes and scenario `0009`, but added no
rescue. All seven failures ended in `BODY_OR_LINK_COLLISION`.

## Action and realization audit

- Telemetry shape is `50,362 x 122`; only the geometrically undefined
  `margin_m` field has NaNs (`5,854`), as allowed by the metric schema.
- There are 146 nonzero execution rows: 133 exact asymmetric emergency
  rows and 13 historical climb rows. No other structure occurs.
- Every emergency row is exact
  `[FL,FR,RL,RR] = [0,-0.3000000119,+0.2400000095,0]`.
- Nonzero rows occur only in registered phases; all x and wheel-speed
  residuals remain exactly zero. Physical residual scaling differs from
  the registered action/bound product by at most `9.32e-11 m`.
- Every nonzero requested target is physically realized. There are zero
  rollback rows above `1e-7 m`; maximum final-to-request error is
  `4.47e-8 m`.
- Action and physical bounds pass. No unauthorized nonzero row exists.
- The 13 success histories comprise `34,800 x 122` values and are exactly
  identical to both v25 and v24, including NaN locations.

## Failure diagnosis

All failures are scenarios `0003`, `0005`, `0006`, `0008`, `0013`,
`0017`, and `0019`. Every terminal full-wheel pattern is
`[true,false,false,true]`; every collision body is `front_right_bot`.

V25's front-right-only downward extension delayed `0008` and `0013` to
phase timeouts. V26 adds rear-left `+2.4 mm`, which raises/retracts that
already missing wheel-center channel. Those two scenarios return to
front-right-body collision; all seven failures now collide. The emergency
trajectory terminates so rapidly that v26 records only 133 emergency rows,
versus 1,602 physically realized front-right-only rows under v25.

The result is a causal direction failure, not an implementation or IK
failure.

## Artifacts

- Result:
  `1a51083dd038e4f78ef8f05476b14607b5b226d716606affee1531e8dc7d1efb`
- Episodes/status:
  `3fdd448c371036402c9c4e3cb5641fafd3bde30cfa223b4e88e19dd3b5ef5c31`,
  `6af7cb49734775e659929afe99007aa3cebe308f3c45d95df63afe85fb3c5c7e`
- Telemetry:
  `c541ac57894e9fd42f6745da26a68efe1d4863ee9a10c05f596b81789dc8d263`
- Stdout/stderr:
  `8b18b048b997653730a2979d25ec5cacb00859b92b66c0513f6defe9e835c2cb`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `164780`; it exited naturally.

## Next action

Do not train v26. Freeze an offline v27 feasibility analysis for
simultaneously extending the deficient front-right and rear-left
wheel-centers downward, then register and smoke that candidate before any
new counterfactual.
