# Pre-locked final-delivery audit registration

## Status and scope

`REGISTERED_BEFORE_VALIDATION_AND_METHOD_FREEZE`.

This addition changes only post-experiment evidence verification. It does not
change the evaluator, FSM, PPO architecture, reward, randomization, training
budget, checkpoint selection, metric definition, scenario manifests, or
locked-test protocol. The locked-test manifest was not read or hashed while
implementing or testing it.

## Required independent checks

The final audit must fail closed unless all of the following reproduce:

- verified method freeze and the 21-evaluation / 2,100-episode paired locked
  audit;
- result, episode, telemetry, and status hashes for every locked evaluation;
- exact report, six-table, nine-PNG, unit-test, and experiment-ledger
  coverage;
- exact 300 FSM, 900 method-B, and 900 method-C scenario rows, with all
  seeds 11/29/47 and no duplicate paired keys;
- video inventory bound to its deterministic selection file, nine complete
  method-height category requirements, locked source results and episodes,
  selected checkpoints, replay results, and MP4 hashes;
- report metrics bound to the same unit-test XML, video inventory, method
  freeze, locked manifest, and report-generator source;
- claim statuses, validation fallback disclosures, and conservative Chinese
  resume wording with no placeholders.

A negative scientific result or a disclosed validation fallback may produce
`PASS_WITH_DISCLOSURES`; evidence drift or missing coverage must produce
`FAILED`.

## Registered implementation

- `src/resume_validation/final_audit.py` SHA256:
  `7830faef9d3c3def29ad420991f33e933c680ce85701634ec9070233412603fc`
- `src/resume_validation/report_generator.py` SHA256:
  `2e61ac9c12cb868bf260c9237e43ef94532c0ffc5dce0d3c5923af8427be8876`
- `src/resume_validation/locked_test_guard.py` SHA256:
  `201b37408bd436f471097f246ce73ec5622ff48ecad96d80738ecd55006556ba`
- `src/resume_validation/video_selection.py` SHA256:
  `a65abf5755aa839954677ba57db963a053910100792f5bf0f011cd713bf8435b`
- `src/resume_validation/method_freeze.py` SHA256:
  `f8cbae085d07830a7fe61270472a48d48b78caee3f296c5c1479ee321ed8388e`
- `scripts/12_final_audit.ps1` SHA256:
  `4ee3e9fe23dd488b848ed68feef149a400f3e49f0d934f1af24732fb2fcc38b8`
- `scripts/full_pipeline_supervisor.ps1` SHA256:
  `cfd66f32b708376a553438b5e6c9f9a7f1f6d869a0cfe0d2522635ab7800b6b8`

The method-freeze critical-source list includes all five Python audit/report
modules above. It also includes the formal B/C training, validation, freeze,
locked-test, video, report, final-audit, recoverable state-machine, and
full-pipeline-supervisor PowerShell entry points. The earlier report and
physical-video registration hashes remain historical records of their
respective intermediate states; this document registers the later composed
final state.

## Verification

The complete CPU regression suite passes: 185 tests, 0 failures. A new
end-to-end synthetic audit test reaches `PASS` with a complete hash chain,
then modifies the deterministic video selection and confirms the same audit
returns `FAILED`.
