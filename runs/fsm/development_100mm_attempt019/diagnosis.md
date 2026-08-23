# FSM 100 mm development attempt 019 diagnosis

- Scenario: `development-h100-0000`.
- Result: **FAIL**, `BODY_OR_LINK_COLLISION`.
- Physical episode and telemetry SHA256 are bit-identical to attempt 018:
  `96430299049184511ee8341c070994a49a59625d4d83c4c85c19fb0a391fbf44`
  and
  `c86c263dcbad047348275cb77dcbf330089e51482bdb4150344d3290684266ea`.
- Result SHA256:
  `41abfaeba09d93a432a998a16aa010543394bdca18996cb838d32e4fbeb37e81`.

The supported-capture rule used the same world-Z >=2 N predicate as formal
success, but it produced no recorded wheel-command or physical-trajectory
change. Audit then found that the apparent 138.05 s four-wheel support point
had been inferred from legacy `contact_force_n` telemetry, which stores force
vector magnitudes. Success uses the upward component, so that inference was
invalid.

Attempt 020 makes no controller, physics, scenario, metric, or threshold
change. It adds explicit per-wheel world-Z upward-force telemetry and terminal
evidence while preserving the legacy magnitude fields. The identical scenario
must be rerun before another physical hypothesis is selected.
