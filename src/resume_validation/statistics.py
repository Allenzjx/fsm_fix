from __future__ import annotations

import math
import random
from statistics import mean, median, pstdev
from typing import Iterable, Mapping, Sequence


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("total must be positive")
    if successes < 0 or successes > total:
        raise ValueError("successes must be within [0, total]")
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denom
    return center - half, center + half


def quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("quantile requires at least one value")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def bootstrap_mean_ci(values: Sequence[float], *, draws: int = 10_000, seed: int = 20260727) -> tuple[float, float]:
    values = tuple(float(value) for value in values)
    if not values:
        raise ValueError("bootstrap requires at least one value")
    generator = random.Random(seed)
    estimates = [
        mean(generator.choice(values) for _ in range(len(values)))
        for _ in range(int(draws))
    ]
    return quantile(estimates, 0.025), quantile(estimates, 0.975)


def paired_bootstrap_ci(
    left: Sequence[float],
    right: Sequence[float],
    *,
    draws: int = 10_000,
    seed: int = 20260727,
) -> tuple[float, float]:
    if len(left) != len(right) or not left:
        raise ValueError("paired inputs must have equal non-zero length")
    delta = [float(r) - float(l) for l, r in zip(left, right)]
    return bootstrap_mean_ci(delta, draws=draws, seed=seed)


def stratified_bootstrap_mean_ci(
    values_by_stratum: Mapping[object, Sequence[float]],
    *,
    draws: int = 10_000,
    seed: int = 20260727,
) -> tuple[float, float]:
    """Bootstrap an equal-stratum-weighted mean.

    Each draw resamples with replacement inside every stratum, computes that
    stratum's mean, and then gives all non-empty strata equal weight. This is
    the registered aggregate behavior for 50/75/100 mm even when an invalid
    continuous metric leaves unequal valid counts across heights.
    """

    groups = {
        key: tuple(float(value) for value in values)
        for key, values in values_by_stratum.items()
    }
    if not groups or any(not values for values in groups.values()):
        raise ValueError("every registered bootstrap stratum must be non-empty")
    generator = random.Random(seed)
    estimates: list[float] = []
    for _ in range(int(draws)):
        stratum_means = [
            mean(generator.choice(values) for _ in range(len(values)))
            for values in groups.values()
        ]
        estimates.append(mean(stratum_means))
    return quantile(estimates, 0.025), quantile(estimates, 0.975)


def describe(values: Iterable[float]) -> dict[str, float | int | list[float]]:
    rows = [float(value) for value in values]
    if not rows:
        return {"count": 0}
    return {
        "count": len(rows),
        "mean": mean(rows),
        "median": median(rows),
        "std_population": pstdev(rows),
        "q25": quantile(rows, 0.25),
        "q75": quantile(rows, 0.75),
        "bootstrap_95_ci": list(bootstrap_mean_ci(rows)),
    }
