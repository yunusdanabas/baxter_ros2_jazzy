#!/usr/bin/env python3
"""Enable/disable Baxter's head sonar ring over the ROS 1 bridge.

The 12 transducers are a bitmask on /robot/sonar/head_sonar/set_sonars_enabled
(std_msgs/UInt16); /realtime_loop echoes the live value on .../sonars_enabled,
which is what this script reads back to confirm the change actually landed.

Runtime setting only — the robot resets to all-on when it reboots.

Usage (after `source scripts/baxter_env.sh`):
  python3 scripts/sonar_ctl.py status
  python3 scripts/sonar_ctl.py off
  python3 scripts/sonar_ctl.py on
"""

import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from py_bridge import ROS1Publisher, ROS1Subscriber, SlaveApi, detect_local_ip

ALL_ON = 0x0FFF  # 12 transducers
SET_TOPIC = "/robot/sonar/head_sonar/set_sonars_enabled"
STATE_TOPIC = "/robot/sonar/head_sonar/sonars_enabled"
# ponytail: fixed TCPROS port, fine for a one-shot CLI; make it ephemeral if
# you ever need two of these running at once.
PUB_PORT = 31600


def read_state(slave, master, timeout=15.0):
    got = {}
    ROS1Subscriber(master, STATE_TOPIC, "std_msgs/UInt16", "/sonar_ctl_read",
                   slave, lambda v: got.setdefault("v", v),
                   lambda d: struct.unpack("<H", d[:2])[0]).start()
    deadline = time.time() + timeout
    while time.time() < deadline and "v" not in got:
        time.sleep(0.2)
    return got.get("v")


def describe(v):
    if v is None:
        return "unknown (no message received)"
    return f"{v} (0x{v:04x}) — {bin(v).count('1')} of 12 transducers active"


def main():
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if action not in ("on", "off", "status"):
        sys.exit(f"usage: {sys.argv[0]} [on|off|status]")

    master = os.environ.get("ROS_MASTER_URI")
    if not master:
        sys.exit("ROS_MASTER_URI unset; run 'source scripts/baxter_env.sh' first")
    local_ip = os.environ.get("ROS_IP") or detect_local_ip(master)

    slave = SlaveApi(local_ip, master)
    current = read_state(slave, master)
    print(f"current: {describe(current)}")

    if action == "status":
        return

    target = ALL_ON if action == "on" else 0
    if current == target:
        print(f"already {action}, nothing to do")
        return

    pub = ROS1Publisher(master, SET_TOPIC, "std_msgs/UInt16", "/sonar_ctl",
                        slave, PUB_PORT, lambda v: struct.pack("<H", v))
    pub.start()
    time.sleep(3)  # let /realtime_loop negotiate TCPROS with us

    deadline = time.time() + 12
    while time.time() < deadline:
        pub.publish(target)
        if read_state(slave, master, timeout=1.0) == target:
            break
        time.sleep(0.5)

    time.sleep(1.0)
    final = read_state(slave, master)
    print(f"now:     {describe(final)}")
    if final != target:
        sys.exit(f"FAILED: wanted {target}, robot reports {final}")
    print(f"head sonar {action.upper()}")


if __name__ == "__main__":
    main()
