# Post-transfer activation grid 014 diagnosis

- Fixed extensions: front-right/rear-left 14 mm, rear-right 15 mm.
- Varied phase-9 offset-ramp start progress: 0/0.2/0.4/0.6/0.8.
- Five Latin-rotated repetitions per value.
- Raw environment result: **4 / 25 strict successes**, 12 collisions, 9
  timeouts.
- Engineering-admissible result: **0 / 25**, because every raw success still
  contained rear-left IK fallback.
- Result SHA256:
  `c341b10d84721edc5f901fc4914e9513edd4cb9046c01ff2c2e4481368fa528d`.

Delaying the phase-9 ramp preserved the true four-point-support mechanism and
reduced fallback substantially:

- start 0.2, candidate 22: success, best minimum 3.1302 N, 106 fallback steps;
- start 0.4, candidate 10: success, best minimum 4.7065 N, 95 fallback steps;
- start 0.4, candidate 19: success, best minimum 6.0697 N, 92 fallback steps;
- start 0.8, candidate 20: success, best minimum 7.0620 N, 95 fallback steps.

The best start-0.4 snapshot was
6.207/8.190/8.282/6.070 N. The start-0.8 success was nearly balanced at
7.114/7.062/7.473/7.066 N. These margins are well above the unchanged 2 N
threshold.

Per-leg fallback counts isolated the remaining invalidity. Every successful
candidate had exactly 0/0/N/0 counts in front-left/front-right/rear-left/
rear-right order, with N=92--106. The front-right 14 mm and rear-right 15 mm
commands are therefore reachable along the successful path; only the
rear-left 14 mm command crosses unreachable intermediate targets. Delaying
the common ramp cannot remove that leg-specific conflict by itself.

Grid 015 fixes start progress at 0.4, front-right extension at 14 mm, and
rear-right extension at 15 mm. It varies only rear-left extension over
8/9.5/11/12.5/14 mm with Latin rotation. The 14 mm value is an exact command
control; 8--11 mm covers the previously observed fully reachable range. A
candidate is selectable only if it both completes strict success and reports
0/0/0/0 per-leg baseline IK fallback.
