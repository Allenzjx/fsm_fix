# Changelog

## 2026-07-27

- Created isolated validation project and full source/hash inventory.
- Parsed and hashed the accepted 50/100 mm replay logs.
- Derived a validation USD with an eight-joint, limit-only modification scope.
- Ran fresh Isaac static, wheel-direction, and safe joint-motion checks.
- Implemented contact classification with explicit riser exclusion, signed
  longitudinal support margin, whole-body CoM utilities, telemetry schemas,
  replay/FSM references, analytic IK, and 12-D residual action handling.
- Added a ContactSensor-backed asymmetric DirectRLEnv and confirmed exact
  zero-residual target equivalence in Isaac.
- Retained a failed legacy collector ContactSensor attempt as negative
  evidence; added a sensor-stable DirectRLEnv replay path.
- Pre-registered development, validation, and 300-scenario locked-test
  manifests. No locked results have been read or produced.
- Invalidated the first full 50 mm DirectRLEnv replay after proving that some
  legacy per-event `command_state_after` fields are stale pre-command snapshots.
- Reimplemented the reference player's `expanded_commands`/`command` dispatch
  semantics in the isolated loader and added regression tests against both
  ordinary and batched events.
- Made exact replays non-terminating while retaining and logging every failure
  predicate, and changed formal body-collision detection/reward to actual
  non-wheel ContactSensor forces near the obstacle.
- Verified the corrected first wheel event in a 3 s Isaac diagnostic: immediate
  0.3 rad/s targets, finite contact telemetry, and no reset or safety failure.
- Superseded (without deleting) the unused v1 scenario manifests after fresh
  replay geometry proved their legacy obstacle/distance constants incompatible.
  Pre-registered v2 contains the same split sizes and seeds, uses the measured
  replay geometry, and has locked-test SHA256
  `a621045d04b5a84a707fd2fb7a6cc8a8fe13aab3407dc944ea0dd6ae95cb58a3`.
- Preserved corrected 50 mm attempt 002 as a strict failure: it reached final
  four-wheel top support with no safety fault, but the 2 s observation tail
  ended at 62/90 required stable steps. Increased only the post-command
  observation tail to 3 s; the replay, physics and 1.5 s criterion are unchanged.
- Passed the explicitly seeded 50 mm raw profile on attempt 005: all 159 state
  events, +0.941704 m progress, final debounced four-wheel top support, and no
  recorded collision/fall/command-limit/joint-limit/numerical failure. The
  independent post-audit also passed.
- Preserved the seeded 50 mm fast/no-cap run as a strict failure. It dispatched
  all 159 aggregate events and 269 expanded commands and ended with all four
  wheels geometrically on top, but the rear-right upward force remained near
  1.83 N, below the unchanged 2 N reference threshold. Formal replay scripts
  therefore default to the timestamp-exact raw profile.
- Preserved the seeded 100 mm raw replay as a strict traversal failure after
  complete 68-event/101-command dispatch. It had no safety fault, but the rear
  wheels ended at the front riser. The source recording's own final root and
  command snapshot confirms that it is a partial reference rather than a full
  all-four-wheel traversal under the frozen-intent success definition.
- Corrected the runtime FK validator to compare post-step body positions with
  post-step actual joint angles rather than pre-step commands. The invalid
  comparison attempt is retained; the corrected 1,024-configuration run passed
  with 3.82 micrometre maximum and 0.78 micrometre RMS wheel-center error.
- Corrected the residual-environment validator so static contact settling holds
  the standing reference and exact zero-residual assertions cannot compare
  across an automatic episode reset. The corrected 16-environment run passed
  180 settling, 300 exact-zero, 40 bounded-random, and explicit vector-reset
  checks with 96-D actor and 146-D critic observations.
- Added a wheel-distance-preserving FSM timing profile. It only compresses
  zero-wheel waiting gaps; full-replay integration tests prove that all four
  commanded wheel-angle integrals are unchanged for both source recordings.
- Changed contact phase exits to latch a physical milestone only after
  three-control-step debounce. This prevents a valid lift/place event from
  being forgotten before the planned command window ends.
- Added live controller-evaluation status plus per-wheel contact state, force,
  x/z position, and 12-D reference command telemetry, including terminal
  snapshots taken before DirectRLEnv auto-reset.
- Corrected controller-evaluation initialization so each articulation settles
  for 120 physics steps before paired scenario placement, wheel geometry
  determines a non-penetrating pitched root height, and the episode clock
  starts only after initialization.
- The first 50 mm zero-order-hold FSM development scenario reached stable
  four-wheel top support with +1.140915 m progress and no safety termination.
- Preserved four 100 mm development failures. The first exposed the old
  initialization penetration; attempts 002 and 003 reached contact-gated
  approach/body transfer but lacked a rear-leg lift in the partial 100 mm
  source; attempt 004 proved that phase-7-only substitution created a
  discontinuous rear-leg target and a body/link collision.
- Replaced the discontinuous substitution with the physically successful
  50 mm rear-leg channels from episode time zero. All heights now use the
  slower complete-source duration, so those accepted zero-order-hold command
  intervals are never compressed. Two reference-composition regressions raise
  the local unit-test total to 33 passing tests.
- Preserved 100 mm attempt 005 as a collision failure. It proved the rear
  reference splice was continuous, but also showed that the fixed phase-5
  boundary held the 100 mm source before its recorded front-leg placement
  while retaining a forward wheel command, producing 0.448 m of excess gate
  travel. Phase 5 is now height-conditioned from `u=0.500` at 50 mm to
  `u=0.574` at 100 mm, and non-recovery gate waits command zero wheel speed.
- Added terminal per-link non-wheel contact-force snapshots and three
  height-conditioned phase-schedule regressions; all 36 unit tests pass.
- Preserved 100 mm attempt 006 as a strict `base_link` collision failure at
  5.113 N. It removed the gate-overtravel mechanism, then showed that an
  unwarped 50 mm rear-left preparation command began while the 100 mm front
  leg was still placing and induced a roll transient.
- Added a continuous piecewise-linear rear-reference time map. It is the
  identity at 50 mm and aligns rear `u=0.50` with the recorded 100 mm
  front-placement completion boundary `u=0.574`; 75 mm is interpolated.
  The new continuity/timing regression brings the unit-test total to 37.
- Preserved 100 mm attempt 007 as a `base_link` collision failure. The rear
  time map eliminated the earlier phase-5 collision, but the phase-6 source
  wheel command advanced the base another 70.6 mm while rear preparation was
  underway, producing 38.55 N edge contact. BODY_TRANSFER now holds all wheels
  at zero and phase-7/8 contact recovery remains unchanged.
- Preserved 100 mm attempt 008 as a strict collision failure. The phase-6
  wheel hold reduced base travel to 18.7 mm and `base_link` contact to
  19.00 N, proving sequential rear-leg preparation remained the cause.
- Added a height-blended coordinated BODY_TRANSFER trajectory connecting the
  exact recorded-safe rear endpoints: both hips move synchronously with a
  smoothstep profile before the rear-right knee tuck. Endpoint and continuity
  tests bring the unit-test total to 38 passing.
- Preserved 100 mm attempt 009 as a strict `base_link` collision failure.
  Coordinated rear hips reduced roll to 0.038 rad and contact to 9.32 N, but
  pitch reached -0.124 rad because the active front reference kept only
  58--70 mm hip-to-wheel vertical separation.
- BODY_TRANSFER now first extends both front supports to the recorded-safe
  100 mm recovery posture (approximately 141 mm vertical separation), then
  performs synchronized rear preparation. A staging regression raises the
  local unit-test total to 39 passing.
- Preserved 100 mm attempt 010 as a strict `JOINT_LIMIT` failure. The staged
  front support eliminated every earlier body collision, the right-rear wheel
  reached top contact, and the left-rear wheel reached the riser with
  +0.843341 m progress and +0.158809 m minimum support margin. The phase-8
  rear reference placed two channels at the edge of the recorded-safe command
  envelope, but the old output did not retain first-violation joint state.
- Added first-joint-limit diagnostic snapshots containing actual raw joint
  positions, raw limits, tracking tolerance, and exact violating joint names.
  The unchanged controller/scenario is reproduced before any reference limit
  is altered. All 39 unit tests still pass.
- Preserved diagnostic attempt 011. It reproduced attempt 010 bit-for-bit and
  identified only `rear_right_hip`: actual raw position `0.6011857390` rad
  exceeded the recorded upper limit plus the unchanged 2 degree tolerance by
  `0.0000605394` rad (`0.0034686` degrees).
- FSM servo references now retain a 1 degree margin inside every recorded-safe
  command endpoint. This does not relax the physical joint-limit predicate or
  any success/collision criterion. An all-channel regression brings the local
  unit-test total to 40 passing.
- Preserved 100 mm attempt 012 as a strict `front_right_bot` collision
  failure. The 1 degree margin removed the joint-limit termination and all
  four wheels reached the platform, but the held asymmetric rear transfer pose
  increased roll from 0.0124 rad to about 0.078 rad, unloaded the front-right
  wheel, and produced 7.291 N link contact during DRIVE_CLEAR.
- Added a phase-9 smoothstep recovery toward the exact physically successful
  50 mm final rear pose. It begins only after both rear wheels have passed the
  contact gate and is height-blended from zero at 50 mm to full at 100 mm.
  The new endpoint/height regression brings the unit-test total to 41 passing.
- Preserved 100 mm attempt 013 as a strict `front_right_bot` collision
  failure. Full rear recovery reduced roll and delayed contact to 149.433 s,
  but its endpoint lifted the rear-left wheel to 0.18172 m with zero load.
- The phase-9 trace logged all four contact-force magnitudes at
  6.13/6.64/7.96/6.52 N near 10% recovery, while the front-right magnitude fell
  below 2 N beyond about 15%. Recovery is now capped at that measured 10%
  equilibrium direction at 100 mm (5% at 75 mm, zero at 50 mm); all 41 unit
  tests pass.
- Preserved 100 mm attempt 014 as a strict `front_right_bot` collision
  failure. The 10% recovery point was only transiently balanced: after settling,
  forces returned to an approximately 11.79/0.00/2.82/14.35 N diagonal split
  and link contact reached 26.8161 N at 145.55 s.
- Added contact-closed-loop front load trim during RECOVER/DRIVE_CLEAR. It uses
  2/4 N hysteresis, 2.5 mm/s rate, a 10 mm wheel-center extension bound, the
  validated planar IK, and the unchanged recorded-safe joint envelope. Trim
  state is included in status, telemetry, and terminal episode evidence. A
  vector hysteresis regression brings the unit-test total to 42 passing.
- Preserved 100 mm attempt 015 as a strict `front_right_bot` collision
  failure. At 3.583 mm trim it achieved measured all-wheel forces of
  9.80/2.32/4.56/12.02 N, but the 10 mm bound allowed continued extension and
  contact at 6.875 mm. The bound is now tightened to the measured 3.5 mm
  support point; all 42 unit tests pass.
- Preserved 100 mm attempt 016 as a strict `front_right_bot` collision
  failure. Capping direct front-right extension at 3.5 mm prevented the early
  overshoot but did not create static support; front-right remained at 0 N and
  contact reached 24.1183 N at 145.533 s.
- Replaced the rejected low-leg extension with independent high-load
  unloading: legs over 8 N shorten radially at 1.5 mm/s up to 5 mm and release
  below 4 N, using validated IK and unchanged safe envelopes. Four-leg
  terminal trim is now audited. A new vector regression brings the unit-test
  total to 43 passing.
- Preserved 100 mm attempt 017 as a strict `front_right_bot` collision
  failure. FL/RR radial shortening reached 5 mm on both high-load legs but did
  not restore front-right wheel force; link contact reached 10.4382 N.
- Added a development-only, 25-environment GPU grid diagnostic for smooth
  phase-9 front-right wheel-center offsets. It duplicates the same first
  100 mm development scenario, disables the rejected unload loop only for the
  diagnostic, and preserves all physics and evaluation thresholds.
- Fixed the PPO training preflight's missing `ACTION_DIM` import, which would
  otherwise fail before the first zero-residual step. Added a static entrypoint
  regression and a local `src`-layout pytest bootstrap; the pure-Python suite
  now reports 44 passing tests under `env_isaaclab`.
- Invalidated recovery grid 001 before its intervention began: the diagnostic
  offset ramp reached its endpoint in phase 9 but reset to zero on entry to
  phase 10. The exact environment PID 142060 was stopped while all 25
  candidates were still in phase 5. The corrected scale ramps in phase 9 and
  holds at one throughout phase 10; a continuity regression raises the suite
  to 45 passing tests, and the replacement run is grid 002.
- Hardened the not-yet-unlocked PPO entrypoint: PPO scalar settings now come
  from the hashed common config, startup rejects any B/C config drift beyond
  the method label and CoM-margin reward weight, and the shared Actor starts
  with exactly zero deterministic residual and recorded `log_std=-2.0`.
  Config-diff and initialization regressions raise the suite to 47 passing
  tests.
- Replaced independent per-height PPO runs with a shared B/C curriculum
  wrapper. Each seed resumes 50 -> 75 -> 100 mm, executes the complete
  development split after each stage, and advances only when the configured
  episode-count, method, height, checkpoint-hash, and success-rate gate passes.
- Added deterministic per-reset training randomization with nominal, light,
  and full registered bounds for initial distance/pitch, friction, actuator
  delay, and observation noise. Sampling depends only on method-shared seed,
  environment ID, and episode index; evaluation leaves this hook disabled.
  Gate and randomization regressions bring the suite to 51 passing tests.
- Recovery grid 002 completed with 0/25 strict successes; every candidate's
  first latched termination was a body/link collision, rejecting the
  front-right-only offset hypothesis. A recorder audit found that auto-reset
  overwrote detailed terminal tensors for 24 already-finished environments
  while the success flags and first failure classifications remained intact.
  Grid 003 repeats the identical experiment with immediate first-terminal
  tensor copies; no controller or physics parameter changed.
- Registered a second, not-yet-executed 25-candidate recovery grid that varies
  common leg height and a right-side height differential while remaining
  within 15 mm per-wheel offsets. It contains an exact zero-offset control and
  will run only if grid 003 confirms the same terminal collision mode.
  Candidate regressions bring the suite to 53 passing tests.
- Fixed the same auto-reset evidence hazard in the formal vector evaluator:
  each scenario now copies its terminal collision, FSM trim, and joint-limit
  evidence on the first done transition. Primary time-series metrics were
  already active-masked and their definitions are unchanged. Added a separate
  count for diagnostic/FSM baseline IK fallbacks so unreachable recovery
  candidates cannot be mistaken for applied physical interventions.
- Disabled the rejected attempt-017 high-load diagonal shortening in the
  formal FSM defaults (`maximum_radial_shortening_m: 0.0`). The configuration
  retains its thresholds and failure evidence for provenance, and a regression
  prevents accidental re-enabling. The suite now reports 54 passing tests.
- Recovery grid 003 reproduced 002 with trustworthy first-terminal evidence:
  0/25 successes, 22 phase-10 and 3 phase-9 collisions, all on
  `front_right_bot`. The zero-offset control reproduced 145.55 s and
  26.8161 N; the longest-lived single-leg candidate reached only 145.85 s with
  zero front-right wheel support. The coordinated common/right-height grid 004
  is now the active diagnostic.
- Added pure formal-result aggregation primitives that require complete
  50/75/100 mm evidence, report Wilson success intervals and both all-episode
  and successful-only continuous summaries, compute equal-height-weighted
  aggregates, and reject incomplete or duplicate scenario pairing before a
  10,000-draw paired bootstrap. Synthetic tests bring the suite to 56 passing;
  no report values are emitted before real locked-test rows exist.
- Added explicit metric-window and canonical-config serialization regressions,
  including negative-margin duration, invalid-margin accounting, pitch-rate
  RMS, empty-window rejection, and key-order-independent config hashes. The
  pure-Python suite now reports 60 passing tests.
- Body-pose grid 004 completed with 0/25 successes and 25
  `front_right_bot` collisions. Seventeen candidates were fully applied with
  no IK fallback and still failed, showing that phase-9 support-plane changes
  occur too late. Added a 25-candidate phase-6 front-right hip/knee support
  posture grid wholly inside the recorded-safe command envelope, with a
  continuous ramp, hold, and clamp audit. Two regressions raise the suite to
  62 passing tests; grid 005 is now active.
- Front-support grid 005 completed with 0/25 strict successes: 23 collisions
  and two global timeouts, with zero IK fallback and zero command clamp for
  every candidate. The only collision-free phase-10 posture used front-right
  hip/knee offsets of -3/-15 deg and reached the global timeout with safe
  attitude, but its front-left/rear-right diagonal carried 0.09/0.00 N and
  therefore could not satisfy the unchanged all-wheel support dwell.
- Registered grid 006 around that measured posture. It changes no controller
  or threshold, retains an exact zero-offset reproduction, and varies only
  smooth phase-9/10 front-left and rear-right wheel-center extension from
  0 to 6 mm independently. One candidate regression raises the pure-Python
  suite target to 63 passing tests.
- Invalidated grid 006 before physics initialization because its launcher
  pre-created the output directory while the diagnostic intentionally requires
  a new directory. The `FileExistsError`, empty output directory, and sibling
  logs are preserved; no candidate step ran. The unchanged replacement is
  grid 007.
- Grid 007 completed with 0/25 successes, 18 collisions, and seven global
  timeouts. Every candidate had zero IK fallback and zero command clamp. All
  collision-free branches retained rear-right force at 0 N, rejecting static
  0--6 mm unloaded-diagonal extension.
- Grid 007 also isolated the late collision command: phase-10 failures drove
  only the front wheels backward at about -1.32/-1.31 rad/s while the rear
  wheels were stopped, after which the front-right wheel fell from the top
  plane and its lower link collided. The formal FSM now uses the
  twice-reproduced collision-free front support target and a height-conditioned
  all-wheel post-transfer drive of 0/0.15/0.3 rad/s at 50/75/100 mm.
  Two regressions raise the suite target to 65 passing tests.
- Preserved attempt 018 as a strict 100 mm `front_right_bot` collision at
  142.0333 s and 10.0646 N. The all-wheel +0.3 rad/s override was confirmed in
  terminal telemetry and removed the prior reverse-front command, but
  the apparent brief four-wheel support point was later found to contain only
  contact-force magnitudes, not the world-Z components required by success.
- Added a threshold-preserving capture rule for attempt 019: phases 9--10
  retain the height-conditioned forward command while any wheel is below the
  unchanged 2 N threshold, command all wheels zero when all four meet it, and
  resume if support drops. A regression raises the suite target to 66 tests.
- Attempt 019 produced bit-identical physical episode and telemetry hashes to
  attempt 018. A force-semantics audit found that the legacy
  `contact_force_n` columns were vector magnitudes, whereas formal success
  uses world-Z upward components; the claimed 138.05 s upward-support point is
  withdrawn.
- Added explicit magnitude and upward-force status, CSV, terminal episode, and
  diagnostic-grid fields without changing controller or physics. Attempt 020
  is an instrumentation-only repeat of the same scenario. A regression raises
  the suite target to 67 tests.
- Attempt 020 reproduced attempt 019 exactly in all 2,841 rows and 44 shared
  telemetry columns, then failed at the same 142.0333 s `front_right_bot`
  collision. Across all 301 phase-9/10 samples, all wheels were geometrically
  on top but no sample had every world-Z wheel force at or above 2 N. The best
  minimum force was only 1.1544 N at 138.05 s, on the sinking front-right
  wheel. A reusable hash-bearing contact-capture audit and two regressions
  bring the suite to 69 tests.
- Registered diagnostic grid 008 as the next single-variable experiment. It
  varies only the rear recovery path cap over 0/5/10/15/20%, with five exact
  repetitions of each value across environment indices. This directly
  re-tests the provisional 10% magnitude-based choice using the newly explicit
  upward-force evidence. Two regressions bring the suite to 71 tests.
- Rear-recovery grid 008 completed with 0/25 strict successes: 22 collisions
  and three global timeouts. Twelve phase-8 `rear_left_bot` collisions occurred
  before the varied parameter became active and are solver-index confounds.
  Every late collision remained on `front_right_bot`; the 0/10/20% timeout
  branches all ended with front-right upward force at 0 N and rear-left below
  1 N. The formal 10% replicate reproduced attempt 020 at 142.0333 s and
  10.064577 N exactly, so rear recovery fraction alone is rejected.
- Registered grid 009 to vary only phase-9/10 rear-right extension over the
  measured 0--20 mm support-plane gap. Five repeats are Latin-rotated across
  environment-index residues. The diagnostic runner now parks completed
  environments away from contact to prevent repeated auto-reset collisions
  from slowing the remaining batch. One candidate regression raises the suite
  to 72 tests.
- Rear-right grid 009 completed with 0/25 successes, 21 collisions, and four
  timeouts. The same 12 pre-intervention candidate IDs collided in phase 8 as
  grid 008. Fully applied 10/15 mm extensions produced three collision-free
  timeouts and loaded rear-right at about 14 N, but front-right remained 0 N
  and rear-left stayed below 1.1 N. The 20 mm timeout had 639 IK fallbacks and
  is ineligible as applied evidence.
- Registered grid 010 with fixed, reachable 15 mm rear-right extension and one
  varied common 0/2/4/6/8 mm extension on the newly measured unloaded
  front-right/rear-left diagonal. Added per-candidate historical best minimum
  upward force and longest all-wheel upward-force dwell fields. Two
  regressions bring the suite to 74 tests.
- Grid 010 physically completed with 0/25 successes, 18 collisions, and seven
  timeouts; all candidates had zero IK fallback. Its new trajectory-wide
  diagnostic accumulator incorrectly included initial ground support, so the
  reported 2.5--7.1 s force-only dwells and best-minimum forces are invalid
  for top capture. Formal success and terminal evidence were unaffected.
- Corrected the diagnostic accumulator to require phase 9/10, the formal
  full-top geometry/support predicate, bounded tilt/angular velocity, and an
  active non-terminal environment. Grid 011 is an instrumentation-only repeat
  of grid 010; no physical parameter changes.
- Grid 011 reproduced all 25 scalar first-terminal fields from grid 010
  exactly. The corrected audit found zero phase-9/10 samples in which any
  candidate satisfied the force-independent formal full-top eligibility
  predicate. Consequently all corrected best-minimum forces are null and all
  success-condition dwells are 0 s; continuing to tune load alone is rejected.
- Added per-wheel ordinary/full-top flags, aggregate formal top eligibility,
  support score, and wheel y positions to formal evaluator status, telemetry,
  and terminal snapshots. Attempt 021 is an instrumentation-only replay of the
  unchanged formal 100 mm controller to isolate the geometric blocker.
- Attempt 021 reproduced attempt 020 in all 2,841 rows and 48 shared telemetry
  columns. All four formal full-top flags held continuously for 2.60 s with
  support score about 0.9999, while inherited aggregate eligibility remained
  false because it also used a link-center bounding-box collision estimate.
  Formal collision policy already specifies measured ContactSensor external
  force above 5 N, and all-wheel upward support still never occurred.
- Isolated the formal aggregate in the project residual environment: full-top
  geometry, bounded tilt, and support score define top eligibility; actual
  non-wheel ContactSensor force remains the unchanged collision rejection in
  `_get_dones`. Two regressions bring the suite to 76 tests. Attempt 022 will
  repeat the controller unchanged to audit definition-only behavior.
- Attempt 022 changed exactly one of 58 shared telemetry columns:
  `all_wheels_on_top` became true in the intended 52-sample, 2.60 s full-top
  window. Every other value across 2,841 rows and the complete episode record
  matched attempt 021. No sample had all four upward forces at or above 2 N,
  and the same 142.0333 s `front_right_bot` collision remained, validating the
  definition correction without manufacturing a success.
- Registered grid 012 as an unchanged physical repeat of grid 011: fixed
  reachable 15 mm rear-right extension plus common 0/2/4/6/8 mm
  front-right/rear-left extension, five Latin-rotated repetitions. Its
  force-quality accumulator now sees the declared full-top eligibility rather
  than the rejected bounding-box proxy.
- Grid 012 reproduced every non-diagnostic first-terminal field from grid 011:
  0/25 successes, 18 collisions, and seven timeouts. Eight 2--8 mm candidates
  entered corrected full-top eligibility, but all eight had best simultaneous
  minimum upward force exactly 0 N and 0 s dwell. Eligible timeout terminals
  consistently had front-right 0 N and rear-left below 0.8 N.
- Registered grid 013 as a continuous single-variable range extension to
  8/11/14/17/20 mm, retaining the fixed 15 mm rear-right support and Latin
  rotation. Added observational eligible-sample count, per-wheel eligible
  force maxima, and best-minimum force snapshots. One regression brings the
  suite to 77 tests; no new field participates in control or termination.
- Grid 013 produced four raw strict 100 mm successes: two at 14 mm and two at
  20 mm. Their best simultaneous minimum upward force was 3.056--4.132 N, but
  all four accumulated 216--243 analytic-IK fallback steps. They are retained
  as physical mechanism evidence and explicitly rejected for FSM selection
  because the protocol forbids unreachable reference targets.
- Added per-environment phase-9 offset-ramp start control and per-leg baseline
  IK fallback counts. Grid 014 fixes the lower successful 14 mm common
  front-right/rear-left extension and 15 mm rear-right extension, then varies
  only ramp start progress over 0/0.2/0.4/0.6/0.8 with Latin rotation. Two
  regressions bring the suite to 79 tests.
- Grid 014 produced four raw strict successes. Start 0.4 repeated success with
  best minimum force 4.706--6.070 N, and start 0.8 reached a nearly balanced
  7.062 N minimum. Every success still had 92--106 fallback steps, now
  isolated exactly to the rear-left leg; other per-leg counts were zero.
- Registered grid 015 with start 0.4, front-right 14 mm, and rear-right 15 mm
  fixed. Only rear-left extension varies over 8/9.5/11/12.5/14 mm. The
  selection condition is strict environment success plus 0/0/0/0 per-leg IK
  fallback. One regression brings the suite to 80 tests.
- Grid 015 produced one raw success at the invalid 14 mm control. Its fully
  reachable 11 mm candidate reached a 2.0726 N simultaneous minimum with
  0/0/0/0 per-leg fallback, but only for one 0.01667 s step; it correctly
  failed the unchanged 1.5 s dwell. The 12.5 mm branches already had 494
  rear-left fallback steps.
- Registered grid 016 as a 0.25 mm resolution search over
  11.00/11.25/11.50/11.75/12.00 mm rear-left extension, with every other
  parameter held fixed. One regression brings the suite to 81 tests.
- Grid 016 produced strict successes at rear-left 11.5 and 12.0 mm with best
  simultaneous minimum force 6.916 and 6.204 N. Both still had exactly 90
  rear-left-only fallback steps; reachable 11.25 mm remained below 0.25 N.
- Added independent per-leg phase-9 offset-ramp starts. Grid 017 preserves
  front-right/rear-left/rear-right amplitudes at 14/11.5/15 mm and starts the
  non-rear-left legs at 0.4, while varying only rear-left start over
  0.4/0.5/0.6/0.7/0.8. One regression brings the suite to 82 tests.
- Grid 017 produced raw strict successes for rear-left start 0.5/0.6/0.8 with
  nearly balanced 6.939--6.979 N minimum force, but all retained 90--92
  rear-left-only fallback steps. The final 11.5 mm target, not ramp timing, is
  the unreachable condition.
- Registered grid 018 with rear-left fixed at its reachable 11.25 mm value,
  front-right fixed at 14 mm, and only rear-right varied over
  15.0/15.5/16.0/16.5/17.0 mm. One regression brings the suite to 83 tests.
- Grid 018 produced no strict success. Rear-right 16/17 mm briefly crossed
  2 N minimum for 0.0167/0.15 s but accumulated hundreds of rear-right-only
  fallback steps; 15 mm remained the observed zero-fallback upper bound.
- Registered grid 019 with rear-left/rear-right fixed at reachable
  11.25/15 mm and only front-right reduced over 10/11/12/13/14 mm to
  redistribute its measured 14 N load toward rear-right. One regression brings
  the suite to 84 tests.
- Grid 019 produced no strict success: 12 candidates collided in the common
  pre-offset phase and 13 timed out. Every candidate retained 0/0/0/0 IK
  fallback and zero clamp, but reducing front-right did not redistribute load;
  the sweep maximum instead occurred at 14 mm with a 1.6522 N simultaneous
  minimum and 0 s strict-condition dwell.
- Registered grid 020 as the measured-direction counter-sweep over front-right
  14.00/14.25/14.50/14.75/15.00 mm, holding rear-left/rear-right at their
  reachable 11.25/15 mm values. Any front-right fallback remains an automatic
  engineering rejection. One regression brings the suite to 85 tests.
- Grid 020 retained zero fallback and zero clamp for every candidate. At
  front-right 14.5 mm, candidate 19 reached a fully admissible 2.1649 N
  simultaneous minimum, but for only one 0.01667 s step rather than the
  required 1.5 s; therefore strict success remained 0/25.
- Registered grid 021 over front-right 15/15.5/16/16.5/17 mm with both rear
  offsets unchanged. It continues the measured load trend only until sustained
  support or a front-right-only reach violation is observed. One regression
  brings the suite to 86 tests.
- Grid 021 retained zero fallback and zero clamp through front-right 17 mm.
  The 17 mm branch reached a 2.4076 N simultaneous minimum and extended the
  strict-condition dwell to 0.15 s, still below the required 1.5 s.
- Registered terminal amplitude grid 022 over front-right
  17/17.75/18.5/19.25/20 mm. The final value is the declared diagnostic offset
  limit, so no larger amplitude will be tested. One regression brings the
  suite to 87 tests.
- Grid 022 produced two strict successes at front-right 18.5 and 20 mm. Both
  had 0/0/0/0 per-leg analytic-IK fallback and zero clamp, so both are
  engineering-admissible. The lower 18.5 mm candidate retained a 1.5 mm bound
  margin and was selected for formal reproduction.
- Added a validated formal post-transfer support-geometry section to
  `fsm.yaml`; both evaluation and PPO training now inject the same selected
  offsets into the environment. Diagnostic grids retain separate additive
  controls and therefore do not silently include the formal candidate. Two
  regressions bring the suite to 89 tests.
- Formal single-environment attempt 023 timed out. Complete-top geometry was
  true from 129.2--131.6 s, while four-wheel force support began only at
  133.6 s; continued rolling moved front-right laterally beyond the complete
  footprint before the formal geometry could load.
- Post-transfer capture now stops wheel drive on either complete all-wheel
  geometry or four-wheel force support. This does not relax success; it
  preserves the earlier valid geometry while the selected reachable support
  offsets build load. One regression brings the suite to 90 tests.
- Formal attempt 024 succeeded on the same single 100 mm scenario at 134.8 s.
  Terminal complete-top flags were all true, upward forces were
  5.058/10.542/9.519/3.628 N, and baseline IK fallback was zero.
- Added per-leg baseline-IK fallback and formal clamp counts to evaluator
  episode artifacts before the full development batch. One regression brings
  the suite to 91 tests.
- Full 100 mm development batch attempt 025 produced 7/20 strict successes
  (35%), seven phase-8 `rear_left_bot` collisions, and six timeouts. Every
  episode retained 0/0/0/0 IK fallback and zero clamp. This is a valid but
  low-success FSM baseline, not a robustness claim.
- Full 50 mm development batch attempt 026 produced 0/20 strict successes:
  seven `front_right_bot` collisions, one FSM phase timeout, and 12 global
  timeouts. Applying the 100 mm support offsets unchanged caused 9,235
  rear-left analytic-IK invalid samples; all clamp counters remained zero.
- Formal post-transfer support geometry is now linearly height-conditioned:
  50/75/100 mm use 0/50/100% of the selected 100 mm offsets. Effective
  offsets are recorded in evaluation and training provenance. One regression
  brings the suite to 92 tests.
- Fifty-millimetre smoke attempt 027 repeated the exact scenario that timed
  out in attempt 026 and reached strict success at 133.45 s. Terminal upward
  forces were 5.859/8.174/8.494/6.154 N, analytic-IK fallback was 0/0/0/0,
  and the clamp count was zero.
- Full 50 mm development batch attempt 028 produced 12/20 strict successes
  (60%), seven `front_right_bot` collisions, and one FSM phase timeout. All
  20 episodes retained 0/0/0/0 analytic-IK fallback and zero clamp. The same
  12 branches that globally timed out under unscaled geometry in attempt 026
  now completed strictly; the earlier collision branches remain visible.
- Full 75 mm development batch attempt 029 produced 0/20 strict successes;
  all failures were `front_right_bot` collisions. The 50%-scaled geometry was
  reachable with zero IK fallback and zero clamp, but no episode recorded one
  complete all-wheel-top sample. A 50--100% amplitude-only diagnostic grid
  was registered; one regression brings the suite to 93 tests.
- Diagnostic grid 030 produced 0/25 successes. Common 50% geometry remained
  fully reachable but collided 5/5; every 62.5--100% candidate accumulated
  rear-left-only IK fallback while still never entering complete all-wheel
  top geometry. A front-right-only continuation with reachable half-scale
  rear support was registered; one regression brings the suite to 94 tests.
- Diagnostic grid 031 produced 0/25 successes. Every 9.25--18.5 mm
  front-right target remained reachable with zero clamp, but phase-9
  activation was too late to recover geometry lost in phase 8. Per-leg
  diagnostic activation phases and a phase-7 amplitude/timing grid were
  added without changing formal defaults; two regressions bring the suite to
  96 tests.
- Diagnostic grid 032 produced 0/25 successes. Every phase-7 amplitude/timing
  combination remained zero-fallback and zero-clamp but still never entered
  complete all-wheel-top geometry. A phase-7/8 front-versus-rear wheel-speed
  diagnostic override was added with the original +0.3 rad/s as its formal
  default; two regressions bring the suite to 98 tests.
- Diagnostic grid 033 produced 0/25 successes but isolated a useful speed
  split: zero front-wheel speed with +0.3 rad/s rear speed produced 2,599
  complete-top eligible samples, a best 8.365 N simultaneous minimum force,
  and 0.2833 s maximum strict dwell, all with zero fallback/clamp. A combined
  front-right-amplitude grid was added; one regression brings the suite to 99
  tests.
- Diagnostic grid 034 produced 0/25 successes and 25 global timeouts. Every
  front-right amplitude from 9.25 to 18.5 mm entered complete-top geometry
  with zero fallback/clamp, but the best strict dwell was only 0.05 s and the
  response was non-monotonic. Front-right amplitude is rejected as the
  missing mechanism. A development-only phase-9/10 forward-speed override
  and a 0--0.15 rad/s grid were added without changing the formal NaN-default
  path; two regressions bring the suite to 101 tests.
- Diagnostic grid 035 produced 0/25 successes and 25 global timeouts, with
  zero fallback/clamp throughout. A 0 rad/s replicate was still in a strict
  four-wheel-force state at the 150 s cutoff after 0.5667 s continuous dwell;
  a 0.075 rad/s replicate similarly ended after 0.4 s. The fixed metric and
  timeout are unchanged. A grid that moves only the same support geometry
  earlier in phase 8/9 was registered; one regression brings the suite to 102
  tests.
- Diagnostic grid 036 produced 0/25 successes. Phase-8 activation at progress
  0.5/0.75 accumulated 5,444/4,809 analytic-IK fallback samples and is
  engineering-rejected. Reachable phase-9 starts at 0/0.2/0.4 peaked at only
  0.0167/0.3333/0.1 s strict dwell, so timing-only searches stop. A
  development-only per-environment high-load shortening bound was added for a
  0--2 mm load-redistribution grid; formal configuration remains disabled.
  Two regressions bring the suite to 104 tests.
- Diagnostic grid 037 produced 0/25 successes but validated the measured load
  direction with zero fallback/clamp. The controller shortened only
  front-left/rear-right. Maximum dwell increased from the 0 mm baseline's
  0.5667 s to 1.35 s at 1 mm and 1.25 s at 2 mm; the 2 mm group had the best
  mean dwell and a balanced 7.729/6.589/7.131/7.211 N terminal snapshot.
  A fixed-2-mm rate grid was registered; one regression brings the suite to
  105 tests.
- Diagnostic grid 038 produced the first strict 75 mm success: 1/25 overall,
  at a 0.75 mm/s shortening rate and fixed 2 mm limit. It terminated naturally
  at 149.833 s with 7.999/5.954/6.692/7.957 N upward forces, zero
  fallback/clamp, and only the measured high-load diagonal shortened. A
  combined post-transfer-speed grid was registered to improve repeatability;
  one regression brings the suite to 106 tests.
- Diagnostic grid 039 produced 3/25 strict successes, one each at
  0.075/0.1125/0.15 rad/s post-transfer speed. All candidates retained zero
  fallback/clamp and all three successes had balanced terminal upward force.
  The 0.075 rad/s group had the best mean dwell at 1.0067 s and was selected
  for a 25-environment exact-candidate repeat; one regression brings the suite
  to 107 tests.
- Diagnostic grid 040 repeated the exact selected 75 mm controller 25 times
  and produced 4/25 strict successes (16%), with 21 timeouts. All branches had
  0/0/0/0 fallback, zero clamp, and exactly 2/0/0/2 mm terminal shortening.
  The repeated nonzero candidate is selected for height-conditioned formal
  promotion; formal evaluator results remain pending.
- The grid-040 combination is now encoded as the formal 75 mm anchor under
  `fsm.yaml` SHA-256
  `1943be80e44e57ff63b479195970e0e02d0bad6f22bc4712337cec51fae243af`.
  Its phase-7/8 wheel speeds are 0/0/0.3/0.3 rad/s, phase-9/10 forward speed
  is 0.075 rad/s, and high-load radial shortening is bounded at 2 mm with a
  0.75 mm/s rate. Explicit piecewise height anchors preserve the prior 50 and
  100 mm wheel-speed behavior and disable shortening at both endpoints.
  Evaluation and training now parse, validate, apply, and record all effective
  policy values. Three regressions bring the suite to 110 passing tests;
  formal simulator evaluation remains pending.
- Formal 75 mm smoke attempt 041 executed successfully but the selected
  development scenario timed out, for a strict result of 0/1. The terminal
  state had all four full wheels on top, upward forces
  9.894/3.807/4.102/10.722 N, support score 0.9999503, zero fallback/clamp,
  no non-wheel collision, and 2/0/0/2 mm shortening. The failed artifact is
  retained; because the source diagnostic candidate measured only 4/25
  successes, the planned full 20-scenario formal batch remains required.
- Formal 75 mm full attempt 042 produced 7/20 strict successes (35%); all 13
  failures were global timeouts and there were no collision failures. All 20
  scenarios retained 0/0/0/0 analytic-IK fallback, zero clamp, and no
  terminal non-wheel contacts; 19/20 ended with all four full wheels on top.
  Successful termination occurred only at 147.85--149.90 s, so this is a
  feasible but low-margin FSM baseline. Current-config endpoint revalidation
  at 50 and 100 mm remains required before freezing.
- Current-config 50 mm attempt 043 reproduced 12/20 strict successes (60%),
  seven `front_right_bot` collisions, and one FSM phase timeout exactly as in
  attempt 028. Provenance records the preserved endpoint values: four
  +0.3 rad/s rear-transfer wheel speeds, zero post-transfer speed, zero
  support geometry, and zero unload bound. All 20 branches had zero
  fallback/clamp and zero unload trim.
- Current-config 100 mm attempt 044 reproduced 7/20 strict successes (35%),
  seven `rear_left_bot` collisions, and six global timeouts exactly as in
  attempt 025. Provenance records four +0.3 rad/s rear-transfer speeds,
  +0.3 rad/s post-transfer drive, full selected support geometry, and a zero
  unload bound. All 20 branches had zero fallback/clamp and zero unload trim.
- With same-selection-config results of 12/20, 7/20, and 7/20 at
  50/75/100 mm, the FSM and metric definitions were frozen. The only change
  after the development runs was the top-level administrative `frozen` field;
  both selection and final hashes are retained in `config_freeze.json`.
- Method-B PPO smoke attempt 045 failed before agent initialization because
  local skrl 2.0.0 uses `PPO_CFG.gae_lambda` rather than the legacy dictionary
  key `lambda`. Local source inspection also confirmed that positive
  `value_clip` already enables predicted-value clipping and that the separate
  `clip_predicted_values` key is unsupported. The semantic lambda value is
  now mapped to `gae_lambda`, the redundant flag is removed, and an explicit
  unknown-key check was added before agent construction. No checkpoint or
  training timestep was produced by the retained failed attempt.
- Method-B seed-11 50 mm smoke attempt 046 passed in 16 Isaac environments.
  Actor observations were 16×96, asymmetric Critic states were 16×146,
  contact force was finite, and zero residual exactly reproduced the frozen
  FSM. This is preflight evidence only and is not counted as training.
- Method-B seed-11 50 mm training attempt001 failed on its first Trainer
  action request before any transition: the Actor incorrectly read the
  146-dimensional privileged Critic state instead of its 96-dimensional
  observation. The Actor now exclusively reads `inputs["observations"]`, a
  regression confirms privileged-state changes cannot affect it, and the
  integration preflight now calls `agent.act`. One regression brings the
  suite to 111 tests; the failed run has no checkpoint or training data.
- The first expanded smoke attempt047 called `agent.act` before local skrl's
  Trainer initialized Gaussian action bounds and failed without a transition.
  Trainer construction now precedes the Actor/Critic preflight on both smoke
  and training paths, matching the installed skrl lifecycle. The preflight
  also verifies the finite privileged Critic value.
- Smoke attempt048 then exposed that IsaacLab's integer action-space
  declaration is represented as an unbounded 12-D Box. The residual
  environment's actual contract is normalized `[-1, 1]`, so the policy now
  supplies those finite bounds to skrl's Gaussian sampler. This both resolves
  the `None` clip-bound failure and keeps sampled log-probabilities consistent
  with executed actions. One regression brings the suite to 112 tests.
- Method-B seed-11 50 mm smoke attempt049 passed the complete initialized
  integration path in 16 Isaac environments: finite 96-D Actor observations,
  finite 146-D privileged Critic states and values, finite bounded 12-D policy
  samples, finite contacts, and exact zero-residual FSM equivalence. It
  contributes no optimization transitions and authorizes full training
  attempt002.
- Method-B seed-11 50 mm training attempt002 completed four finite checkpoints
  through 6,400 timesteps, then failed when two environments entered the first
  partial reset. A per-environment wheel-radius tensor had not been subset by
  `env_ids`; the initial 64-of-64 reset hid the shape error. The reset now uses
  matching indices, smoke explicitly forces a two-environment partial reset,
  and recovery provenance records a 6,400-step offset so only the remaining
  12,800 steps count toward the original 19,200-step budget. One regression
  brings the suite to 113 tests.
- Partial-reset smoke attempt050 passed in 16 real Isaac environments,
  including an explicit two-environment reset with finite resulting root
  poses. The original Actor/Critic/contact/zero-residual preflight also
  remained valid, authorizing recovery from the finite 6,400-step checkpoint.
- Method-B seed-11 50 mm recovery attempt003 loaded the exact hashed
  6,400-step checkpoint and completed the remaining 12,800 timesteps. The
  audited chain therefore matches the original 19,200-timestep /
  1,228,800-transition budget exactly. Its final checkpoint contains 77
  finite tensors and is now subject to the registered deterministic
  20-episode development promotion gate; training completion itself is not a
  promotion.
- Development-gate attempt001 failed before any episode because the evaluator
  used the removed skrl `set_running_mode` API and omitted the training-time
  value preprocessor while loading the checkpoint. Evaluation now uses
  `enable_training_mode(False, apply_to_models=True)`, restores all three
  training preprocessors, and retains deterministic `mean_actions`.
  One regression brings the suite to 114 tests.
- Diagnostic development-gate smoke attempt002 restored the complete
  checkpoint without warnings, ran deterministic mean actions for 298 control
  steps, and wrote hashed episode/status/telemetry artifacts. Its deliberately
  truncated 5-second `0/1` outcome is excluded from performance statistics;
  it authorizes the unchanged full 20-scenario, 150-second gate.
- Full Method-B seed-11 50 mm development gate attempt003 executed all 20
  scenarios but produced 0/20 successes: 19 body/link collisions (16
  `front_right_bot`, three `rear_right_bot`) and one timeout. Residual
  saturation and baseline IK fallback were both zero. The deterministic
  policy emitted a large nonzero residual from the initial state. Inspection
  found that per-step top-contact/recovery rewards accumulate thousands of
  units while collision is penalized once by only 10 units, matching the
  observed high training return despite zero safe completions. A numbered
  common-reward revision is required; the method is not promoted.
- Common PPO reward v2 is registered in `ppo_common.yaml` SHA-256
  `034019e479cbe64fd5b1b8d5207a55920a72cadb094f394dcbbffcdd9e5d127e`.
  Top-contact and recovery occupancy terms now integrate in seconds,
  success/collision weights are +200/-200, and residual/action-rate
  regularization is strengthened. B and C still differ only by method label
  and CoM weight. Evaluator provenance now hashes the common and method
  configs and records every effective weight. Evaluation telemetry now
  includes the full policy-to-actuator residual chain, including terminal
  pre-reset snapshots. Three regressions bring the suite to 117 tests.
- Method-B reward-v2 seed-11 50 mm smoke attempt001 passed in 16 real Isaac
  environments, including effective-weight provenance and the forced
  two-environment reset. It contributes zero transitions and authorizes a
  from-scratch full-budget run; no reward-v1 checkpoint is reused.
- Method-B reward-v2 seed-11 50 mm training attempt001 completed from random
  initialization with the exact registered 19,200-timestep /
  1,228,800-transition budget across 64 environments. The final checkpoint
  SHA-256 is
  `c02026df0f913c6761e1354f6026928421896d5e570dd1e1c848ce13852d8706`;
  all 77 stored tensors and all 300 final training-scalar updates are finite.
  This is training evidence only; curriculum promotion still requires the
  deterministic final-policy development gate.
- Reward-v2 development-gate smoke attempt001 restored the final Method-B
  checkpoint and executed deterministic mean actions for one deliberately
  truncated 5-second scenario. Its 100×122 telemetry table has uniform row
  width, finite numeric values, and the complete 64-field action-to-actuator
  chain. The diagnostic `0/1` timeout is excluded from performance evidence
  and authorizes the unchanged full 20-scenario gate.
- The full reward-v2 Method-B gate completed all 20 fixed 50 mm scenarios but
  failed promotion at `0/20`. All failures were late non-wheel collisions
  after substantial forward progress: 18 on `front_right_bot` and two on
  `rear_right_bot`. Expanded telemetry showed systematic phase-8 left/right
  residual asymmetry, including +4.64 mm rear-left versus approximately zero
  rear-right dx and opposing front wheel-speed residual signs. Reward v3 is
  therefore limited to common residual safety regularization and a smaller
  wheel-speed residual bound; the frozen FSM, metrics, success definition,
  architecture, seeds, budgets, and B/C-only CoM difference remain unchanged.
- Common reward v3 (`reward-v3-symmetry-anchor`) increases normalized
  residual-magnitude regularization from -0.05 to -0.5, adds a -1.0
  left/right residual-asymmetry term, and reduces only the wheel-speed
  residual bound from 0.35 to 0.20 rad/s. The common config SHA-256 is
  `337defd27f0020a0d45dd47e13ea774be42ae25d9998c333a2ace675c6c2a50f`
  (canonical config SHA-256
  `922db2f38ac49803d7d5302593bcee4711eb005b7790aaa738353c2cfbc6cc19`).
  FSM/metrics hashes remain frozen and all 117 tests pass.
- Reward-v3 smoke attempt001 passed all 16-environment runtime checks, but its
  result only evidenced the new 0.20 rad/s wheel residual bound through the
  complete config hash. Trainer and evaluator provenance now also serialize
  the three effective residual bounds directly. The first smoke remains
  preserved and a numbered repeat is required before training.
- Reward-v3 smoke attempt002 passed the same real-Isaac runtime checks and
  directly recorded effective residual bounds of 0.015 m x, 0.020 m z, and
  0.20 rad/s wheel speed, together with both new common reward weights. It
  authorizes a from-scratch Method-B seed-11 50 mm full-budget run.
- Method-B reward-v3 seed-11 50 mm training attempt001 completed from random
  initialization with the exact 19,200-timestep / 1,228,800-transition
  budget. The final checkpoint SHA-256 is
  `d3509ab1dbebc658cefdbf00aef77766e4ec574263c5c8c99ca3dfef1ad62a2e`;
  all 77 stored tensors and all 300 final scalar updates are finite. Training
  completion is not curriculum promotion.
- Reward-v3 evaluator smoke attempt001 failed before environment construction:
  the new direct-bound provenance field referenced `cfg` before assignment.
  No episode or policy action occurred. Bound serialization now follows
  environment-config construction; pycompile and all 117 tests pass, and a
  numbered smoke repeat is required.
- Reward-v3 evaluator smoke attempt002 passed with the exact final checkpoint,
  direct 0.015/0.020/0.20 residual-bound provenance, and 100×122 finite
  telemetry containing all 64 action-chain fields. Its deliberate 5-second
  timeout is excluded from performance and authorizes the full gate.
- The full reward-v3 Method-B gate produced 2/20 successes, 12
  `front_right_bot` collisions, two phase timeouts, and four global timeouts.
  This improved on reward v2's 0/20 and 20 collisions: phase-8 mean action L2
  fell from 0.667 to 0.289 and mean collision force fell from 14.20 to
  10.15 N. It remains below both the 16/20 gate and the frozen FSM's 12/20,
  so reward v4 will further preserve the baseline with stronger common
  residual anchoring and half-size physical residual bounds.
- Common reward v4 (`reward-v4-baseline-preservation`) sets normalized
  residual-magnitude/asymmetry weights to -2/-3 and physical x/z/wheel
  residual bounds to 0.0075 m, 0.010 m and 0.10 rad/s. Its common config
  SHA-256 is
  `b3417383ecb3ab22436764a33c57adb5a374897f87ae680f38bbe64c2275699a`
  (canonical
  `08b55672d151650699dc16b26498979c0ec5f21a5ee2875630377b981498629c`).
  Frozen hashes remain unchanged and all 117 tests pass.
- Reward-v4 Method-B seed-11 50 mm smoke attempt001 passed all 16-environment
  real-Isaac checks and directly recorded the 0.0075/0.010/0.10 bounds and
  -2/-3 regularization weights. It authorizes a from-scratch full-budget run.
- Method-B reward-v4 seed-11 50 mm training attempt001 completed from random
  initialization with the exact 19,200-timestep / 1,228,800-transition
  budget. The final checkpoint SHA-256 is
  `e23b091a4a3f05b2092963a3960df7b1a2539a3e62072cb095b375e8587b87f0`;
  all 77 stored tensors are finite and every core optimization series has
  300 finite updates through timestep 19,200. Training completion is not
  curriculum promotion.
- Reward-v4 evaluator smoke attempt001 restored that exact final checkpoint
  and executed deterministic mean actions for one deliberately truncated
  five-second development scenario. Its 100×122 finite telemetry contains
  the complete 64-field action-to-actuator chain and direct v4 bounds/weights.
  The diagnostic timeout is excluded from performance and authorizes the
  unchanged full 20-scenario gate.
- The full reward-v4 Method-B gate produced 5/20 successes, eight
  `front_right_bot` collisions, three phase timeouts, and four global
  timeouts. All nine delay-2 scenarios failed, while the five successes used
  delay 0 or 1; training had used only nominal delay 0 and no randomization.
  Audit also found that a one-second stuck occupancy cost -360 at 60 Hz,
  worse than the one-time -200 collision penalty, and that phase-local
  progress reward cancelled at phase transitions. Reward v5 will fix these
  common credit-assignment defects and train on bounded disturbances without
  changing the frozen controller or metrics.
- Common reward v5 (`reward-v5-robust-credit`) integrates stuck occupancy in
  seconds and replaces phase-local progress with the non-negative delta of
  `fsm_phase + phase_progress`. The 50 mm training stage now uses bounded full
  variation: ±25 mm distance, ±0.020 rad pitch, friction 0.90--1.20, delay
  0--2 steps, and sensor noise 0--0.005. V4's residual bounds and safety
  weights are unchanged. The common config SHA-256 is
  `356b3144ac2175b21380d8accb33b8e0ad6190e93fbb78e256a7a69323e3451a`
  and all 119 tests pass with frozen FSM/metrics hashes unchanged.
- Reward-v5 Method-B seed-11 50 mm smoke attempt001 passed all real-Isaac
  preflight checks with 16 environments and direct full-randomization
  provenance. It contributes zero optimization transitions and authorizes
  the exact registered from-scratch training run.
- Reward-v5 Method-B seed-11 50 mm full training attempt001 was safely aborted
  at progress 9,517/19,200 after the 9,024-step episode report proved a second
  reward-scale defect: a 168-step termination returned -17.6176 while long
  episodes averaged -1,486.234. Fall, numerical failure, and phase timeout
  terminated without terminal penalties; several continuous costs were also
  charged at 60 Hz rather than integrated over time. The finite
  `agent_8000.pt` is retained but objective-ineligible, and the run contributes
  zero accepted budget. Reward v6 will correct only these common reward
  semantics before a new from-scratch attempt.
- Common reward v6 (`reward-v6-continuous-safety`) integrates seven continuous
  state/rate terms by `step_dt` and gives fall, body collision, numerical
  failure, phase timeout, and joint-limit termination explicit -200 terms.
  The common config SHA-256 is
  `c416ea5ad8dc4836f5f97d3e9da95869baea5cc25a6008edfa1c233f972c2a32`
  (canonical
  `e395947b685c129a4047b3cb6a918d734cc673488dc0db056c8688d989949831`).
  All 120 tests pass; frozen FSM, metrics, asset, action, PPO, randomization,
  seed, and B/C-ablation controls remain unchanged.
- Reward-v6 Method-B smoke attempt001 returned `SMOKE_PASS`, but post-review
  found it did not enumerate the runtime raw reward tensors or hash the exact
  executed reward/environment/model/trainer sources. It is retained as
  superseded audit evidence. The preflight now makes those checks mandatory;
  attempt002 will repeat the smoke before full training.
- Smoke attempt002 passed the 22-term runtime finite check and exact source
  provenance. Because it observed safety terms only on nonterminal steps, it
  is also retained as superseded evidence. The smoke-only branch now forces
  one real fall transition and requires an exact -200 weighted fall term
  before it can authorize full training.
- Smoke attempt003 failed the new compound forced-fall assertion. Its first
  implementation did not serialize the individual subconditions before
  raising, so no diagnosis is inferred from the compound failure alone.
  Framework source confirms dones precede rewards. Attempt004 will record
  every sub-result before applying the same assertion.
- Attempt004 proved the forced low-root transition terminated with a finite
  -200.009903 total reward, but via body collision rather than the fall
  predicate. The valid collision-path evidence is retained. Attempt005 lifts
  the robot and applies a 1.4 rad roll to isolate the tilt-fall path.
- Attempt005 passed every real-Isaac preflight. The isolated tilt fall produced
  raw fall 1.0, weighted fall -200.0, `terminated=true`, and finite total
  reward -200.193939. All 22 runtime terms, exact source hashes, frozen hashes,
  full randomization bounds, zero residual, interfaces, contacts, and partial
  reset are recorded. It authorizes the exact v6 from-scratch full run.
- Reward-v6 full training was safely aborted at progress 10,057/19,200. At
  step 9,024, paired skrl episode arrays contained a 168-step positive-return
  episode. Audit found randomized auto-reset mixed a newly written default
  root pose with stale terminal link/wheel caches, allowing a new episode to
  start near/on the obstacle. V6 reward safety worked, but the training
  distribution was invalid. Runtime v7 will compute reset placement solely
  from cached standing geometry and registered scenario values.
- Runtime v7 (`runtime-v7-reset-safe`) removes all current root/body reads from
  randomized reset placement. A new pure-geometry regression verifies desired
  front-wheel distance and ground clearance; all 121 tests pass. Common config
  SHA-256 is
  `049386620349475e3c2c6800de3a9911ee9a8ec2e817c0bc75fb433e992e5ac1`
  (canonical
  `cb706674975c45f2297f1522f5484302f4d4085ed4d76bd80542bbd2eaa3ce2e`).
- V7 smoke attempt001 passed a terminal-over-obstacle auto-reset test. The
  next-step distance error was 1.327 mm with no immediate success or
  termination, directly closing the v6 reset-contamination defect.
- V7 Method-B seed-11 training completed the exact 19,200/1,228,800 budget.
  Final checkpoint SHA-256 is
  `0f00a8207fff1fb096f9124f4e9b0df47cae9d9d579914913f47ef5f90ab704d`;
  all 77 tensors and all 300 core scalar updates are finite.
- A minimal reproduction corrected the earlier interpretation of the
  168-step TensorBoard segment: skrl 2.0 resets environment 0's display
  accumulator whenever any `[N,1]` done index is processed. The six rolling
  episode display series and skrl “best” marker are non-authoritative; PPO
  memory/updates and the explicit final checkpoint are unaffected.
- V7 evaluator smoke restored the exact final checkpoint and produced
  100x122 uniform telemetry with all 64 action-chain fields finite. Its
  deliberate five-second timeout is excluded and the 20-scenario gate is
  authorized.
- The full v7 50 mm development gate passed execution but failed promotion at
  2/20. Failures were six phase-8 `front_right_bot` collisions, two phase-10
  `rear_right_bot` collisions, one phase-9 FSM phase timeout, and nine global
  timeouts all ending in phase 10. All nine delay-2 scenarios failed.
- Paired scenario audit showed that v7 retained none of the frozen FSM's 12
  successes; its two successes rescued two different baseline failures.
  Deterministic mean action L2 increased from 0.11758 in v4 to 0.24512 in v7.
  Converting residual regularizers to per-second integrals while retaining
  their old per-step `-2/-3` weights weakened baseline anchoring by about 60x.
  V8 will restore the intended per-second scale, suppress residual execution
  in approach/terminal-settle phases, and locally repair the skrl display
  accumulator before retraining from scratch.
- Common runtime/reward v8
  (`runtime-v8-phase-safe-tracker-audited`) is registered with physical
  residual execution limited to FSM phases 2--9 and time-integrated residual
  magnitude/asymmetry weights of -120/-180 per second. The latter exactly
  restores v4's -2/-3 per-step strength at 60 Hz.
- Training now uses a local `AuditablePPO` subclass that calls the unmodified
  PPO transition/memory path and then repairs only the two skrl display
  accumulators with first-axis done indexing. Pure-torch regressions reproduce
  done rows 5/7 without clearing row 0. The suite passes 126 tests; frozen
  FSM, metrics, and asset hashes remain unchanged.
- V8 common config SHA-256 is
  `e97d76f169b08d4b3503a5ad74c26e9077664fb2aef7c92fb74874d4a6dc0333`
  (canonical
  `a571f9c16d30593b133d1cd78adf33288fe9ce1f4bffb3bd749d22ac117b0200`).
- V8 Method-B seed-11 50 mm smoke attempt001 passed in 16 real Isaac
  environments. The runtime phase-1/2/10 scaled-residual maxima were exactly
  0 / 0.0500000007 / 0, the local tracker audit preserved env 0 when envs
  5/7 ended, and the isolated fall retained an exact -200 term. Post-terminal
  reset distance error was 1.327 mm with no immediate success/done.
- V8 Method-B seed-11 full training completed the exact
  19,200/1,228,800 budget from scratch. Final checkpoint SHA-256 is
  `8a5b9520dad5ecc928623da2d52e5bf08b44611db6fd985bed93f949fb243ae2`;
  all 77 tensors/785,093 elements and all 300 core scalar updates are finite.
- The repaired tracker produced 40 finite episode windows with lengths
  3,814--8,999 and no false 168-step env-0 segment. Training observed 15
  success-bonus windows and 24 safety-terminal windows. These are integrity
  signals only; promotion still requires the independent deterministic gate.
- V8 evaluator smoke restored the explicit final checkpoint and produced a
  uniform 100x122 telemetry table with all 64 action-chain fields finite.
  During phases 0/1, policy action max-abs was 0.07633 while all physical
  scaled residuals were exactly zero. Its deliberate timeout is excluded.
- The full v8 50 mm development gate passed execution but failed promotion at
  10/20. It retained eight of the frozen FSM's 12 successes, rescued baseline
  failures 0008/0013, and improved the delay-2 subgroup from v7's 0/9 to 4/9.
  Failures were three phase-8 front-right collisions, three phase-9 phase
  timeouts, and four phase-10 global timeouts ending with full-top `1110`.
- V8 emitted no failure before phase 8, but successful trajectories took
  approximately 133--135 seconds versus the frozen FSM's approximately
  44 seconds. Phase-9 telemetry retained systematic rear-wheel residuals.
  Runtime v9 will therefore preserve the exact FSM in phases 0--6 and 9--12
  and execute bounded residuals only in the critical rear-transfer phases
  7--8; all other common controls remain unchanged.
- Common runtime v9 (`runtime-v9-transfer-only`) is registered with physical
  residual execution limited to phases 7--8. Its raw common-config SHA-256 is
  `52311feb78d8ad1ef2741c7bc0408a24af8e9cbefc4970e3929c698035f9d138`
  (canonical
  `1f82953b32dd6c39dfba43841f09e5610e7d0a399777f70ab80eb8334ac064af`).
  The smoke phase probes are now derived from the registered window rather
  than hard-coded. All 126 unit tests pass; the frozen FSM, metrics, and asset
  hashes remain unchanged.
- V9 Method-B seed-11 50 mm smoke attempt001 passed in 16 real Isaac
  environments. The window-derived phase-6/7/8/9 scaled-residual maxima were
  exactly `0 / 0.0500000007 / 0.0500000007 / 0`; tracker, terminal-safety,
  finite-interface, and clean post-terminal reset audits also passed.
- V9 Method-B seed-11 full training completed exactly
  19,200/1,228,800 steps/transitions from scratch in 42:22. Final checkpoint
  SHA-256 is
  `fafc0ada9dadb12f49ebe98d7fbc258ff432d0a20d2ade3d2af6cccfb8834140`;
  all 77 tensors/785,093 elements and all 300 core scalar updates are finite.
- The repaired tracker produced 36 finite episode windows with lengths
  6,445--8,999 and no false 168-step segment. Training observed both
  success-bonus and safety-terminal transitions. These remain integrity
  signals only; independent deterministic evaluation is required.
- V9 evaluator smoke restored the explicit final checkpoint and produced a
  uniform 100x122 table with all 64 action-chain fields finite. During phases
  0/1, policy action max-abs was 0.07747 while all physical scaled residuals
  were exactly zero. Its deliberate five-second timeout is excluded.
- The full v9 50 mm development gate passed execution but failed promotion at
  6/20. Failures were eight front-right lower-link collisions, two phase-9
  timeouts, and four phase-10 global timeouts. V9 retained only four frozen
  FSM successes and rescued two baseline failures.
- Direct re-audit corrected an earlier duration claim: the frozen FSM's 12
  successes terminate at 133.20--134.45 seconds, not approximately 44
  seconds. Thus 19,200 local steps provide only about 2.1 complete episode
  horizons per environment even with the v9 phase window.
- V9 learned positive front wheel-center z residuals and weak rear lift;
  safer v8 phase-8 successes showed the opposite vertical pattern. V10 will
  add a front-down/rear-up physical z-direction projection, separately expose
  projected actions, and use a 76,800-step full-development budget.
- Common runtime v10 (`runtime-v10-direction-safe-full-exposure`) is
  registered. Its phase-7--8 applied actions project front z non-positive and
  rear z non-negative; raw 12-D actions remain visible and regularized.
  Evaluator `executed_action_*` now records the actual projected action.
- V10 registers 76,800 local timesteps per stage for both B and C. Common
  config SHA-256 is
  `06b96fbd4009630e7b68fe04aa387583848c8685fcbcbc91f99c1d2b57f3526c`
  (canonical
  `a8bf1626c55c98f6d80ed7d812efa56e657ff869d7f6cec455f82440026fe17c`).
  All 129 tests and Python compilation pass; frozen hashes are unchanged.
- V10 Method-B seed-11 smoke passed in 16 real Isaac environments. The
  phase-6/7/8/9 scaled maxima were `0/nonzero/nonzero/0`, and all-positive raw
  actions projected to front/rear z `[0, 0, 0.5, 0.5]`. Tracker, -200
  terminal safety, finite-interface, and clean-reset audits also passed.
- V10 Method-B seed-11 full development completed exactly
  76,800/4,915,200 steps/transitions from scratch in about 2:42. Final
  checkpoint SHA-256 is
  `679461e49cae1c5579496da4709619ffa76cc771a15aa53fdc86398780ea3aa4`;
  all 77 tensors/785,093 elements and all 1,200 core updates are finite.
- The repaired tracker produced 364 finite episode windows with lengths
  3,822--8,999 and no false 168-step segment, providing roughly ten times the
  completion feedback of v9 medium training. Performance still requires
  independent deterministic evaluation.
- V10 evaluator smoke restored the explicit final checkpoint and produced a
  uniform 100x122 table with 64 finite action-chain fields. During phases 0/1
  policy max-abs was 0.10223 while projected executed actions and scaled
  residuals were both exactly zero. Its five-second timeout is excluded.
- The full v10 50 mm development gate passed execution but failed promotion
  at 2/20. It retained only frozen-FSM success 0010, rescued 0013, and lost
  eleven baseline successes. Failures were ten collisions, five phase-9
  timeouts, and three phase-10 global timeouts; nine collisions were
  phase-8 `front_right_bot` events.
- V10 phase-8 policy z means again occupied the rejected direction
  (front-up/rear-down), so the one-sided clamp produced almost no physical z
  correction and a flat action-to-outcome region. PPO shifted authority into
  unrestricted front x and wheel-speed channels; front-right x changed from
  about +0.2 mm in v8 successes to about -0.36 mm in v10 collision rows.
- V11 will test z-only signed-magnitude execution
  (`front=-abs(raw)`, `rear=+abs(raw)`) with x and wheel-speed residuals
  masked exactly to zero. A real-Isaac smoke and a frozen-development
  counterfactual using the existing v10 checkpoint must precede any new
  full-budget training.
- Runtime v11 (`runtime-v11-z-only-signed-magnitude`) is registered with the
  same phase-7--8 window, 12-D actor, reward, PPO, randomization, seeds, and
  76,800-step budget. Its physical action mask is
  `[0,1,0,1,0,1,0,1,0,0,0,0]`; enabled z values use front-negative and
  rear-positive signed magnitudes.
- V11 common config SHA-256 is
  `7a37e165aa803e1c876fd3b7c30194078f4b93895f1d18430300ee4d16daafa3`
  (canonical
  `1dc76d4f27011e6ac17d69f920b377a3e8b2e61ae5387ffbb733312524f4136d`).
  All 130 tests and Python compilation pass; frozen hashes are unchanged.
- V11 Method-B seed-11 real-Isaac smoke passed in 16 environments. The
  phase-6/7/8/9 scaled maxima were
  `0/0.0049999999/0.0049999999/0`. All-positive raw actions produced exactly
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`; tracker, -200 terminal safety,
  finite-interface, and clean-reset audits also passed.
- The v11 deterministic evaluator smoke restored the exact v10 final
  checkpoint and produced 100x122 finite telemetry. In phases 0/1, policy
  max-abs was 0.10223 while executed and scaled residuals were exactly zero.
  Its deliberate five-second timeout is excluded.
- The full v11/v10-checkpoint development counterfactual completed at 7/20,
  versus 2/20 for the same checkpoint under v10 physical semantics. The
  exact mask restored six frozen-FSM successes and rescued 0013; all eight
  masked action channels remained exactly zero and all z signs were correct.
- Remaining failures were six phase-8 front-right collisions, five phase-9
  timeouts, and two phase-10 timeouts. This diagnostic checkpoint is not
  promotion-eligible. The material +5 paired improvement authorizes a new
  76,800-step Method-B v11 run from random initialization.
- V11 Method-B seed-11 full training completed exactly
  76,800/4,915,200 steps/transitions from random initialization in about
  2:48. Final checkpoint SHA-256 is
  `29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`;
  all 77 tensors/785,093 elements and all 15,534 scalar samples are finite.
- The repaired tracker produced 389 episode windows with lengths
  3,822--8,999 and observed both success and safety-terminal feedback.
  Policy standard deviation ended at 0.0741615. Independent deterministic
  evaluation is still required.
- V11 evaluator smoke restored the explicit final checkpoint and produced a
  uniform 100x122 finite table. In phases 0/1, policy max-abs was 0.09336
  while executed and scaled residuals were exactly zero. Its deliberate
  five-second timeout is excluded.
- The full v11 50 mm development gate passed execution but failed promotion
  at 6/20. It retained five frozen-FSM successes, rescued 0013, and ended
  with ten phase-8 front-right collisions, one phase-9 timeout, and three
  phase-10 timeouts.
- V11's mask and signs were exact, but collision rows learned about 0.52 mm
  rear-right lift versus 0.22 mm rear-left lift. The soft raw-action
  asymmetry cost did not enforce physical symmetry after signed-magnitude
  projection. V12 will hard-tie left/right front and rear z magnitudes before
  any further retraining.
- Runtime v12 (`runtime-v12-bilateral-z-tied`) is registered. Front
  left/right execute their shared negative mean absolute z magnitude; rear
  left/right execute their shared positive mean absolute z magnitude. The
  phase window, z-only mask, 12-D actor, rewards, PPO, randomization, seeds,
  and 76,800-step budget are unchanged.
- V12 common config SHA-256 is
  `f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`
  (canonical
  `22927197cf439041d3665edfc95f91823ef9f86c0267fd6057c2ee6d1e4ee5d3`).
  All 130 tests and Python compilation pass; frozen hashes are unchanged.
- V12 smoke attempt001 correctly produced the nonuniform probe action
  `[0,-0.3000000119,0,-0.3000000119,0,+0.7000000477,0,+0.7000000477,0,0,0,0]`
  and passed separate phase/mask/tie checks, but a decimal-literal float32
  oracle rejected the correct 0.6/0.8 mean. The failed artifact is retained.
  Attempt002 computes its exact oracle from the registered operands; physical
  projection code is unchanged.
- V12 smoke attempt002 passed. Its nonuniform raw probe produced exact tied
  front/rear pairs `-0.3000000119/-0.3000000119` and
  `+0.7000000477/+0.7000000477`; phase gate, mask, signs, tracker, terminal
  safety, finite interfaces, and reset checks also passed.
- The full v12/v11-checkpoint development counterfactual completed at 9/20,
  versus 6/20 for the same checkpoint under v11 physical semantics. It
  retained five old successes, gained four, and lost one.
- All 50,719 telemetry rows had exact phase gating, z-only masking,
  front-negative/rear-positive signs, and bilateral ties. The action chain
  was finite; undefined support margins were confined to `margin_m`.
- Remaining failures were eight `front_right_bot` collisions, two FSM phase
  timeouts, and one global timeout. The paired +3 improvement authorizes one
  new 76,800-step Method-B v12 run from random initialization.
- V12 Method-B seed-11 full training completed exactly
  76,800/4,915,200 timesteps/transitions from random initialization in about
  2:50. Final checkpoint SHA-256 is
  `a28a8a583622dc15734d427286cbfeb1315dc536a7afe22a32bb1571c478fc93`;
  all 77 tensors/785,093 elements and all 15,510 scalar samples are finite.
- The repaired tracker produced 385 episode windows with lengths
  3,822--8,999 and observed both success and safety-terminal feedback.
  Policy standard deviation ended at `0.07029545`. Independent deterministic
  evaluation is still required.
- The v12 evaluator smoke restored the exact final checkpoint and produced a
  uniform 100x122 table with a finite action chain. During phases 0/1 policy
  max-abs was `0.0726394`, while projected actions and scaled residuals were
  exactly zero. Its deliberate five-second timeout is excluded.
- The full v12 50 mm development gate passed execution but failed promotion
  at 7/20. Failures were seven `front_right_bot` collisions, three phase
  timeouts, and three global timeouts.
- V12's hard bilateral ties were exact, but training learned approximately
  0.123 mm front down versus 0.650 mm rear up in successful phase-8 rows.
  This new front/rear imbalance regressed from the 9/20 v12 projection
  counterfactual. V13 will hard-share one magnitude across all four z
  residuals before any further retraining.
- Runtime v13 (`runtime-v13-four-wheel-balanced-z`) is registered. All four
  raw z channels contribute to one shared mean absolute magnitude; the front
  pair executes its negative value and the rear pair its positive value.
  Phase window, z-only mask, bounds, 12-D actor, rewards, PPO,
  randomization, seeds, and budget are unchanged.
- V13 common config SHA-256 is
  `0c06cd2d2ea208461233074062285ec42cf14f92809036c2e164a27a6b2aec17`
  (canonical
  `9ff7a3ed7b787134b22acde1e8c4bf9197444f6f968d7adfcb0536b147e0ed47`).
  All 130 tests and Python compilation pass; frozen hashes are unchanged.
- V13 Method-B seed-11 real-Isaac smoke passed in 16 environments. The
  nonuniform raw z probe produced one exact shared magnitude:
  `[0,-0.5,0,-0.5,0,+0.5,0,+0.5,0,0,0,0]`. Phase gate, mask, signs,
  bilateral ties, four-wheel balance, tracker, terminal safety, finite
  interfaces, and reset checks passed.
- The v13 deterministic evaluator smoke restored the exact v12 final
  checkpoint and produced 100x122 finite action-chain telemetry. In phases
  0/1, policy max-abs was `0.0726394` while executed and scaled residuals
  were exactly zero. Its deliberate timeout is excluded.
- The full v13/v12-checkpoint counterfactual completed at 8/20, versus 7/20
  for the same checkpoint under v12. Collisions decreased from seven to six
  and global timeouts from three to one, but phase timeouts increased from
  three to five.
- The exact balanced projection produced about 0.389 mm shared magnitude in
  successful phase-8 rows. The paired +1 result is insufficient to authorize
  retraining. V14 will test the unchanged balanced projection through phase
  9, where the remaining failure mass moved.
- Runtime v14 (`runtime-v14-balanced-z-through-phase9`) is registered. It
  changes only the physical execution window from phases 7--8 to phases
  7--9; the four-wheel-balanced signed-magnitude projection, masks, bounds,
  rewards, actor/PPO, randomization, seeds, budget, and B/C-only CoM
  difference are unchanged.
- V14 common config SHA-256 is
  `2022543c57ae20da7b62ae1874efdfcf4d06cedabc15e78a9e12692b733eff52`
  (canonical
  `4f36a5962291173fc348c331841433c54635da298527d660dfc9dd843c084f92`).
  Safety/env/train/evaluator source SHA-256 values are
  `97ec077318ea7f47cbb15234a59ce2d1b0dbe7b8f560ecf1bb1125ef39cb494c`,
  `f9a89c28d0a2b33006bc475be1ec18abab72f8f70db4544a40f7f44cb8c60ec7`,
  `501be3ebae3e6679c58b93ca0c7e6808566bd7e7a1b43fc6977187116e8efdee`,
  and
  `b14d945b6894f0d1fdb6b276e95b18f3343336ed539560e97d96cccb3b9778a1`.
  All 130 tests, Python compilation, and state JSON parsing pass.
- V14 Method-B seed-11 real-Isaac smoke passed in 16 fully randomized
  environments. Boundary phases 6/7/9/10 produced scaled maxima
  `0/0.005/0.005/0`; the nonuniform probe retained exact z-only signs,
  bilateral ties, and four-wheel balance. Finite interfaces, tracker
  isolation, one-shot terminal safety, and randomized reset checks passed.
- The v14 deterministic evaluator smoke restored the exact v12 final
  checkpoint and emitted 100x122 fully finite telemetry rows. Policy action
  max-abs was `0.0726394`, while executed and scaled residuals were exactly
  zero in observed phases 0/1. Its deliberate timeout is excluded from
  performance evidence.
- The full v14/v12-checkpoint counterfactual completed at 9/20. It retained
  v13's six front-right-lower-link collisions and five phase timeouts, while
  converting only scenario `0019` from global timeout to success.
- All 52,254x122 telemetry rows preserve exact v14 constraints. Successful
  phase-9 rows averaged about 0.286 mm shared magnitude versus 0.223 mm for
  phase-timeout rows. The +1 result versus v13 is insufficient to authorize
  retraining; v15 will test a 1.5x gain only in phase 9 under the unchanged
  hard bounds and projection.
- Runtime v15 (`runtime-v15-phase9-balanced-z-gain`) is registered with
  aligned phase-7/8/9 gains `[1.0,1.0,1.5]`. The gain is applied after the
  unchanged balanced projection and before clamping to normalized `[-1,1]`
  and the existing physical bounds.
- V15 common config SHA-256 is
  `2cf5437c3541c21c82dc221fec77c09b3f9d4c9ad52fbaf43d9dc6dc0f74cb11`
  (canonical
  `f260aa605ec9dc229749a8c1e418333d6c1f9fbdd1f4f2a2e36b5f452db6c73c`).
  Safety/env/train/evaluator source SHA-256 values are
  `83f5b4dbd694696e20cb00fe0cc6c7dce530c8d2d4374a8e02e87cf1866cee9d`,
  `45d483345492ed27726cfe11837113ee7d2e45604e5a9a8a27ef9df9062124cc`,
  `88a0b36aaad1257e904dd5feb43369179a9fa53a31a60b61d843ea9a9ca1e3a6`,
  and
  `0e01746153c02a2cac819aac43f1317916acf80af18ed45d42c29207e9084c91`.
  All 132 tests and Python compilation pass.
- V15 Method-B seed-11 real-Isaac smoke passed. The nonuniform probe
  produced scaled maxima `0/0.005/0.0075/0` at phases 6/7/9/10,
  respectively, proving the 1.5x gain is phase-specific. Projection, hard
  bounds, zero action, finite interfaces, terminal safety, and reset checks
  passed.
- The v15 deterministic evaluator smoke restored the exact v12 final
  checkpoint with effective gains `[1.0,1.0,1.5]`. Its 100x122 phase-0/1
  telemetry is byte-identical to the v14 smoke; policy actions remain
  observable while executed and scaled actions are exactly zero.
- The full v15 counterfactual again reached 9/20 with exactly the same
  scenario outcomes as v14. The gain propagated to final wheel-center and
  servo targets and raised timeout-group phase-9 magnitude to about
  0.332 mm, but did not rescue a single timeout. V15 retraining is rejected.
- A training-only checkpoint screen is pre-registered before further
  action-space changes. Candidate order is 59200, 64000, 75200, then
  skrl `best_agent`/70400, based respectively on checkpoint-window mean
  episode returns, best individual return, and skrl's internal selection.
- V12 checkpoint 59200 restored successfully under v15. Its 100x122
  phase-0/1 evaluator smoke recorded policy max-abs `0.182093` and exact-zero
  executed/scaled residuals, with matching checkpoint/config/gain
  provenance.
- The full checkpoint-59200 screen reached 8/20: seven collisions, three
  phase timeouts, and two global timeouts. Its 51,841x122 telemetry preserves
  exact constraints, but it is worse than the final checkpoint and is
  rejected. Candidate 64000 is next by the pre-registered order.
- Checkpoint 64000 restored successfully under v15. Its 100-row smoke
  recorded policy max-abs `0.177924` and exact-zero phase-excluded execution.
- Checkpoint 64000 reached only 5/20 (nine collisions, four phase timeouts,
  two global timeouts) and is rejected. Candidate 75200 is next.
- Checkpoint 75200 restored successfully; its smoke recorded policy max-abs
  `0.0651841` and exact-zero execution outside the residual window.
- Checkpoint 75200 reached 10/20: five collisions, four phase timeouts, and
  one global timeout. Its 52,818x122 telemetry preserves exact v15
  constraints. It is the current development best, but remains below the
  16/20 eligibility threshold; `best_agent`/70400 is the last
  pre-registered candidate.
- The final pre-registered `best_agent` checkpoint restored successfully
  under v15. Its 100x122 smoke telemetry is fully finite, records maximum
  policy action `0.0550975`, and preserves exact-zero physical residual
  outside the execution window.
- `best_agent` completed at 8/20 with eleven `front_right_bot` collisions
  and one phase timeout. Its 48,472x122 telemetry preserves all constraints.
  The pre-registered screen is closed: checkpoint 75200 is best at 10/20
  but remains ineligible, so a new numbered development-only iteration is
  required before any validation or locked test.
- Runtime v16 (`runtime-v16-zero-preserving-balanced-z-gate`) replaces the
  mean-absolute projection with a signed projection onto the same safe
  front-negative/rear-positive direction followed by a one-sided zero gate.
  Zero and the opposite half-space now preserve the FSM exactly; enabled
  actions remain z-only, four-wheel balanced, and bounded. The rejected v15
  phase-9 gain is removed, giving phase-7/8/9 gains `[1,1,1]`.
- V16 common config raw/canonical SHA-256 values are
  `8dc33c824c1b3576012dc5437db764df04fb8e47ea48c6af9a6a325a0494b193`
  and
  `0cea2d98a2ab17b82cdca9dedd2051d799fbe059ed99a4e85172db14b538c71d`.
  Safety/env/train/evaluator source SHA-256 values are
  `1919e45f49c103fa4413a0238bab8c162fb95419132db47737344d7dab0e9fc2`,
  `d4c9f78052e09251200462af51d1bdd00ab1ca09b636bb69837a3998b11a2299`,
  `a2903efad7c927214452db6cab65d66199ae0ffeeb862db4b5d80e9698413248`,
  and
  `86897ca3b9628dcd2ce348b8611d35cd9963bcd9e271dfd47aed66e75bfb17dd`.
  All 133 tests, Python compilation, and state JSON parsing pass.
- V16 Method-B real-Isaac smoke passed in 16 fully randomized environments.
  Boundary phase maxima were `0/0.002/0.002/0 m` for phases 6/7/9/10.
  The nonuniform probe produced exact balanced z action
  `[-0.2,-0.2,+0.2,+0.2]`; reversing its aligned sign produced exact zero
  physical residual, directly auditing the new off half-space.
- The v16 evaluator smoke restored checkpoint 75200 with exact checkpoint,
  config, projection, and gain provenance. Its 100x122 telemetry is fully
  finite; policy maximum was `0.0651841` while physical execution in phases
  0/1 was exactly zero.
- The full v16/checkpoint75200 counterfactual completed at 10/20, equal to
  v15 but with a materially different paired path: it restored three
  v15-lost FSM-success branches, recorded exact off action in 40.00% of
  execution-window rows, and reduced maximum scaled action to 0.529 mm.
- Successful phase-8 branches were off in about 94--95% of rows, while
  collision branches were off in only about 79--87%. Because checkpoint
  75200 was never trained to use raw action sign as a gate, this
  state-dependent separation plus the exact off function space authorizes
  one from-scratch 76,800-step Method-B v16 run.
- Method-B v16 seed 11 completed its authorized from-scratch 50 mm run at the
  exact 76,800-local-timestep / 4,915,200-transition budget in 64 real Isaac
  environments. All 17,964 TensorBoard scalar samples and all 785,093 final
  checkpoint tensor elements are finite.
- The v16 final checkpoint SHA-256 is
  `c835b6fc5a9e72557de12232aa8f2f86c4850e7ee7c9820ca25c9d2a4123b75e`.
  Training integrity passes, but performance remains unclaimed pending an
  independent deterministic smoke and the unchanged 20-scenario 16/20 gate.
- The v16 final-checkpoint deterministic restore smoke passed with exact
  checkpoint/config/frozen-artifact provenance. Its 100x122 telemetry is
  fully finite; policy actions remain visible while phases 0/1 produce
  exactly zero executed and scaled residuals.
- The full v16 final-checkpoint gate reached only 8/20, a strict subset of
  the frozen FSM's 12 successes. It rescued no baseline failure and lost
  scenarios 0000/0004/0007/0015. All 50,598x122 telemetry rows preserve
  exact action constraints; the result is retained as a promotion failure.
- V16's deterministic gate was off in 71.68% of execution-window rows, while
  its learned shared-drive exploration standard deviation remained 0.03503.
  Estimated stochastic gate-on probabilities were about 38--41% in every
  outcome group, exposing a plausible exploration-gate versus deterministic
  evaluation mismatch.
- Before inspecting any intermediate v16 checkpoint, a training-only screen
  was frozen in order: agent60800, agent72000, best_agent/agent76800, then
  agent57600. The order is based on fixed 1,600-step TensorBoard return
  windows; each candidate must pass restore smoke and the unchanged 16/20
  development gate.
- The first candidate, agent60800, passed deterministic restore smoke with
  exact checkpoint/config provenance, fully finite 100x122 telemetry, and
  exact phase-excluded physical zero action.
- Agent60800 reached 10/20 with exact 52,692x122 action constraints. Its
  successes remain a strict subset of the FSM successes, so it is rejected
  and the frozen screen advances to agent72000.
- Agent72000 passed deterministic restore smoke with exact provenance,
  100x122 finite telemetry, and zero physical residual outside the phase
  window.
- Agent72000 reached 10/20 with exact 50,786x122 constraints. It rescued
  scenario 0013 but lost three FSM successes, so it is rejected and the
  screen advances to best_agent/agent76800.
- Best_agent restored successfully, but a direct tensor audit found its
  policy and observation preprocessor exactly equal to the already evaluated
  final_agent controller; its smoke telemetry is byte-identical. It is
  retained as an equivalent duplicate rather than rerun as a false
  independent result. The screen advances to agent57600.
- Agent57600, the last pre-registered distinct candidate, passed restore
  smoke with fully finite telemetry and exact phase-excluded zero action.
- Agent57600 completed the unchanged gate at 9/20 with eight body/link
  collisions and three timeouts. Its 50,896x122 telemetry preserves all
  exact v16 action constraints, but the physical gate is off in 74.86% of
  phase-7--9 execution-window rows.
- The pre-registered v16 screen is closed: distinct checkpoints scored
  10/20, 10/20, 8/20, and 9/20 (with best_agent exactly policy-equivalent
  to the 8/20 final agent). None reaches 16/20, so v16 is rejected without
  reading the locked-test manifest.
- Registered runtime v17
  (`runtime-v17-deterministic-gate-aligned-exploration`) before training.
  It leaves v16 physics, projection, rewards, randomization, architecture,
  optimizer, and budget unchanged, but changes the exploration envelope to
  initial/max `log_std=-4`, min `-5`, and entropy scale zero.
- Under the unchanged 10 mm bound, v17 limits the four-channel shared-drive
  exploration standard deviation to 0.09158 mm. A 200,000-sample CPU audit
  measured channel/shared standard deviations of 0.0183106/0.00915831
  against theoretical 0.0183156/0.00915782, with exact zero deterministic
  mean and fully finite bounded samples.
- All 133 unit tests pass after the v17 implementation. A real-Isaac
  one-environment training smoke remains required before full training.
- The v17 one-environment real-Isaac smoke passed with finite sampled
  action/value/reward, exact phase gating and balanced z projection, exact
  reversed-action off behavior, the exact -200 fall term, and clean reset.
  Its result SHA-256 is
  `52c5abe731fa9e0cf3a8f609b0cd66396d813cc84d8b37735dfa6ed824793462`.
- The pre-registered 76,800-local-timestep / 4,915,200-transition Method-B
  seed-11 50 mm v17 run is authorized.
- Method-B v17 seed 11 completed the exact 76,800-local-timestep /
  4,915,200-transition budget from scratch in 64 real Isaac environments.
  All 14,184 TensorBoard scalar samples and all 785,093 final-checkpoint
  tensor elements are finite.
- Effective policy standard deviation remained inside the registered
  envelope, decreasing from 0.0183138 to 0.0180137. Final checkpoint
  SHA-256 is
  `e29c94d54a12e895c8a8e3ba1c2aea726df3b5559d5ce693dbc09ac439f5a102`.
  Training completion makes no performance claim; deterministic restore
  smoke and the unchanged 20-scenario gate remain required.
- The v17 final checkpoint deterministic restore smoke passed with exact
  checkpoint/config/source provenance, fully finite 100x122 telemetry, and
  exact physical zero execution in phases 0/1. The deliberate timeout is
  excluded from performance.
- The full v17 final-checkpoint gate reached only 6/20 with seven
  body/link collisions, four phase timeouts, and three global timeouts.
  All 52,354x122 rows preserve exact constraints, but the deterministic
  gate is off in only 10.74% of phase-7--9 rows.
- V17 fixes v16's predominantly-off deterministic mean but over-corrects to
  nearly always-on execution. Learned median drive is strongly
  phase-separated (0.02667/0.01005/0.00785 in phases 7/8/9), which
  authorizes a v18 confidence deadband analytically fixed at two registered
  shared-noise standard deviations, `exp(-4)=0.0183156`, before any v18
  evaluation.
- Registered runtime v18
  (`runtime-v18-two-sigma-confidence-balanced-z-gate`) before any v18 Isaac
  run. It subtracts the analytically fixed threshold `exp(-4)` from positive
  shared drive before the unchanged balanced-z projection.
- V18 raw/canonical common-config hashes are
  `3c6b744266f48155348f9fe8df36ce254221ee9b873abee5b6b3980194e2fcc5`
  and
  `ba0b27c4fc565d9ba42167c214fec8002049d90deb03cb5099e16ccc788d475b`.
  Safety/env/train/evaluator source hashes are frozen in
  `runs/diagnostics/v18_confidence_gate_registration.md`.
- Python compilation and all 137 tests pass. The unchanged v17 checkpoint
  must first reach at least 12/20 under the v18 runtime counterfactual before
  one from-scratch v18 Method-B seed-11 run can be authorized.
- V18 training-entrypoint smoke attempt001 failed before environment
  construction: threshold validation referenced `math.exp` without importing
  `math`. The failed attempt and empty stderr are retained with hashes.
- Runtime-v18.1 adds only the missing import plus an AST regression test; all
  138 tests and compilation pass. The common config, mechanism, and decision
  gates remain byte-identical.
- V18.1 real-Isaac training-entrypoint smoke attempt002 passed. The
  registered `0.2` probe became exactly `0.18168437` normalized /
  `1.81684375 mm` after threshold subtraction, with exact phase exclusion,
  balanced z-only execution, reversed-drive shutoff, finite rewards, exact
  terminal penalty, and finite reset.
- The unchanged v17 final checkpoint restored under v18 with exact
  checkpoint/config/source provenance. Its five-second, 100x122 smoke is
  fully finite and byte-identical to the v17 smoke because phases 0/1 have
  exact-zero physical residual under both runtimes.
- The complete v18/v17-checkpoint counterfactual reached 10/20: seven
  collisions and three phase timeouts. It gained five v17 failures but lost
  one v17 success, a net +4, so it missed the pre-registered 12/20 and +6
  authorization gates and v18 retraining is rejected.
- All 51,793x122 telemetry rows preserve exact action constraints. The gate
  was off in 56.91% of phase-window rows, closely matching the registered
  aggregate prediction, but was on in 89.96% of phase-7 rows and off in
  99.18%/95.50% of phase-8/9 rows.
- Frozen-FSM telemetry shows a physically interpretable IMU separation:
  phase-8 successes never exceed 0.08677 rad positive pitch, whereas failure
  branches reach 0.15414 rad; phase-9 successes stay below 0.07910 rad and
  the timeout branch reaches about 0.169 rad. V19 will use a pre-registered
  0.09 rad positive-pitch hazard gate, not scenario identity or simulator-only
  contact truth.
- Registered runtime v19
  (`runtime-v19-positive-pitch-imu-hazard-gate`) before any v19 Isaac run.
  It preserves the FSM throughout phase 7 and whenever phase-8/9 real-IMU
  pitch is below +0.09 rad; only the positive-pitch hazard branch can use the
  zero-preserving balanced z projection.
- V19 raw/canonical common-config hashes are
  `f115a3a4e435c70721ffdc44468e0352e71ca66f8187610f6ecd3cda112a8f93`
  and
  `3ffba6ff7e809a4244ebcee93e38b359a080ab7f594c87c73bd6e22f39ea31bf`.
  All 144 tests and Python compilation pass.
- V19 real-Isaac training-entrypoint smoke passed. At measured pitch
  -0.02244 rad the runtime produced exact-zero residual; after an explicit
  +0.10000-rad pose probe it produced exact balanced z authority in phases
  8/9 and exact zero in phases 7/10. Finite interfaces, terminal safety, and
  reset checks also passed.
- The unchanged v17 final checkpoint restored under v19 with exact
  provenance. Its 100x122 five-second telemetry has policy max 0.08164 but
  exact-zero execution because observed pitch stayed below the hazard
  threshold; it is byte-identical to prior restore smokes.
- The complete v19/v17-checkpoint counterfactual reached 13/20, retained all
  12 frozen-FSM successes, and rescued 0009. It had four collisions and
  three phase timeouts.
- All 2,310 nonzero action rows are in phase 8/9 at pitch >=0.09 rad; every
  phase-7, below-threshold, masked, bilateral, and balance constraint is
  exact. Frozen-FSM success trajectories have identical physical telemetry.
- V19 passes all pre-registered counterfactual gates and authorizes exactly
  one from-scratch 76,800-local-timestep Method-B seed-11 50 mm run.
- Method-B v19 seed 11 completed the exact 76,800-local-timestep /
  4,915,200-transition budget from random initialization in 64 real Isaac
  environments. The environment and wrapper processes exited normally.
- All 39,254,650 floating values across 50 checkpoint files and all 14,232
  TensorBoard scalar samples are finite. Final checkpoint SHA-256 is
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.
- Training completion makes no performance claim. The explicit final
  checkpoint must pass a deterministic restore smoke and then the unchanged
  20-scenario development gate at the pre-registered threshold of 16/20.
- The v19 final checkpoint deterministic restore smoke passed with exact
  checkpoint/config/source provenance and fully finite 100x122 telemetry.
  Pitch stayed below the positive hazard threshold, so physical residual
  execution was exactly zero despite a nonzero policy output.
- The deliberate five-second smoke timeout is performance-excluded. The
  unchanged 20-scenario 50 mm development gate remains fixed at 16/20.
- The full v19 final-checkpoint development gate completed at 13/20 and
  therefore failed the fixed 16/20 promotion rule. It had four collisions
  and three FSM phase timeouts.
- All 2,386 nonzero rows were authorized by phase 8/9 and pitch >=0.09 rad;
  masking, bilateral ties, balance, and FSM-preservation constraints were
  exact. The trained policy used substantially stronger hazardous-branch
  residuals but produced exactly the counterfactual's success set.
- Physical audit identifies a direction mismatch: the
  front-negative/rear-positive wheel-center-z output creates a positive-pitch
  moment under fixed contact, aligned with the positive-pitch hazard. V20
  will reverse only the executed balanced-z direction while preserving the
  v19 state gate and learning protocol.
- Registered runtime v20
  (`runtime-v20-positive-pitch-corrective-balanced-z-gate`) before any v20
  Isaac run. Historical actor-drive alignment stays
  `[-1,-1,+1,+1]`, while positive drive now executes corrective
  `[+1,+1,-1,-1]` wheel-center-z signs.
- V20 leaves the phase-8/9 and +0.09-rad IMU gates, zero preservation,
  z-only mask, bounds, network, rewards, optimizer, randomization, budget,
  curriculum, and B/C distinction unchanged.
- V20 raw/canonical common-config hashes are
  `5494a5b575445d05fe2ea45ed9fd5fe351d08b94c4bd5fb3a74ad16c21a671be`
  and
  `51bae0d8d66105104a2126843d49f35405163ad0543bd785fea9fe7e34943111`.
  Python compilation and all 146 tests pass.
- V20 real-Isaac training-entrypoint smoke passed. At nominal
  -0.02244-rad pitch the residual was exactly zero; an explicit
  +0.10000-rad probe executed exact front-positive/rear-negative 2 mm
  correction in phases 8/9 and exact zero in phases 7/10.
- Finite policy/value/contact/reward interfaces, one-shot terminal safety,
  partial reset, post-terminal reset, mask, tie, balance, and zero-preserving
  checks all passed.
- The explicit v19 final checkpoint restored under v20 with exact
  checkpoint/config/source provenance. Its 100x122 finite telemetry is
  numerically identical to the v19 restore smoke because low pitch keeps
  physical residuals exactly zero.
- The complete v20/v19-checkpoint counterfactual reached 12/20. It retained
  all 12 frozen-FSM successes but lost v19's scenario-0009 rescue and added
  no new rescue, so it failed the pre-registered 16/20 authorization gate
  and v20 retraining is prohibited.
- All 2,386 nonzero rows were authorized phase-8/9, pitch-at-least-0.09
  corrective actions. Every action/physical field is finite; masking,
  bilateral ties, balance, corrective signs, and unauthorized execution are
  exact.
- Frozen-FSM failure timing motivates a pre-registered phase-aware v21:
  preserve the phase-8 climb direction, use corrective direction in
  post-transfer phases 9--10, and open phase-8 authority early only on the
  real-IMU precursor `pitch >= +0.04 rad` and
  `pitch_rate >= +0.35 rad/s`. No v21 Isaac result exists yet.
- Registered runtime v21
  (`runtime-v21-phase-aware-imu-emergency-recovery`) before any v21 Isaac
  run. Phase 8 uses corrective direction only on the rapid-rise precursor
  and otherwise retains the v19 climb direction above +0.09 rad; phases
  9--10 use the corrective direction above +0.09 rad.
- A fixed 3x emergency gain maps the inherited checkpoint's observed
  0.331305 mm maximum to about 0.994 mm while retaining the 10 mm hard
  bound. Architecture, observations, rewards, optimizer, randomization,
  curriculum, budget, and B/C distinction are unchanged.
- V21 raw/canonical common-config hashes are
  `96d11bc49cc06a0af4248673b59d25117464aa3638c8964b32c844ab25abdb1b`
  and
  `1db52003b9a2b78ed670702334611a1f3cb132bddbcfb630764977586678b9ba`.
  Python compilation and all 149 tests pass.
- V21 real-Isaac training-entrypoint smoke passed. Nominal pitch produced
  exact zero; a slow +0.10-rad probe produced the climb direction in phase
  8 and corrective direction in phases 9/10; a
  +0.05-rad/+0.40-rad/s rapid-rise probe produced correction in phase 8
  and exact zero in phase 9.
- The 3x gain, phase-7/11 exclusion, z-only mask, bilateral ties,
  four-wheel balance, opposite-drive shutoff, finite interfaces, terminal
  safety, and reset checks all passed.
- The explicit v19 final checkpoint restored under v21 with exact
  provenance. Its fully finite 100x122 smoke telemetry is byte-identical to
  the v19 restore because measured pitch remains below every physical gate;
  policy output is nonzero while execution is exact zero.
- The complete v21/v19-checkpoint counterfactual reached 13/20, exactly the
  v19 success set. It retained all frozen-FSM successes and scenario 0009
  but added no rescue; scenario 0017 changed from timeout to collision.
- All 1,744 nonzero rows use a registered phase/sign vector, all physical
  values are finite, and masks, ties, balance, scaling, and bounds pass.
  Phase-8 rapid correction is not persistent: failed 0008 switches from 3
  corrective rows to 22 climb rows, while failed 0019 switches from 4
  corrective rows to 160 climb rows before phase 9.
- V21 training is prohibited. The evidence isolates v22 to a hysteretic
  phase-8 corrective latch that persists after the rapid-rise trigger.
- Registered runtime v22
  (`runtime-v22-latched-imu-emergency-override`) before any v22 Isaac run.
  A rapid-rise trigger now latches corrective mode through phase-8 exit,
  and corrective positive-drive branches receive a 0.1 pre-gain floor,
  yielding 3 mm after the unchanged gain3.
- The non-latched slow/high-pitch phase-8 branch remains actor-scaled climb
  to preserve 0009; zero/opposite drive remains off. Hard bounds,
  architecture, observations, rewards, optimizer, randomization,
  curriculum, budget, and B/C distinction are unchanged.
- V22 raw/canonical config hashes are
  `39927e1e21f8bdfc364cc2d81bef9e617911fa4acaa31e241de0f02159b43b74`
  and
  `180d8d52c8f12f1d74316708e865a4bd699984ae093b568842697b8fe670e05a`.
  Python compilation and all 152 tests pass.
- V22 real-Isaac training-entrypoint smoke passed. Rapid-rise correction
  remained latched after pitch rate was set back to zero; a 0.05 positive
  shared drive executed the exact 0.1 pre-gain floor / 0.3 normalized /
  3 mm physical correction.
- Phase exit below the post-transfer pitch threshold cleared the latch to
  exact zero. Phase directions/exclusion, zero/opposite-drive shutoff,
  masks, ties, balance, bounds, finite interfaces, terminal safety, and
  reset checks passed.
- The explicit v19 final checkpoint restored under v22 with exact
  provenance. Its fully finite 100x122 nominal telemetry is byte-identical
  to prior restore smokes and has exact-zero execution, proving no stale
  latch or floor activation.
- The complete v22/v19-checkpoint counterfactual reached 13/20, exactly the
  v19/v21 success set. It retained all frozen-FSM successes and scenario
  0009 but added no rescue; 0008 changed from collision to timeout and 0019
  changed from timeout to collision.
- All 1,721 nonzero rows use a registered phase/sign vector, including
  1,555 rows at the exact 0.1 pre-gain / 3 mm corrective floor. Masks,
  bilateral ties, four-wheel balance, scaling, bounds, and unauthorized
  execution pass.
- V22 training is prohibited. Every collision branch terminates on
  `front_right_bot` with positive roll and lost right-front upward support.
  Frozen-FSM successes stay below +0.09077 rad roll in phases 8--10, whereas
  failures reach +0.14237 rad.
- The bilateral pitch patterns used by v19--v22 cannot generate a roll
  moment. The next candidate must be pre-registered from frozen development
  evidence as a positive-roll, left-positive/right-negative
  `[+1,-1,+1,-1]` emergency correction with zero frozen-success activation.
- Frozen pre-code v23 gate analysis confirms `roll >= +0.10 rad` in phases
  8--10 activates every frozen-FSM/current-baseline failure and no
  v19/v22 success, including scenario 0009. The closest v22 success reaches
  +0.0960836 rad.
- The registered early phase-8 conjunction `roll >= +0.06 rad` and
  `pitch_rate >= +0.35 rad/s` activates failed 0005/0006/0008/0019 only,
  gives 0.15--0.25 s more recorded lead, and activates no success.
- Registered runtime v23
  (`runtime-v23-positive-roll-emergency-override`) before any v23 Isaac run.
  A roll emergency executes pure-roll z signs `[+1,-1,+1,-1]`; the
  phase-8 slow/high-pitch-only branch retains the historical climb that
  rescued 0009.
- V23 keeps the positive actor-drive half-space, phase-8 latch, 0.1
  pre-gain corrective floor, gain3, 10 mm hard bound, architecture,
  observations, rewards, optimizer, randomization, curriculum, budget, and
  B/C distinction unchanged. Compilation and all 155 tests pass.
- V23 real-Isaac training-entrypoint smoke passed. Nominal state was exact
  zero; slow +0.10-rad pitch kept phase-8 climb and phase-9 zero; +0.11-rad
  roll executed `[+0.6,-0.6,+0.6,-0.6]` in phases 8--10.
- The +0.07-rad roll / +0.399-rad/s early probe triggered phase-8 pure-roll
  correction, remained latched after rate decay, and applied the exact
  0.1 pre-gain / 0.3 normalized / 3 mm floor. Phase exit/reset, exclusions,
  mask, pure-roll pairing, zero sum, zero pitch moment, bounds, finite
  interfaces, terminal safety, and reset checks passed.
- The explicit v19 final checkpoint restored under v23 with exact
  provenance. Its fully finite 100x122 telemetry has exact-zero physical
  execution and is byte-identical to the v22 restore, because nominal roll
  remains below both registered gates.
- The complete v23/v19-checkpoint counterfactual reached 13/20, exactly the
  v19/v22 success set. It retained all frozen-FSM successes and scenario
  0009 but added no rescue; 0013 changed from timeout to collision while
  0019 changed from collision to timeout.
- All 876 nonzero rows satisfy a registered row-local gate. The 863
  pure-roll rows are exact 3 mm floor actions; masks, registered signs,
  pure-roll pairing, zero sum, zero pitch moment, climb balance, scaling,
  bounds, and finite checks pass.
- V23 training is prohibited. All seven failures finish with
  `[FL=True, FR=False, RL=False, RR=True]`; all six collisions are
  `front_right_bot`. Pure roll also moves the already-supported FL/RR
  diagonal.
- The next candidate is isolated to diagonal wheel-center-z output
  `[0,-1,+1,0]`, directly targeting front-right/rear-left while leaving
  front-left/rear-right unchanged under the same success-inactive IMU gates.
- Registered runtime v24
  (`runtime-v24-front-right-rear-left-diagonal-emergency`) before any v24
  Isaac run. Only the emergency output changes to `[0,-1,+1,0]`; v23's
  gates, latch, actor half-space, floor, gain, bounds, architecture,
  observations, rewards, optimizer, randomization, curriculum, budget, and
  B/C distinction remain unchanged.
- The diagonal output extends front-right, retracts rear-left, keeps
  front-left/rear-right exact zero, and has zero four-wheel sum. Compilation
  and all 156 tests pass.
- V24 real-Isaac training-entrypoint smoke passed. High roll executed exact
  `[0,-0.6,+0.6,0]` in phases 8--10; early gating/latch passed and a small
  positive drive executed the exact `[0,-0.3,+0.3,0]` / 3 mm floor.
- Nominal zero, slow-pitch climb/phase-9 zero, phase exclusion, FL/RR zero,
  FR/RL equal-and-opposite, four-wheel balance, masks, scaling, bounds,
  finite interfaces, terminal safety, and resets passed.
- The explicit v19 final checkpoint restored under v24 with exact
  provenance. Its `100 x 122` telemetry is fully finite, has exact-zero
  executed and physical residuals, and is byte-identical to the v23/v22
  restores because nominal IMU state never enters either registered gate.
- The deliberate 5 s restore-smoke timeout is diagnostic only and is not a
  traversal result. Environment Python PID 92144 exited naturally.
- The complete v24/v19-checkpoint counterfactual reached 13/20, exactly the
  v19/v23 success set. It retained all frozen-FSM successes and scenario
  0009 but added no rescue; its episode artifact is byte-identical to v23.
- All 876 action-layer nonzero rows are authorized and structurally exact:
  13 phase-8 climb rows plus 863 exact `[0,-0.3,+0.3,0]` / 3 mm diagonal
  floor rows. Numerical, mask, sign, phase, balance, scale, and bound checks
  pass.
- V24 physical realization fails. All 863 diagonal requests make only the
  rear-left IK leg invalid; the primary knee solution exceeds its safe lower
  limit by at most 0.00195988 rad. The coupled all-leg fail-closed branch
  therefore restores all four FSM baseline targets on every corrective row.
- V23/v24 final wheel-center targets, final servo targets, and all 56 shared
  physical/state/contact/reference/time fields are exact across all 51,092
  rows. Only six requested-action columns differ. V24 training is
  prohibited.
- Frozen pre-code v25 analysis shows that removing the infeasible rear-left
  request and retaining front-right-only `[0,-1,0,0]` makes all four legs IK
  valid on 863/863 reconstructed corrective rows. A v25 smoke must prove
  final-target realization, not merely a nonzero action tensor.
- Registered runtime v25
  (`runtime-v25-front-right-only-ik-feasible-emergency`) before any v25
  Isaac run. Only the corrective signs change to `[0,-1,0,0]`; every v24
  gate, latch, actor drive, floor, gain, bound, model, reward, optimizer,
  randomization, curriculum, and budget remains unchanged.
- V25 adds a mandatory real-Isaac physical-realization smoke: unchanged
  residual IK-invalid count, exact -3 mm front-right request, final
  front-right wheel-center movement toward the request, nonzero front-right
  servo change, and exact-zero other-leg requests. Compilation and all 157
  tests pass.
- V25 realization smoke attempt001 failed and authorized no downstream run.
  The action request was exact `[0,-0.3,0,0]`, but the IK-invalid count rose
  by one and final wheel-center/servo deltas stayed zero.
- Audit found that the new probe manually changed only the phase integer
  while retaining the initial standing reference, rather than sampling the
  real held phase-8 reference used by frozen development rows. It also left
  the small floor probe active before the independent 0.6 direction check.
  The next change is isolated to this smoke harness; runtime/config remain
  frozen.
- Registered the v25.1 smoke-only harness correction before repeat Isaac
  execution. It samples the live held phase-8 reference, establishes a
  same-reference zero baseline, records per-leg IK and final-target/servo
  realization, and resets the independent high-drive probe. Runtime config
  hashes are unchanged; corrected training source SHA-256 is
  `18f4bc0cfcd4d2d8712ffdd7afb7711511c4c3c68f462e066e31b42dde81ea51`.
- V25 realization smoke attempt002 passed at the live phase-8 reference
  progress 0.87999898. All four IK legs were valid, invalid count delta was
  zero, requested and final front-right z deltas were both -2.9999986 mm,
  and the front-right servo target changed by 0.01647520 rad.
- The independent action checks produced `[0,-0.6,0,0]` in phases 8--10,
  exact zero in phases 7/11, and `[0,-0.3,0,0]` at the floor. All remaining
  gate, latch, climb, mask, bound, finite, terminal, and reset checks passed.
- V25 v19-checkpoint restore attempt001 had exact provenance and exact-zero
  execution but used noncanonical `record_stride=1`, yielding 299 rows.
  Its 100 samples at canonical 0.05 s timestamps are all 122 columns
  bit-exact to v24, but the invocation mismatch is retained and requires a
  new-directory stride-3 repeat.
- Canonical v25 restore attempt002 passed: `100 x 122` fully finite
  telemetry, exact-zero execution/scaling, exact checkpoint/config/source
  provenance, and telemetry SHA-256
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`,
  byte-identical to v24/v23/v22.
- The complete v25/v19-checkpoint counterfactual reached 13/20, retaining
  the exact prior success set. It changed 0008/0013 from collision to timeout
  and 0019 from timeout to collision but added no rescue. V25 training is
  prohibited.
- All 1,602 front-right corrective rows are exact 3 mm requests and all
  1,602 are physically realized; rollback rows are zero and
  final-to-request error is at most 4.47e-8 m. Action, authorization,
  scaling, numerical, and success-preservation audits pass.
- Every failure still lacks front-right and rear-left full support. With
  front-right fixed at -3 mm, frozen IK reconstruction gives a minimum
  rear-left positive-z limit of 2.700939 mm across 1,602 v25 rows. A
  +2.4 mm rear-left candidate is valid on all v25 rows and all 863 v24
  source rows, retaining at least 0.300939 mm measured margin.
- Frozen pre-code v26 evidence selects asymmetric corrective scale
  `[0,-1,+0.8,0]`, or `[0,-3.0 mm,+2.4 mm,0]` at the floor.
- Registered runtime v26
  (`runtime-v26-asymmetric-diagonal-ik-margin-emergency`) before any v26
  Isaac execution. Corrective signs/scales are fixed at
  `[0,-1,+1,0] / [0,1,0.8,0]`; all v25 gates, latch, actor drive, floor,
  gain, bounds, model, reward, optimizer, randomization, curriculum, and
  budget remain unchanged.
- The training-entrypoint smoke now requires all-leg IK validity, exact
  front-right -3.0 mm and rear-left +2.4 mm requests, final-target movement
  toward both requests, nonzero servo changes on both legs, and strict zero
  on inactive coordinates. Compilation and all 159 tests pass.
- V26 training remains prohibited until the real-Isaac realization smoke,
  exact v19 checkpoint restore, and fixed 20-scenario >=16/20 development
  counterfactual gates all pass.
- V26 real-Isaac realization smoke attempt001 passed at live phase-8
  progress 0.87999898. All four IK legs were valid and rollback count
  stayed zero; requested/final z deltas were about -3.0000/-3.0000 mm on
  front-right and +2.4000/+2.39999 mm on rear-left.
- Front-right/rear-left servo targets changed by 0.01647520/0.01590106 rad.
  High-drive and floor outputs were exact `[0,-0.6,+0.48,0]` and
  `[0,-0.3,+0.24,0]`; every other runtime, safety, finite, terminal, and
  reset audit passed.
- The explicit v19 final checkpoint restored under v26 with exact
  provenance. Canonical `100 x 122` telemetry is fully finite, physical
  execution is exact zero, and telemetry SHA-256
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`
  is byte-identical to the v25/v24/v23/v22 restores.
- The complete v26/v19-checkpoint counterfactual reached 13/20, the exact
  prior success set. V26 training is prohibited.
- All 133 asymmetric emergency rows and 13 climb rows are authorized,
  bounded, and physically realized with zero rollback above `1e-7 m`.
  Successful `34,800 x 122` histories are exact v25/v24. This is not an
  implementation or IK failure.
- Rear-left `+2.4 mm` raises/retracts an already missing support channel.
  Scenarios 0008/0013 revert from v25 timeouts to collision, and all seven
  failures collide on `front_right_bot` with terminal full-support pattern
  `[true,false,false,true]`.
- Frozen pre-code v27 analysis selects downward extension of both deficient
  legs: signs/scales `[0,-1,-1,0] / [0,1,1,0]`, yielding
  `[0,-3 mm,-3 mm,0]` at the floor.
- Offline calibrated-IK reconstruction validates the v27 candidate on all
  1,602 v25 source rows and all 146 v26 source rows, and remains valid
  through the full -10 mm rear-left registered bound. Rear-left joint
  margin at -3 mm is at least 0.0359745 rad.
- Registered runtime v27
  (`runtime-v27-deficient-diagonal-downward-support-emergency`) before any
  v27 Isaac execution. Only corrective signs/scales change to
  `[0,-1,-1,0] / [0,1,1,0]`; every gate, latch, shared-drive computation,
  floor, gain, bound, model, reward, optimizer, randomization, curriculum,
  and budget remains unchanged. Compilation and all 160 tests pass.
- V27 real-Isaac realization smoke passed: both front-right and rear-left
  requested/final z deltas were -2.9999986 mm, all four IK legs were valid,
  rollback count stayed zero, and the two servo targets changed by
  0.01647520/0.01961753 rad. High-drive/floor outputs were exact
  `[0,-0.6,-0.6,0]` / `[0,-0.3,-0.3,0]`.
- The exact v19 checkpoint restored under v27. Canonical `100 x 122`
  exact-zero telemetry SHA-256 is again
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`,
  byte-identical to all v22--v26 canonical restores.
- The complete v27 counterfactual remains 13/20 and training is prohibited,
  but collisions fall from seven to three. Scenarios 0005/0008/0013/0017
  reach phase-9 timeout, proving the downward direction while showing that
  3 mm authority is insufficient for strict support completion.
- V27 has 3,269 exact emergency rows; 3,267 physically realize the request.
  Two late scenario-0003 rows at 130.50/130.55 s are simultaneously
  front-right/rear-left IK-invalid after divergence and fail closed.
- Frozen pre-code v28 analysis retains `[0,-1,-1,0]` but doubles the
  corrective floor to 0.2, yielding 6 mm downward extension. It remains
  4 mm inside the hard bound and is valid on all previously valid v25,
  v26, and v27 source rows; no new invalid row appears.
- Registered runtime v28 before any v28 Isaac execution. Only the
  corrective floor changes; compilation and all 160 tests pass. Training
  remains prohibited pending 6 mm realization, restore, and >=16/20 gates.
- V28 6 mm real-Isaac smoke passed: both requested/final target changes are
  approximately -6.0 mm, all four IK legs are valid, rollback stays zero,
  and FR/RL servo changes are 0.03307688/0.03896400 rad.
- V28 exact v19 restore passed; canonical exact-zero telemetry remains
  byte-identical with SHA-256 `6418d01f...01a9`.
- The complete v28 counterfactual remains 13/20 with the exact prior
  success set, and all seven failures are now collisions. In particular,
  the four v27 phase-9 timeouts collide under 6 mm authority, three before
  reaching phase 9. V28 training is prohibited.
- V28 contains 527 exact 6 mm emergency rows, of which 525 physically
  realize the request. The only two rollback rows are the same late
  scenario-0003 coupled-invalid rows seen in v27; successful
  `34,800 x 122` telemetry is exact v27.
- Frozen pre-code v29 analysis restores 3 mm authority in phases 8 and 10
  and raises only phase 9 to 4 mm using gains `[3,4,3]` with the original
  0.1 floor. This preserves the useful v27 phase-8 trajectory by
  construction while testing the smallest bounded phase-9 increase.
- Offline calibrated-IK reconstruction validates all 2,524 changed v27
  phase-9 rows. Minimum FR/RL safe-joint margins are
  0.141975/0.068788 rad, and the 4 mm request retains 6 mm to the hard
  z bound.
- Registered runtime v29 before any v29 Isaac execution. The only
  effective change from the evidence-backed v27 behavior is phase-9 gain
  3 to 4; phase 8/10 remain gain 3 with floor 0.1. Compilation and all
  160 tests pass.
- The real-Isaac preflight now audits the expected projected action
  independently for each enabled phase, so unequal phase gains cannot be
  accepted through an equal-gain assumption.
- V29 realization smoke attempt001 passed its implemented runtime checks:
  high-drive projection was 6/8/6 mm, phase-8 floor realization was
  exactly 3 mm on both target legs, all-leg IK was valid, and rollback was
  zero. It is retained as coverage-incomplete because the minimum floor
  was not directly realized in phases 9 and 10.
- Before attempt002, the preflight-only audit was amended to apply a
  sub-floor probe in every enabled phase and require exact 3/4/3 mm
  applied/requested/final deltas, all-leg IK validity, and zero rollback.
  Runtime behavior and configuration are unchanged; compilation and all
  160 tests pass.
- V29 realization smoke attempt002 passed the amended audit. Applied
  actions are exactly -0.3/-0.4/-0.3 by phase, requested physical
  FR/RL deltas are -3/-4/-3 mm, final-target error is below 2.24e-8 m,
  all four legs are IK-valid in every phase, and all rollback increments
  are zero.
- The exact v19 final checkpoint restored under v29. Canonical
  `100 x 122` telemetry is finite and has exact-zero physical residuals;
  SHA-256 `6418d01f...01a9` is byte-identical to all v22--v28 canonical
  restores.
- The complete v29 counterfactual remains 13/20 with three collisions and
  four phase-9 timeouts. V29 training is prohibited.
- V29 and v27 telemetry have the same `53,498 x 122` shape; successes and
  target prefixes through phase 8 are exact. Only 2,524 phase-9 rows
  change from 3 to 4 mm, all physically realize with zero new rollback,
  and all four outcomes remain timeout.
- Formal-geometry diagnosis identifies excessive negative yaw as the
  direct missing channel: timeout phase-9 starting axle-midpoint yaw is
  -0.229 to -0.278 rad versus -0.065 to -0.119 rad for successes.
  Terminal FR is on the top surface but laterally outside full support,
  while RL remains airborne.
- Frozen pre-code v30 analysis selects phase-9-only skid-steer
  counter-yaw speeds `[-0.04,+0.04,-0.04,+0.04] rad/s` in the
  physical-forward convention, authorized only by the unchanged real-IMU
  corrective gate. V29 3/4/3 mm wheel-center behavior is retained.
- Registered runtime v30 before any v30 Isaac execution. The composite
  projection derives z support and counter-yaw speed from the same
  checkpoint-compatible shared magnitude, but exposes wheel speed only on
  corrective phase-9 rows.
- The smoke preflight records and requires normalized action, physical
  wheel-speed residual, physical-forward command delta, and mapped raw
  joint target delta independently. Compilation and all 162 tests pass.
- V30 real-Isaac composite smoke passed. Wheel-center floor realization
  remains exact 3/4/3 mm; physical-forward speeds are exact zero in
  phases 8/10 and `[-.04,+.04,-.04,+.04] rad/s` in phase 9.
- Mapped raw joint target deltas are all `+0.03999999 rad/s`, proving the
  imported left/right wheel signs produce the intended physical
  differential. All-leg IK is true and rollback is zero in every phase.
- The exact v19 checkpoint restored under v30 with registered projection,
  signs, and phase provenance. Canonical `100 x 122` telemetry remains
  exact-zero and byte-identical with SHA-256 `6418d01f...01a9`.
- The complete v30 counterfactual finished naturally at 13/20, with the
  exact unchanged failure set: collisions 0003/0006/0019 and phase-9
  timeouts 0005/0008/0013/0017. V30 training is prohibited.
- Exactly 2,524 v30 rows execute phase-9 wheel-speed residual and no row
  outside phase 9 does. All 45,944 pre-phase-9 state rows and all 13
  existing-success trajectories are exact v29.
- The v30 sign is empirically correct but its magnitude is insufficient.
  Target terminal yaw improves toward zero by 0.001719--0.009877 rad and
  front-right lateral position improves by 1.127--1.865 mm, but all four
  contact topologies remain `[TOP,TOP,AIR,TOP]` and time out.
- Frozen pre-code v31 analysis selects an independent 0.25 wheel-speed
  shared-magnitude floor only on corrective phase-9 rows. With gain 4,
  normalized output reaches the existing hard clip and physical-forward
  speed reaches exactly `[-.10,+.10,-.10,+.10] rad/s`; the 0.1 z floor
  and 3/4/3 mm wheel-center behavior remain unchanged.
- Registered runtime v31 before code and Isaac execution. Architecture,
  checkpoint, gate, direction, rewards, optimizer, randomization,
  curriculum, budget, development manifest, and B/C distinction remain
  fixed. Compilation and all 164 tests pass.
- V31 real-Isaac composite smoke passed. Phase-8/10 speed is exact zero;
  phase-9 physical residual is `[-.100000001,+.100000001,-.100000001,
  +.100000001] rad/s`, physical command delta is approximately
  `[-.099999994,+.099999994,-.099999994,+.099999994]`, and mapped raw
  actuator deltas are all `+.099999994 rad/s`.
- V31 smoke preserves exact 3/4/3 mm z realization. All legs are IK-valid
  and rollback increments are zero in every enabled phase; all phase,
  mask, hard-bound, mapping, finite, terminal, reset, and provenance
  checks pass.
- The exact v19 checkpoint restored under v31. Canonical `100 x 122`
  telemetry is finite, every physical residual is exact zero, and SHA-256
  `6418d01f...01a9` remains byte-identical to all v22--v30 restores.
