# Rear-right support-extension grid 009 diagnosis

- Scenario: `development-h100-0000`.
- Single varied parameter: phase-9/10 rear-right wheel-center extension
  (`0/5/10/15/20 mm`), five Latin-rotated candidates per value.
- Result: **0 / 25 strict successes**.
- Outcomes: 21 body/link collisions and 4 global timeouts.
- Terminal phases: 12 in phase 8 and 13 in phase 10.
- Collision bodies: 12 `rear_left_bot` contacts before intervention and 9
  late `front_right_bot` contacts.
- Result SHA256:
  `49c6fcc036e0a1ba523dd330cee2a3cd07491fb1a3949adf3a5fbce9fdce3637`.

The phase-8 collision candidate IDs exactly matched grid 008, independently
confirming a deterministic environment-index/contact-solver effect before the
varied parameter. Latin rotation distributed that attrition across extension
values instead of binding every value to one index residue.

All 0--15 mm candidates had zero baseline-IK fallback. Two 20 mm candidates
accumulated 6 and 639 IK fallbacks, so the 20 mm timeout is not evidence for a
fully applied intervention. Fully applied 10 mm and 15 mm candidates reached
three collision-free global timeouts, but none satisfied success:

- 10 mm: terminal upward forces
  13.7930 / 0.0000 / 0.5295 / 13.8418 N;
- 15 mm candidate 7:
  12.0515 / 0.0000 / 0.5719 / 14.8291 N;
- 15 mm candidate 15:
  12.8309 / 0.0000 / 1.0913 / 14.6244 N.

The reachable extensions successfully put the rear-right wheel near the
0.150 m top plane and loaded it at about 14 N. They did not load the
front-right/rear-left diagonal: front-right remained 0 N and rear-left stayed
below 1.1 N. Rear-right extension alone is therefore rejected.

Grid 010 fixes the fully reachable 15 mm rear-right extension and varies only
a common front-right/rear-left extension over 0/2/4/6/8 mm, again with Latin
rotation. It also records, over the whole trajectory, the highest achieved
minimum per-wheel upward force and the longest continuous all-wheel
upward-force dwell, rather than relying only on terminal snapshots.
