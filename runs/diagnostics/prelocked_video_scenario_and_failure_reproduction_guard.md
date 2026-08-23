# Pre-locked video scenario and failure-reproduction guard

Before method freeze or locked access, video inventory verification was
strengthened so that a replay cannot be described as the selected locked
episode merely because its scenario ID matches.

The inventory builder now:

- loads the hash-verified locked episode source;
- requires the replay episode to match all registered scenario fields,
  including geometry, initial state, friction, delay, and both seeds;
- records the replay failure reason;
- treats a failed replay as reproducing the locked outcome only when the
  failure reason also matches; and
- continues to disclose any outcome non-reproduction instead of hiding or
  replacing the selected episode.

This changes no video selection rule, locked result, evaluator, controller,
metric, training, or checkpoint. It only makes the evidence label more exact.
The locked manifest was not read.

- `src/resume_validation/video_selection.py` SHA256:
  `bcd85717dfe1841bc25b9d04c183fe94cc7884b49945ef60930b07bcd30f0a80`
- Complete CPU regression: 187 tests, 0 failures.
- The new regression rejects scenario-parameter and failure-reason mismatch.
