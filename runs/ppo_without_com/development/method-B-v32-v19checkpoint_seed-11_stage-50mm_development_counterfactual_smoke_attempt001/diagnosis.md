# V32 v19-checkpoint restoration smoke

## Disposition

`PASS`.

The exact frozen v19 checkpoint loaded under corrected v32 and completed the
one-scenario, deliberately 5-second development smoke without execution
failure. The TIMEOUT outcome is expected and is not an acceptance test.

## Restoration evidence

- checkpoint SHA-256:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`;
- telemetry contains 100 data rows and 122 columns;
- all 12 recorded residual-action channels are finite exact zero;
- telemetry SHA-256:
  `6418d01f48a446e0c929c18ae76aba994782f7eadb5147407857ee14c98801a9`;
- the telemetry file is byte-identical to the v22--v31 checkpoint
  restoration smokes;
- effective speed phases are `[8,9]` with corrected pre-gain floors
  `[1/3,1/4]`;
- execution passed with no reported failure.

## Frozen artifacts

- result:
  `333e713763ac558c8090f4ea20ab0c386377500ce1b479f674db876ee120f33a`
- episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- status:
  `785ec9d4ccfd8d55e40196e74cda0dcaf08d9a9eae581da719375bff89d88255`
- stdout:
  `a10c3896bd5cb013b55924e2fb58dd6f3f24bba2d94cd2094b9fc85c665645eb`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

The next gate is the fixed 20-scenario 50 mm development counterfactual.

