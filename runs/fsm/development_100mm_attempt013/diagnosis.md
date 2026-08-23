# Attempt 013 diagnosis

This run is retained as a failed FSM-development attempt.

Full phase-9 recovery improved the prior failure but overshot the usable
equilibrium:

- at 135 s, the front-right wheel-frame height was 0.1366 m versus 0.1172 m
  in attempt 012, and no non-wheel contact was present;
- roll decreased from 0.0518 rad at 133 s to about 0.0081 rad at 138 s;
- the eventual `front_right_bot` collision was delayed from 145.5167 s to
  149.4333 s.

The complete recovery endpoint lifted the rear-left wheel off the platform
(terminal frame height 0.18172 m and 0 N), causing a new diagonal loss of
support and the same strict 5 N link-contact failure at 7.35687 N.

The phase-9 trace identifies a measured partial-recovery equilibrium. At
132.0 s, approximately 10% along the recorded recovery direction, wheel
logged contact-force magnitudes were 6.13/6.64/7.96/6.52 N. These historical
fields do not prove the world-Z upward-force success predicate. At roughly
15%, the front-right
force had fallen to 1.42 N. The next attempt therefore caps the high-obstacle
recovery at 10% (5% at 75 mm, zero at 50 mm), reaching it by smoothstep and
holding it. No threshold is changed.
