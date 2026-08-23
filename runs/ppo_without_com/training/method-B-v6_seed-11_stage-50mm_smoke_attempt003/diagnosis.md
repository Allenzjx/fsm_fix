# Method-B reward-v6 seed-11 50 mm smoke attempt003 diagnosis

## Disposition

`FAIL`. The forced-fall assertion raised
`RuntimeError: Forced-fall terminal reward preflight did not produce a finite
termination with the exact -200 fall term`.

All preceding attempt002 checks again passed, but the first forced-path
implementation evaluated its compound predicate before serializing the three
sub-results (termination flag, weighted fall component, and reward
finite/nonfinite state). The immutable result therefore proves the compound
assertion failed but cannot distinguish which subcondition caused it.

Isaac Lab source was inspected directly and confirms `_get_dones()` executes
before `_get_rewards()` in `DirectRLEnv.step`, so reward-order staleness is not
the explanation. The next diagnostic revision writes every forced-fall
sub-result and the terminal fall snapshot to `preflight` before asserting.
Attempt004 will repeat the real-Isaac smoke. The failed result SHA-256 is
`abcdc14f499312b571530bdf16035231e75f6b40da15f540b2cd1422ca1f818b`;
the event SHA-256 is
`eb73802862ba68865945c66af314833504ae169b0b8534293cad8b8bc4c15fa0`.
