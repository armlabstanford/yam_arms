#!/usr/bin/env python3
"""Keyboard teleoperation for a single YAM arm.

Usage:
    uv run python scripts/keyboard_teleop.py --channel can0

Controls:
    1-6     : select arm joint (shoulder pan → wrist 3)
    7       : select gripper
    ↑ / k   : increase selected joint
    ↓ / j   : decrease selected joint
    [ / ]   : halve / double step size
    g       : toggle gripper open/closed
    r       : re-read current arm position as new target
    0       : go to home (all zeros, gripper open)
    q / ESC : quit (arm stays in place)
"""

import argparse
import curses
import sys
import time

import numpy as np

sys.path.insert(0, "dependencies/i2rt")
from i2rt.robots.get_robot import get_yam_robot

JOINT_NAMES = [
    "Shoulder Pan",
    "Shoulder Pitch",
    "Elbow",
    "Wrist 1",
    "Wrist 2",
    "Wrist 3",
    "Gripper",
]

GRIPPER_OPEN = 0.8
GRIPPER_CLOSED = 0.0
GRIPPER_JOINT = 6


def draw(stdscr, target_q, actual_q, selected, step, channel):
    stdscr.clear()
    stdscr.addstr(0, 0, "=== YAM Arm Keyboard Teleop ===")
    stdscr.addstr(1, 0, f"Channel: {channel}   Step: {step:.4f} rad   (q to quit)")
    stdscr.addstr(3, 0, "  Key  Joint              Target      Actual")
    stdscr.addstr(4, 0, "  ---  -----------------  ----------  ----------")
    for i, name in enumerate(JOINT_NAMES):
        arrow = ">" if i == selected else " "
        stdscr.addstr(
            5 + i, 0,
            f"  [{i + 1}] {arrow} {name:<17s}  {target_q[i]:+.4f}    {actual_q[i]:+.4f}",
        )
    stdscr.addstr(13, 0, "")
    stdscr.addstr(14, 0, "1-7:select joint  ↑/k:+  ↓/j:-  g:gripper  [:step/2  ]:step*2  r:resync  0:home")
    stdscr.refresh()


def run(stdscr, args):
    robot = get_yam_robot(channel=args.channel)

    target_q = robot.get_joint_pos().copy().astype(np.float64)
    actual_q = target_q.copy()

    selected = 0
    step = args.step
    gripper_open = target_q[GRIPPER_JOINT] > 0.4

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    dt = 1.0 / args.rate_hz

    try:
        while True:
            t0 = time.monotonic()

            key = stdscr.getch()
            if key != -1:
                if ord("1") <= key <= ord("7"):
                    selected = key - ord("1")
                elif key in (curses.KEY_UP, ord("k")):
                    if selected == GRIPPER_JOINT:
                        target_q[GRIPPER_JOINT] = min(1.0, target_q[GRIPPER_JOINT] + step)
                    else:
                        target_q[selected] += step
                elif key in (curses.KEY_DOWN, ord("j")):
                    if selected == GRIPPER_JOINT:
                        target_q[GRIPPER_JOINT] = max(0.0, target_q[GRIPPER_JOINT] - step)
                    else:
                        target_q[selected] -= step
                elif key == ord("["):
                    step = max(step / 2.0, 0.001)
                elif key == ord("]"):
                    step = min(step * 2.0, 0.5)
                elif key == ord("g"):
                    gripper_open = not gripper_open
                    target_q[GRIPPER_JOINT] = GRIPPER_OPEN if gripper_open else GRIPPER_CLOSED
                elif key == ord("r"):
                    target_q = robot.get_joint_pos().copy().astype(np.float64)
                    gripper_open = target_q[GRIPPER_JOINT] > 0.4
                elif key == ord("0"):
                    target_q = np.zeros(7, dtype=np.float64)
                    target_q[GRIPPER_JOINT] = GRIPPER_OPEN
                    gripper_open = True
                elif key in (ord("q"), 27):
                    break

            robot.command_joint_pos(target_q)
            actual_q = robot.get_joint_pos().copy()
            draw(stdscr, target_q, actual_q, selected, step, args.channel)

            elapsed = time.monotonic() - t0
            remaining = dt - elapsed
            if remaining > 0:
                time.sleep(remaining)
    finally:
        robot.close()


def main():
    parser = argparse.ArgumentParser(description="Keyboard teleop for single YAM arm")
    parser.add_argument("--channel", default="can0", help="CAN interface (e.g. can0, can_follow_l)")
    parser.add_argument("--step", type=float, default=0.02, help="rad per key press (default 0.02)")
    parser.add_argument("--rate_hz", type=float, default=50.0, help="control loop rate (default 50)")
    args = parser.parse_args()

    curses.wrapper(run, args)


if __name__ == "__main__":
    main()
