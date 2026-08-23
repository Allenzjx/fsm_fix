# Pre-locked raw numeric recomputation audit

The final independent audit now reloads all 21 locked evaluation result files
and all 2,100 raw episode rows and recomputes:

- method summaries for FSM, B, and C;
- all equal-height primary and secondary distributions;
- per-height results;
- C-vs-FSM, C-vs-B, and B-vs-FSM paired comparisons;
- all registered 10,000-draw bootstrap intervals;
- aggregate resume values; and
- numeric claim details/statuses under the frozen claim protocol.

Each recomputed object is compared exactly with the corresponding
`resume_metrics.json` object. Coverage, row-count, and source-hash checks
remain independent additional gates. Thus editing a published point estimate,
interval, ablation result, or claim label before final audit produces
`FAILED`, even if file presence and episode counts remain plausible.

No statistical definition changed; this re-executes the already registered
calculation. The locked manifest remained unread during implementation and
the test uses synthetic evidence.

- `src/resume_validation/final_audit.py` SHA256:
  `7830faef9d3c3def29ad420991f33e933c680ce85701634ec9070233412603fc`
- Complete CPU regression: 187 tests, 0 failures.
- A synthetic claim-status alteration is rejected as a raw-recomputation
  mismatch.
