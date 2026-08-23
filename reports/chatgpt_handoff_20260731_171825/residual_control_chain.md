# Residual control chain

```mermaid
flowchart LR
    A["PPO Gaussian sample / deterministic mean"] --> B["sample clipping to [-1,1]"]
    B --> C["phase 8-10 + IMU hazard gate"]
    C --> D["v34 projection and channel mask"]
    D --> E["phase gain 3/4/3 + hard clip"]
    E --> F["wheel-center x/z scale"]
    F --> G["add frozen FSM wheel-center reference"]
    G --> H["analytic IK; nearest safe branch"]
    H --> I["all-leg invalid fallback to FSM"]
    I --> J["servo rate limit"]
    J --> K["joint safe-limit clamp"]
    K --> L["articulation position command"]
```

There is no explicit workspace projection/clipping step. Workspace infeasibility is detected by IK; if any leg is invalid, all residual leg targets fall back to the baseline for that environment.

```mermaid
flowchart LR
    A["PPO wheel-speed channels"] --> B["phase/IMU gate + v34 phase-9 counter-yaw projection"]
    B --> C["phase gain + hard clip"]
    C --> D["× 0.10 rad/s"]
    D --> E["add FSM wheel-speed reference"]
    E --> F["clip to ±2.094 rad/s"]
    F --> G["6 rad/s² acceleration limit"]
    G --> H["per-wheel forward-sign mapping"]
    H --> I["articulation velocity command"]
```

Exact all-zero applied action bypasses IK numerical round trips and residual wheel acceleration limiting, returning the frozen FSM commands exactly (`src\resume_validation\residual_rl_env.py:1647-1689`). Evaluation uses `outputs["mean_actions"]`, so PPO playback is deterministic (`src\resume_validation\evaluate_controller.py:728-733`).
