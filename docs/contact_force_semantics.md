# Contact-force semantics audit

The FSM success and longitudinal support predicates use the **world-Z upward
component** of each wheel's net contact force. The unchanged formal threshold
is 2 N per wheel.

Through `development_100mm_attempt019`, the evaluator field and CSV columns
named `contact_force_n` recorded the **vector magnitude**, not world-Z. The
diagnostic grid field `terminal_wheel_contact_force_n` used the same magnitude.
Those historical artifacts remain immutable and must not be cited as proof
that the upward 2 N predicate was satisfied.

Starting with `development_100mm_attempt020`, the evaluator preserves the
legacy magnitude columns and adds explicit:

- `contact_force_magnitude_n`
- `contact_upward_force_n`
- `*_contact_upward_force_n` CSV columns
- terminal magnitude and terminal upward-force arrays in `episodes.jsonl`

The recovery-grid recorder likewise adds
`terminal_wheel_contact_upward_force_n`. No physical threshold or controller
parameter is changed by this instrumentation.
