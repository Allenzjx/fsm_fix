# Attempt 016 diagnosis

This run is retained as a failed FSM-development attempt.

The 3.5 mm front-right extension cap prevented the early over-extension from
attempt 015, but did not create a static support point. At 135 s the trim was
at its cap, yet the front-right force was still 0 N. The run terminated at
145.5333 s with `front_right_bot` contact of 24.1183 N.

Together, attempts 015 and 016 reject direct extension of the unloaded
front-right leg as the recovery mechanism. The next attempt instead unloads
whichever legs currently carry more than 8 N by shortening their FK radius,
releasing below 4 N. It applies independently to all four legs at 1.5 mm/s
with a 5 mm maximum and uses the same validated IK and recorded-safe joint
envelope. No evaluation threshold is changed.
