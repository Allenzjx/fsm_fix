# Pre-locked experiment-ledger freeze

`experiment_ledger.csv` is now part of the method-freeze immutable evidence.
All prevalidation development, correction, recovery, negative-result, and
audit registrations must therefore be complete before the first locked
access. No post-locked row can be inserted, removed, or edited without
invalidating authorization.

Long-running supervisor state is intentionally separate:
`runs/orchestration/full_pipeline_supervisor_attempt001.json` may progress
from waiting to running to complete without rewriting the historical ledger.
The final audit hashes the frozen ledger and independently reports the
terminal pipeline status.

- `src/resume_validation/method_freeze.py` SHA256:
  `f8cbae085d07830a7fe61270472a48d48b78caee3f296c5c1479ee321ed8388e`
- Targeted method-freeze/final-audit tests: 4 passed.
- Most recent complete regression: 188 tests, 0 failures.
- The locked manifest remained unread.
