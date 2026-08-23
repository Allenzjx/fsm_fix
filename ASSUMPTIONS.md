# Assumptions

1. Physical forward is world/local environment +X.
2. The accepted 50/100 mm logs are command-space references, not proof of
   current physical success; both are re-run.
3. The recorded union of logical servo commands is the conservative safe
   envelope for the derived validation USD.
4. `ContactSensor.net_forces_w` is real simulated force data. Opposing-body
   identity is unavailable from that tensor and is resolved with known box
   geometry; this limitation is explicit in every report.
5. The actor treats obstacle geometry as a noisy simulated-perception proxy,
   not as a claim that the present robot has a production vision stack.
6. Success is a debounced geometric/contact/stability condition and is never
   reduced to forward root position.
7. The placeholder resume values 84%, 91%, 10 mm, and 31% are hypotheses only.
8. The accepted JSONL does not embed one authoritative playback profile.
   Current replay code defaults to raw, while preserved GUI/E2E evidence and
   the earlier physical-success plan use fast/motion-only timing (no idle-gap
   cap). Both timing interpretations are retained and labeled. The raw profile
   is the formal source reproduction because it preserves every recorded
   timestamp. Fast/no-cap remains a diagnostic only: its completed 50 mm run
   changed terminal load distribution and failed the unchanged 2 N per-wheel
   support criterion even though the raw profile passed.
