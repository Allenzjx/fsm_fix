# 100 mm raw replay diagnosis

Verdict: **strict traversal failure; command reproduction passed**.

- The runner dispatched all 68 aggregate state events and all 101 expanded
  commands with at most one control-step scheduling jitter.
- The independent audit found no non-wheel contact above 5 N, fall,
  command/joint limit violation, or non-finite sample.
- Final base x was 0.759542 m. Front wheel centers were at 1.035601 m and
  1.061186 m on the obstacle top; rear wheel centers were at 0.463722 m and
  0.449073 m, still at the 0.521312 m front riser.
- The accepted source recording itself ends at base x 0.622241 m with the same
  final logical target
  `[6.2, 2.3, 4.8, 10.6, -0.7, 0.0, 6.2, 0.0, 0, 0, 0, 0]`.
  It therefore does not contain a complete rear-wheel transfer under the
  pre-registered all-four-wheels-on-top definition.
- The current replay actually progressed farther than the source state
  snapshot, so this is not explained by a missing wheel command, a reversed
  sign, a shortened timestamp, or a more distant obstacle.

The accepted 100 mm log remains a valid partial command reference for FSM
initialization. It is not counted as a successful current traversal. FSM
development must add a contact-gated rear transfer/recovery instead of
weakening the success definition.
