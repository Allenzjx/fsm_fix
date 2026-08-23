"""Height-conditioned FSM phase boundaries derived from replay event timing."""

from __future__ import annotations


LOW_HEIGHT_M = 0.05
HIGH_HEIGHT_M = 0.10

# Boundary i is the upper normalized-reference limit of phase i.
# The 100 mm front-leg placement occurs at u=0.535--0.560 and its next
# physical-forward roll begins at u=0.5747. The phase-5 upper limit is placed
# at u=0.574, after placement and before that roll command.
LOW_PHASE_BOUNDARIES = (
    0.01,
    0.04,
    0.16,
    0.20,
    0.38,
    0.50,
    0.64,
    0.78,
    0.88,
    0.94,
    1.00,
)
HIGH_PHASE_BOUNDARIES = (
    0.01,
    0.04,
    0.16,
    0.20,
    0.38,
    0.574,
    0.64,
    0.78,
    0.88,
    0.94,
    1.00,
)


def phase_boundaries_for_height(height_m: float) -> tuple[float, ...]:
    """Linearly interpolate the pre-registered source-event boundaries."""

    alpha = min(1.0, max(0.0, (float(height_m) - LOW_HEIGHT_M) / (HIGH_HEIGHT_M - LOW_HEIGHT_M)))
    return tuple(
        low + alpha * (high - low)
        for low, high in zip(LOW_PHASE_BOUNDARIES, HIGH_PHASE_BOUNDARIES, strict=True)
    )
