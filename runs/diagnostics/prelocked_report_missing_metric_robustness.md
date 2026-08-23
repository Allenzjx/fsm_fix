# Pre-locked report missing-metric robustness correction

## Timing and scope

This correction was made before validation selection, method freeze, and any
authorized locked-test manifest access. It changes report rendering only.
Training, evaluation, success, telemetry, metric, selection, claim, and
bootstrap definitions are unchanged.

## Diagnosed failure mode

The report generator already retained `None` for an unavailable continuous
metric, but two presentation paths assumed a complete value:

- the Markdown primary table multiplied/formatted an unavailable equal-height
  margin directly;
- a required paired histogram raised when a height had no complete paired
  continuous values.

That behavior could prevent publication of an honest negative/missing-data
result, contrary to the registered rule that missing metrics are disclosed
and never filled with zero.

## Correction

- Optional continuous values now render as
  `不可计算（有效数据不足）`.
- A required plot with no complete paired values is still published, with an
  explicit unavailable-data annotation and a pointer to the missing-pair
  counts in `paired_differences.csv`.
- Empty method distributions are plotted as missing (`NaN`), never as zero,
  and labeled by method.
- Claim evaluation accepts missing pitch values and returns
  `NOT_VERIFIED` without inventing a percentage.
- The generated resume wording reports insufficient valid pairs instead of
  applying numeric formatting to `None`.

## Verification

- `report_generator.py` SHA256:
  `dc91d6c2e730d87edfa7956589b2d1a5fa8fab8c641bcac9b0e47ad9b1318e03`
- Python compilation passed.
- Targeted report/statistics tests: 6 passed, including a new fully missing
  continuous-metric claim case.
- The later method freeze will hash this exact source before locked access.

