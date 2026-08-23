# Pre-locked telemetry/status hash audit completion

## Timing and scope

This audit correction was completed before method freeze and before any
authorized locked-test access. It does not change simulation, control,
success, telemetry collection, metric, selection, or statistical definitions.

## Diagnosis

The locked campaign audit already verified each result JSON and episode JSONL
hash. It recorded fresh hashes for telemetry, but did not compare that fresh
hash against the telemetry hash asserted by the immutable evaluation result.
It also did not include the per-evaluation status JSON in the locked evidence
list.

## Correction

For every one of the 21 locked evaluations, the paired audit now:

1. hashes the telemetry file and requires exact equality with
   `result.json -> artifacts.telemetry_sha256`;
2. hashes the status file and requires exact equality with
   `result.json -> artifacts.status_sha256`;
3. records both verified files in the final evidence inventory.

No file is opened by this code before the method-freeze authorization gate
invokes it.

## Verification

- `locked_test_guard.py` SHA256:
  `9944768a83daaa8321a9c65a5401650a8969fecf17fa75190b6c7ec9af54818b`
- Python compilation passed.
- Six targeted locked/report tests passed.
- A new test mutates the recorded telemetry hash and verifies that the audit
  refuses the evaluation.
- The later method freeze will capture this exact source hash.

