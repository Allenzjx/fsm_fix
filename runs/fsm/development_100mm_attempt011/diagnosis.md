# Attempt 011 diagnosis

This run is retained as an intentionally unchanged diagnostic reproduction of
attempt 010.

The physical trajectory and aggregate metrics reproduced bit-for-bit, including
the telemetry SHA256
`869648fe07de98c73d852548e7ccb862a7fc849940c9f31ee2e55020504de2ec`.
At the first and only strict joint-limit termination:

- violating joint: `rear_right_hip`;
- actual raw position: `0.6011857390 rad`;
- recorded-envelope raw upper limit: `0.5662186146 rad`;
- unchanged tracking tolerance: `0.0349065850 rad` (2 degrees);
- violation beyond upper limit plus tolerance: `0.0000605394 rad`
  (`0.0034686 degrees`).

The commanded rear-right hip was exactly at the recorded lower endpoint,
`-35.3 degrees`. The next attempt preserves every safety and success threshold
but keeps all deployed FSM servo references 1 degree inside their recorded
command envelope. This provides a measured margin larger than the observed
compliant overshoot while remaining within the source-supported range.
