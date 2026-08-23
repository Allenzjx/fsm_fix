# Pre-locked complete metric reporting expansion

This reporting-only expansion was completed before validation, method freeze,
and locked-test access. Metric collection and definitions are unchanged.

The raw per-scenario table already carried every registered secondary metric,
and machine-readable method summaries carried distribution statistics for the
three primary metrics. The final method/height CSVs did not expose all of
those distribution fields directly.

The report generator now publishes:

- count, raw mean, equal-height mean, median, population standard deviation,
  q25, q75, and 10,000-draw equal-height bootstrap bounds for primary
  continuous metrics;
- the same primary distribution columns for successful-only sensitivity;
- per-height mean/median/std/q25/q75/bootstrap columns;
- equal-height summaries for negative-margin duration, maximum pitch, pitch
  RMS, peak pitch rate, traversal time, wheel-slip distance/ratio, residual
  saturation, wheel-speed saturation, and executed-command variation;
- body/link collision and joint-limit rates;
- an explicit statement that no energy/effort number is reported because the
  telemetry is not a calibrated energy measurement.
- a machine-readable conservative resume interpretation: joint improvement,
  similar-success stability improvement, explicit success/stability tradeoff,
  or unsupported combined improvement. Point-estimate increases are not
  described as supported when the paired confidence interval includes zero.

All raw secondary fields remain in `scenario_results.csv`.

- Final `report_generator.py` SHA256 at this registration:
  `4a68ddbbac8d81690f567627467da678d07fdce02aec8a0a765e870462fcf928`
- Compilation and ten targeted reporting/statistics tests passed.
- The method freeze will capture the final source hash before locked access.
