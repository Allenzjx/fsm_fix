# Formal 75 mm full development attempt 042 diagnosis

- Execution passed for all 20 scenarios under `fsm.yaml` SHA-256
  `1943be80e44e57ff63b479195970e0e02d0bad6f22bc4712337cec51fae243af`.
- Strict result: 7/20 successes (35%). The other 13 outcomes were global
  `TIMEOUT`; there were no collision, phase-timeout, joint-limit, or numerical
  failure classifications.
- All 20 scenarios had zero analytic-IK fallback on every leg, zero support
  clamp count, and no terminal non-wheel contact diagnostic. Nineteen of 20
  ended with all four full wheels on top.
- Successful scenario IDs were 0001, 0002, 0008, 0012, 0013, 0014, and 0017.
  Their telemetry ended at 149.85, 149.90, 147.85, 149.70, 149.60, 149.80,
  and 149.60 s respectively. These late successes show that the formal policy
  is feasible but has little time margin.
- The seven successful terminal upward-force vectors were all above the
  unchanged 2 N minimum. The selected high-load shortening generally ended at
  2/0/0/2 mm; scenario 0002 had a transient 0.0125 mm rear-left trim as the
  hysteresis controller responded to its measured force.
- Result SHA-256:
  `86bb143c54420ab932a7d4141da3692b1a1c8b462255d7cfaeb1aa7dc0c27b5c`.
  Episodes SHA-256:
  `a05a0ba89a7ac98f6e3dad765f61e5dc39c6618cb6a2a3233b1f06e92d8fd1a9`.
  Telemetry SHA-256:
  `afb32ab15c9e09bdf465c97ece5d0fdb73b892420304aff5a0868eea0da0b5ff`.

This establishes a nonzero formal 75 mm FSM baseline. The configuration must
not be frozen until the unchanged 50 and 100 mm endpoint behaviors are rerun
under this exact same configuration hash.
