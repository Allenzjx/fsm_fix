# Pre-locked all-video decode inventory guard

Before method freeze and locked access, the decode verification used by the
physical prevalidation smoke was extended to every deterministically selected
final replay.

For each MP4, `video_selection.py` now reopens the finished file, decodes its
first frame, obtains the decoder metadata, counts all decodable frames, and
requires:

- 960x540 decoded pixels;
- 20 FPS within 0.05;
- decoded frame count equal to the evaluator's captured frame count.

The codec and complete probe are stored in `video_inventory.json`.
`final_audit.py` independently requires the registered geometry, timing, and
frame-count fields. MP4 hash and nonzero-size checks remain in force.

No selected episode, category, outcome, evaluator, training, metric, or
locked protocol changed. The locked manifest remained unread.

- `src/resume_validation/video_selection.py` SHA256:
  `a65abf5755aa839954677ba57db963a053910100792f5bf0f011cd713bf8435b`
- `src/resume_validation/final_audit.py` SHA256:
  `cd5c1f298d99234c10e853be204293351668387b8d00ac915f96b71f4bc5552d`
- Complete CPU regression: 187 tests, 0 failures.
