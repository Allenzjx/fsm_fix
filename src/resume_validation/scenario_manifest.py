from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REFERENCE_OBSTACLE_CENTER_X_M = 1.55
REFERENCE_OBSTACLE_LENGTH_M = 2.0573755975573045
REFERENCE_OBSTACLE_FRONT_X_M = REFERENCE_OBSTACLE_CENTER_X_M - 0.5 * REFERENCE_OBSTACLE_LENGTH_M
# Measured after the mandatory 2 s settle in the corrected DirectRLEnv replay.
REFERENCE_INITIAL_FRONT_WHEEL_X_M = 0.2532046139240265
REFERENCE_INITIAL_DISTANCE_M = REFERENCE_OBSTACLE_FRONT_X_M - REFERENCE_INITIAL_FRONT_WHEEL_X_M


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    obstacle_height_m: float
    obstacle_front_x_m: float
    initial_distance_m: float
    initial_pitch_rad: float
    friction: float
    actuator_delay_steps: int
    sensor_noise_std: float
    environment_seed: int
    noise_seed: int


def make_scenarios(
    *,
    split: str,
    seed: int,
    episodes_per_height: int,
    heights_m: Iterable[float] = (0.05, 0.075, 0.10),
) -> list[Scenario]:
    generator = random.Random(seed)
    scenarios: list[Scenario] = []
    for height in heights_m:
        for index in range(episodes_per_height):
            environment_seed = generator.randrange(0, 2**31)
            noise_seed = generator.randrange(0, 2**31)
            scenarios.append(
                Scenario(
                    scenario_id=f"{split}-h{int(round(height * 1000)):03d}-{index:04d}",
                    obstacle_height_m=float(height),
                    # Vectorized environments use one translationally equivalent
                    # obstacle location; paired robustness comes from relative
                    # initial distance, pose, friction, latency and noise.
                    obstacle_front_x_m=REFERENCE_OBSTACLE_FRONT_X_M,
                    initial_distance_m=REFERENCE_INITIAL_DISTANCE_M + generator.uniform(-0.025, 0.025),
                    initial_pitch_rad=generator.uniform(-0.02, 0.02),
                    friction=generator.uniform(0.9, 1.2),
                    actuator_delay_steps=generator.choice((0, 1, 2)),
                    sensor_noise_std=generator.uniform(0.0, 0.005),
                    environment_seed=environment_seed,
                    noise_seed=noise_seed,
                )
            )
    return scenarios


def manifest_bytes(scenarios: Iterable[Scenario], metadata: dict | None = None) -> bytes:
    payload = {
        "metadata": metadata or {},
        "scenarios": [asdict(item) for item in scenarios],
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def write_locked_manifest(path: str | Path, scenarios: Iterable[Scenario], metadata: dict | None = None) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = manifest_bytes(scenarios, metadata)
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="ascii")
    return digest


def verify_manifest(path: str | Path) -> bool:
    path = Path(path)
    record = path.with_suffix(path.suffix + ".sha256").read_text(encoding="ascii").split()[0]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    return record == actual
