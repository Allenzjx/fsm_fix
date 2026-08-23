# Verified local runtime

This project reuses the existing `env_isaaclab` environment; it does not
upgrade or replace core simulation packages.

- Windows 11 Home 25H2, build 26200
- NVIDIA GeForce RTX 4080 Laptop GPU, 12 GB
- NVIDIA driver 581.29
- Python 3.11.15 (`C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe`)
- Isaac Sim 5.1.0.0
- Isaac Lab 0.54.3
- PyTorch 2.7.0+cu128
- CUDA runtime reported by PyTorch: 12.8
- skrl 2.0

The verified launcher is:

```powershell
cd C:\robotics_sim\IsaacLab
conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p <script.py> --headless
```

Machine-readable package, GPU, disk, Conda, PowerShell and launcher evidence
is in `system_inventory.json`. Exact package versions in generated run
artifacts are authoritative if this file and the environment later diverge.
