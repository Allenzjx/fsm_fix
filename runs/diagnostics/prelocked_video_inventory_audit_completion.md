# Pre-locked video inventory audit completion

This correction was completed before method freeze and locked-test access.
The frozen category-selection rule is unchanged.

The deterministic selector already added a typical failure whenever any
failure existed, but the later inventory check inferred category requirements
from the selected subset itself. That check could not independently detect an
omitted category. The selection artifact now records, for all nine
method-height groups, the full locked episode/success/failure counts and the
categories required before deduplication. Inventory generation requires every
recorded category after replay.

Inventory generation now also verifies:

- selected locked result and episode JSONL hashes;
- selected checkpoint hashes;
- replay episode JSONL hashes;
- exact replay scenario ID and locked outcome label.

No category is selected from appearance, and no replay changes primary
statistics.

- `video_selection.py` SHA256:
  `26c3e531c7a1a9472475576bd6f6364e68fc10f5ef9112c0b2ed3054651d0480`
- Compilation and four targeted video/locked-audit tests passed.
- The later method freeze will capture this source hash.

