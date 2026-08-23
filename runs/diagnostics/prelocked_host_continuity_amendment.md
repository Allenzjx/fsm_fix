# Pre-locked host-continuity amendment

This registration supersedes only the `method_freeze.py` hash recorded by
earlier pre-locked diagnostics. No evaluator, PPO implementation, controller,
scenario, metric, validation-selection rule, report statistic, or locked-test
definition changed.

The Windows host advertises a 600-second AC idle-sleep timeout. A reversible,
process-scoped execution-state helper was therefore added and registered in
the method-freeze critical-script inventory. The helper does not modify the
power plan and is bound to the exact full-pipeline-supervisor PID.

Current source registrations after the amendment:

- `final_audit.py`:
  `7830faef9d3c3def29ad420991f33e933c680ce85701634ec9070233412603fc`
- `report_generator.py`:
  `2e61ac9c12cb868bf260c9237e43ef94532c0ffc5dce0d3c5923af8427be8876`
- `locked_test_guard.py`:
  `201b37408bd436f471097f246ce73ec5622ff48ecad96d80738ecd55006556ba`
- `video_selection.py`:
  `a65abf5755aa839954677ba57db963a053910100792f5bf0f011cd713bf8435b`
- `method_freeze.py`:
  `28dd88a8ac030c91de397a2fb5539cf552e1fcad47af4ebd87f8220dec33bceb`
- `prevalidation_video_smoke.ps1`:
  `9d048f8128656207bc05831a9c99df9c1255bf493ff1bf07b1eb03bc07faab78`
- `full_pipeline_supervisor.ps1`:
  `cfd66f32b708376a553438b5e6c9f9a7f1f6d869a0cfe0d2522635ab7800b6b8`
- `pipeline_keep_awake.ps1`:
  `42a7c74d2778e3f80d8455c3b618b72a168ee4df75363a3b940fe6fc3106eaeb`

The complete CPU regression after this amendment passed: `188 passed`.
The locked manifest remained unopened and unhashed.
