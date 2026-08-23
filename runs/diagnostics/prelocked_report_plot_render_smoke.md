# Pre-locked report-plot render smoke

All nine required report plots were rendered in an isolated synthetic
campaign using the installed production libraries:

- Matplotlib 3.10.3 with the Agg backend;
- TensorBoard 2.20.0 event loading;
- real event-file scalar parsing;
- complete FSM/B/C height and paired synthetic rows.

The smoke produced valid nontrivial PNGs for training return, validation
success, success by height, margin, pitch rate, saturation, paired margin,
paired pitch, and failure distribution. A separate local libx264/ImageIO
probe encoded and decoded a 960x540, 20 FPS, five-frame MP4 with codec `h264`
and exact frame count.

These are compatibility checks only, not experimental outcomes. No synthetic
number can enter validation, locked results, or final reports. The locked
manifest remained unread.

- Complete CPU regression including the nine-plot smoke: 188 tests, 0
  failures.
- Physical Isaac video smoke remains required before method freeze.
