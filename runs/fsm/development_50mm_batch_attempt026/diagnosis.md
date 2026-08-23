# Development 50 mm batch attempt 026 diagnosis

## Immutable run result

- The environment process (`PID 96276`) exited naturally.
- The evaluator completed all 20 development scenarios and reported
  `passed_execution: true`.
- Strict success: **0/20 (0.0%)**.
- Failure counts:
  - `BODY_OR_LINK_COLLISION`: 7
  - `FSM_PHASE_TIMEOUT`: 1
  - `TIMEOUT`: 12
- FSM config SHA-256:
  `809577abdddcd229071edf0f406f07ecbfdf20464089da3674f9245542bbcf16`
- Result SHA-256:
  `81e73edad3bffc56887f4cc7a5db8f2612af32262e515983b43f9a4d37f80b74`
- Episodes SHA-256:
  `6c65a125da668ebb3960d2097018f7fbcdcadb5270c18287032eb3b5a0ebd741`
- Telemetry SHA-256:
  `f5a8a5065e4fada7d0e3db7578c8b889f28fa26980d185e0a1a32eaa009575be`

## Reachability audit

The 100 mm support geometry was applied without height scaling:

- front-right wheel-center z offset: 18.5 mm
- rear-left wheel-center z offset: 11.25 mm
- rear-right wheel-center z offset: 15.0 mm

That geometry is not analytically reachable on the 50 mm reference path.
The 20 episodes accumulated **9,235 baseline IK-invalid leg samples**, all on
the rear-left leg:

- 12 global-timeout episodes: 613 rear-left invalid samples each
- scenario `development-h050-0003`: 265 rear-left invalid samples
- scenario `development-h050-0013`: 1,614 rear-left invalid samples
- the remaining six collision episodes: zero IK-invalid samples

The formal/diagnostic clamp counter remained zero in every episode. The
invalid solutions therefore fell back to the unmodified reference, rather
than being silently clamped.

At the global timeout, nine scenarios had
`full_wheel_on_top=[true,true,true,false]`. Three others had all four wheel
centers fully on top, but at least one wheel had less than the unchanged 2 N
upward-force threshold. None satisfied the strict geometry, force, tilt,
angular-rate, non-wheel-contact, joint-limit, and 1.5 s dwell predicate
together.

## Collision and phase-timeout audit

Six `front_right_bot` collisions occurred in phase 8 at approximately
107.55--108.35 s (scenario indices 5, 6, 8, 9, 17, and 19). Their terminal
front-right wheel was not fully on top and their rear-left wheel was also not
fully on top. These failures occur before the phase-9 formal support geometry
is active and must not be attributed to its IK reachability problem.

Scenario index 3 reached phase 10 and then reported a 12.889 N
`front_right_bot` collision near 124.65 s; it had already accumulated 265
rear-left IK-invalid samples.

Scenario index 13 remained in phase 9 until the phase timeout near 147.15 s.
Its terminal front-right upward force was about 0.699 N and rear-left upward
force was 0 N; it accumulated 1,614 rear-left IK-invalid samples.

## Decision

Attempt 026 is retained as a formal negative result. It disproves applying
the grid-022 100 mm support offsets unchanged at 50 mm.

The next development change is narrowly scoped: preserve the selected 100 mm
offsets at 100 mm, scale them linearly to zero at 50 mm, and use the 50%
interpolation at 75 mm. This matches the existing height-conditioned
reference/recovery policy and restores the documented invariant that the
complete 50 mm replay remains unmodified. The strict success predicate,
collision threshold, force threshold, and timeout remain unchanged.
