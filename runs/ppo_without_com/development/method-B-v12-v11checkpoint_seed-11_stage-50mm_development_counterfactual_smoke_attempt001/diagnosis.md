# Method-B v12 / v11-checkpoint evaluator smoke attempt001

`SMOKE_PASS`. The deterministic evaluator restored checkpoint
`29ac9c122b6741500d12f086f39daf768d9a88310715d1f62bdfa60acfbab418`
under v12 bilateral semantics and completed the deliberate five-second
timeout.

- Environment Python PID: `167504` (exited normally).
- Result SHA-256:
  `9ebb2bacd2ebd03877aa119603f49e0693d4b1125a455d2bd468e9ca3e6fa588`.
- Episode/status/telemetry SHA-256:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
  `cc18790bbcca038b423a5573266867e330bcda80d00162a18de147bd390ad07c`,
  and
  `4b49f2807649686d7fe976bd7cfc3613ff4b03c432e890e2492fe94826470212`.
- Telemetry was 100 x 122 and finite. Policy max-abs was `0.0933611`, while
  phase-0/1 executed actions were exactly zero.
- Provenance records v12 common config SHA-256
  `f171dba0270c31fb1571c9e4ff86c9524a2eb32cd4927c33f8bc6b04b9f5251a`
  and projection type `wheel_center_z_bilateral_signed_magnitude`.

Next: run the full 20-scenario development-only counterfactual.
