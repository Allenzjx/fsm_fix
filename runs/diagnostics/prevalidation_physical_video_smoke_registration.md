# Prevalidation physical video smoke registration

## Purpose and isolation

Before validation selection and method freeze, the final evaluator must prove
that its real Isaac camera path, diagnostic overlay, ImageIO/FFmpeg encoder,
and artifact hashes work. This test uses only the frozen development manifest;
it cannot read the locked manifest and cannot affect training, checkpoint
selection, or primary statistics.

## Fixed smoke

- controller: frozen FSM
- manifest:
  `data/scenario_manifests/development_v2.json`
- manifest SHA256:
  `f3d10d7340c06f78c200c44119bb2e17c81e587bd314b342ac90b49019ea2cdc`
- height: 50 mm
- exact scenario: `development-h050-0000`
- registered prior development outcome: success
- resolution: 960x540
- stride: 3 control steps
- FPS: 20
- codec: libx264
- output: a new
  `runs/diagnostics/prevalidation_video_smoke_attemptNNN` directory

The smoke must reproduce the exact scenario success and verify the result,
episode JSONL, telemetry, status, and MP4 hash chain. An incomplete or failed
attempt is preserved; recovery uses a new attempt.

## Freeze gate

`method_freeze.py` refuses to freeze without at least one passing physical
smoke. It selects the earliest passing technical attempt deterministically,
records earlier failed result files, and makes the passing result plus all
four artifacts immutable. It still does not resolve, stat, open, or hash the
locked manifest.

## Registered implementation hashes

- `prevalidation_video_smoke.ps1`:
  `22737419fe5df6f982ee82cdb06b9ac5714b74d40c0f785a2f364a361e4fbf4c`
- `method_freeze.py`:
  `2ded202a6e4b9c23791ecc94f9820e4edacd4d2a0cc687dc1ccad62881235180`
- `evaluate_controller.py`:
  `c082f724b957105129de7664d0cf869919e93cc95179c8657577f69baff984e4`

PowerShell parsing, Python compilation, and 11 targeted freeze/report/video
audit tests pass. The physical test remains pending until the formal training
GPU is free.
