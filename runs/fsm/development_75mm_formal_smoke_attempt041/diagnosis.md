# Formal 75 mm smoke attempt 041 diagnosis

- Execution: passed; one development scenario evaluated to the unchanged
  150 s episode limit.
- Strict result: 0/1. `development-h075-0000` ended as `TIMEOUT`; this failure
  is retained and is not reclassified as success.
- Formal provenance: `fsm.yaml` SHA-256
  `1943be80e44e57ff63b479195970e0e02d0bad6f22bc4712337cec51fae243af`;
  rear-transfer wheel speeds 0/0/0.3/0.3 rad/s; post-transfer speed
  0.075 rad/s; support unload 4/8 N hysteresis, 0.75 mm/s rate, 2 mm bound.
- Terminal physical state: all four full wheels were on top, support score was
  0.9999503, and upward wheel forces were
  9.894/3.807/4.102/10.722 N. Front-right support remained below the
  unchanged 4 N unload-release threshold at timeout.
- Safety/reachability: analytic-IK fallback was 0/0/0/0, clamp count was zero,
  joint-limit diagnostics and non-wheel contact diagnostics were empty, and
  terminal shortening was 2/0/0/2 mm.
- Result SHA-256:
  `43c9a8483222baa0a6eda4451896bacbfe5e91e665bedf0a0267338bf62a8d39`.
  Episodes SHA-256:
  `c3bc6c59bd4ee60b72a7c86c75cc478e0092ef82200fd683698bbc095e538838`.
  Telemetry SHA-256:
  `653401d62913b009fc8e59ca3972fcd1c1e83361dcf9cce12cfeb346511fde8d`.

The selected diagnostic policy had a 4/25 repeat success rate, so this single
timeout neither validates nor rejects the formal policy. The next auditable
step is the already planned full 20-scenario development batch with the same
configuration hash.
