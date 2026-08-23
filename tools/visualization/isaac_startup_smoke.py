"""Minimal 120-frame Isaac startup/render smoke used by startup diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ISAACLAB_ROOT = Path(r"C:\robotics_sim\IsaacLab")
for extension in (ISAACLAB_ROOT / "source").iterdir():
    if extension.is_dir() and str(extension) not in sys.path:
        sys.path.append(str(extension))
if str(ISAACLAB_ROOT) not in sys.path:
    sys.path.append(str(ISAACLAB_ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--frames", type=int, default=120)
parser.add_argument("--capture-images", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.capture_images and not args.enable_cameras:
    parser.error("--capture-images requires --enable_cameras")
simulation_app = AppLauncher(args).app

import cv2
import numpy as np
import torch
import isaaclab.sim as sim_utils
from isaaclab.sensors.camera import Camera, CameraCfg


def main() -> int:
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": "resume_validation.isaac_startup_smoke.v1",
        "started_at": time.time(),
        "headless": bool(args.headless),
        "enable_cameras": bool(args.enable_cameras),
        "requested_frames": int(args.frames),
        "completed_frames": 0,
        "passed": False,
        "failures": [],
    }
    sim = None
    try:
        sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args.device))
        ground = sim_utils.GroundPlaneCfg()
        ground.func("/World/Ground", ground)
        light = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
        light.func("/World/Light", light)
        cube = sim_utils.CuboidCfg(
            size=(0.35, 0.35, 0.35),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.12, 0.45, 0.9)),
        )
        cube.func("/World/Cube", cube, translation=(0.0, 0.0, 0.2))
        camera = None
        if args.capture_images:
            sim_utils.create_prim("/World/CameraOrigin", "Xform")
            camera = Camera(
                CameraCfg(
                    prim_path="/World/CameraOrigin/Camera",
                    update_period=0,
                    height=720,
                    width=1280,
                    data_types=["rgb"],
                    spawn=sim_utils.PinholeCameraCfg(
                        focal_length=24.0,
                        focus_distance=4.0,
                        horizontal_aperture=20.955,
                        clipping_range=(0.05, 100.0),
                    ),
                )
            )
        sim.set_camera_view(eye=(2.0, -2.0, 1.6), target=(0.0, 0.0, 0.2))
        sim.reset()
        if camera is not None:
            camera.set_world_poses_from_view(
                torch.tensor([[2.0, -2.0, 1.6]], device=sim.device),
                torch.tensor([[0.0, 0.0, 0.2]], device=sim.device),
            )
        first = None
        last = None
        for index in range(int(args.frames)):
            if not simulation_app.is_running():
                raise RuntimeError(f"SimulationApp stopped at frame {index}")
            sim.step(render=bool(args.capture_images))
            if camera is not None:
                camera.update(dt=sim.get_physics_dt())
                rgb = camera.data.output.get("rgb")
                if rgb is None or rgb.numel() == 0:
                    raise RuntimeError(f"Camera produced no RGB at frame {index}")
                frame = rgb[0, :, :, :3].detach().cpu().numpy().astype(np.uint8)
                if index == 0:
                    first = frame.copy()
                last = frame.copy()
            result["completed_frames"] = index + 1
        if first is not None and last is not None:
            cv2.imwrite(str(output / "first.png"), cv2.cvtColor(first, cv2.COLOR_RGB2BGR))
            cv2.imwrite(str(output / "last.png"), cv2.cvtColor(last, cv2.COLOR_RGB2BGR))
            result["first_mean"] = float(first.mean())
            result["last_mean"] = float(last.mean())
            result["mean_absolute_change"] = float(np.mean(np.abs(last.astype(float) - first.astype(float))))
        result["passed"] = True
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
        result["traceback"] = traceback.format_exc()
    finally:
        result["finished_at"] = time.time()
        (output / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        simulation_app.close(wait_for_replicator=False)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
