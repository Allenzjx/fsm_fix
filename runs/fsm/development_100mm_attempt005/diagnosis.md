# Attempt 005 diagnosis

This run is retained as a failed FSM-development attempt.

The phase-7 splice discontinuity from attempt 004 was removed. The complete
50 mm rear-leg channels were continuous from episode time zero and all source
timing used the slower 131.374 s duration.

The remaining failure was caused by a height-inappropriate fixed phase-5
boundary:

- Phase 5 stalled at normalized reference time `u=0.50` from 49.95 s through
  81.10 s because both front top contacts had not yet been observed.
- The 100 mm reference does not place its lifted front leg until
  `u=0.535--0.560`.
- At `u=0.50`, the source wheel command is still 0.3 rad/s. During the
  31.15 s gate wait the base advanced from 0.334348 m to 0.782606 m.
- When phase 6 finally began, both rear wheels were already at the riser
  (approximately x=0.470 m for a 0.521312 m obstacle front). The first rear-leg
  preparation motion then produced a non-wheel collision at 84.433 s.

The next attempt uses a 100 mm phase-5 boundary of `u=0.574`, after the
recorded front-leg placement and before the next recorded forward-roll event.
The 50 and 100 mm boundary values are interpolated at 75 mm. Wheel commands
are also held at zero during any non-recovery gate wait, preventing a latched
source command from causing unbounded travel. Contact, safety, and success
thresholds are unchanged.
