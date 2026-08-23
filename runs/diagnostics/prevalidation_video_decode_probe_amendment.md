# Prevalidation video decode-probe amendment

This prevalidation amendment strengthens the already registered physical
camera/encoder smoke. A non-empty MP4 with a matching write-time hash is no
longer sufficient. The fixed development-scenario smoke must now decode its
first frame, count all encoded frames, and record `video_probe.json` with:

- video SHA256;
- decoded width 960 and height 540;
- decoded FPS 20.0 within 0.05;
- decoder-reported codec;
- decoded frame count exactly matching the evaluator's captured frame count.

`method_freeze.py` independently verifies the probe and makes its path and
hash immutable along with the video, result, episodes, telemetry, and status.
The actual physical smoke remains pending a free GPU. A failed decode is
preserved and requires a new attempt.

No evaluator, camera pose, overlay, FSM, metric, training, scenario, or locked
definition changed, and the locked manifest remained unread.

- `scripts/prevalidation_video_smoke.ps1` SHA256:
  `9d048f8128656207bc05831a9c99df9c1255bf493ff1bf07b1eb03bc07faab78`
- `src/resume_validation/method_freeze.py` SHA256:
  `af760f13224f55f6cffa4f2eac2898f1906265770cb209933a1adee80966c7a5`
- PowerShell parsing passed.
- Complete CPU regression: 187 tests, 0 failures.
