# Method-B runtime-v7 development evaluator smoke attempt001

## Disposition

`PASS_EXECUTION`. The deliberate one-scenario, five-second timeout is excluded
from performance.

The evaluator restored checkpoint
`0f00a8207fff1fb096f9124f4e9b0df47cae9d9d579914913f47ef5f90ab704d`
under common config
`049386620349475e3c2c6800de3a9911ee9a8ec2e817c0bc75fb433e992e5ac1`.
Exact evaluator/environment/reward/model/reset source hashes and reset
provenance are recorded. Telemetry has 100 uniform rows and 122 fields; the
64 contiguous action-to-actuator fields (`policy_action_00` through
`final_wheel_target_rad_s_03`) are all finite.

Artifact hashes:

- episodes: `5e6fda6a96c6fc85e09f862ce75131cd2401673662c62907d4d266a05713b902`
- status: `dda45d8160dd24e4a6d640c4ea3b12e9c10ba7fee5e37dc0b9b5cd63ef7a2ffd`
- telemetry: `b002d130ec1742514a2b4e797de5dc30cd24394e569901aa9511d65352ff9595`
- result: `efcf369ebde61f255125bb2619b6eaceb60858110a128380c45536ee8782e27d`

The unchanged 20-scenario, 150-second development gate is authorized.
