# yam_arms

Testing and control scripts for I2RT YAM robot arms.

## Setup

```bash
cd robots_realtime/dependencies/i2rt

# Install dependencies (creates .venv automatically)
uv venv --python 3.11
uv pip install -e .
```

## CAN Bus Setup

Bring up the CAN interface before running any arm commands:

```bash
sudo ip link set can0 up type can bitrate 1000000
```

To verify:

```bash
ip link show can0
# Should show state UP
```

If the adapter is unresponsive, reset it:

```bash
sudo bash robots_realtime/dependencies/i2rt/scripts/reset_all_can.sh
```

## Testing the Arm

All commands are run from the `robots_realtime/dependencies/i2rt` directory:

```bash
cd robots_realtime/dependencies/i2rt
```

### Read Joint Positions (no movement)

```bash
uv run python test_arm.py --channel can0 --read-only
```

Continuously prints all 7 joint positions (6 arm + 1 gripper). Ctrl+C to exit.

### Full Arm Movement Test

```bash
uv run python test_arm.py --channel can0
```

Interactive step-by-step test that walks through each joint:

1. Shoulder pan (joint 0, +/-0.3 rad)
2. Shoulder pitch (joint 1, +0.3 rad)
3. Elbow (joint 2, +0.3 rad)
4. Wrist joints (joints 3-5, +/-0.3 rad each)
5. Gripper (close then open)

Each step waits for Enter before moving. Ctrl+C to abort at any time.

### Zero-Gravity Mode

Arm goes compliant so you can move it by hand:

```bash
uv run python i2rt/robots/motor_chain_robot.py --channel can0
```

### Gripper-Only Test

Opens and closes the gripper repeatedly:

```bash
uv run python i2rt/robots/motor_chain_robot.py --channel can0 --operation_mode test_gripper
```

### Hold Current Position

Locks the arm at its current pose:

```bash
uv run python i2rt/robots/motor_chain_robot.py --channel can0 --operation_mode stay_current_qpos
```

## Python API

```python
from i2rt.robots.get_robot import get_yam_robot
import numpy as np

robot = get_yam_robot(channel="can0")

# Read joint positions (7D: 6 arm joints + 1 gripper)
pos = robot.get_joint_pos()

# Command a target position
robot.command_joint_pos(np.array([0.0, 0.5, 1.0, 0.0, 0.0, 0.0, 0.8]))

# Smooth move to a target over 2 seconds
robot.move_joints(np.array([0.0, 0.5, 1.0, 0.0, 0.0, 0.0, 0.8]), time_interval_s=2.0)

# Gripper: index 6, range 0.0 (closed) to 0.8 (open)

# Cleanup
robot.close()
```

## Gripper Types

| Type | Flag | Notes |
|------|------|-------|
| `linear_4310` | `--gripper_type linear_4310` | Default. Standard linear gripper |
| `linear_3507` | `--gripper_type linear_3507` | Lightweight linear |
| `crank_4310` | `--gripper_type crank_4310` | Zero-linkage crank |
| `no_gripper` | `--gripper_type no_gripper` | Arm only, no gripper |

## Troubleshooting

- **"No such device"**: CAN interface is not up. Run `sudo ip link set can0 up type can bitrate 1000000`.
- **"No module named 'i2rt'"**: Run `uv pip install -e .` from the `robots_realtime/dependencies/i2rt` directory.
- **Joint limit violation on startup**: Arm may need recalibration. Move it to the zero position and power cycle.
- **Motors unresponsive**: Run `sudo bash scripts/reset_all_can.sh` to reset the CAN adapter.
