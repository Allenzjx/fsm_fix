# Attempt 017 diagnosis

This run is retained as a failed FSM-development attempt.

High-load radial shortening activated on the measured FL/RR support diagonal
and reached 5 mm on both legs. It did not restore front-right wheel load:

- at 135 s, unload trims were approximately
  `[3.45, 0.00, 0.05, 3.65]` mm while front-right remained at 0 N;
- terminal trims were `[5, 0, 0, 5]` mm;
- `front_right_bot` contact reached 10.4382 N at 145.5167 s.

This rejects scalar leg-length load redistribution as sufficient for the
platform recovery pose. The next diagnostic runs 25 identical environments in
parallel and sweeps a smooth phase-9 front-right wheel-center offset over
`dx = {-15,-7.5,0,7.5,15}` mm and
`dz = {-10,-5,0,5,10}` mm. All other controller, physics, scenario, and
evaluation thresholds remain identical; the rejected unload loop is disabled
inside that explicit diagnostic run.
