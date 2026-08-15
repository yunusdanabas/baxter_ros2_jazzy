---
step: I10
title: "Hardware Bridge Non-Motion Gate"
agent_date: 2026-07-22
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I14, I15]
---

# I10: Hardware Bridge Non-Motion Gate

First session against the physical robot. Gate **PASSED**. No enable, no
motion.

## Network Reality vs. Repo Assumptions

The repo's hardcoded `192.168.1.224` was wrong and cost the first part of the
session. Actual topology:

| Item | Value |
|---|---|
| Robot mDNS name | `011412P0024.local` (from `plan/baxter_noetic_ref/baxter/baxter.sh`) |
| Robot IP this session | `192.168.1.232` (DHCP lease — **moves**) |
| Robot IP while booting | `169.254.8.12` (link-local, before DHCP succeeded) |
| Laptop iface | `enp4s0` |
| Laptop IP | `192.168.1.252` (DHCP) |

Two distinct failures, in order:

1. **No carrier.** `enp4s0` was down; the robot was also still booting and
   had self-assigned a link-local address. Nothing was reachable.
2. **Wrong subnet.** Once the link came up, `enp4s0` had a stale manual
   `192.168.2.100/24` (NetworkManager `ipv4.method: manual`) while the robot
   was on `192.168.1.0/24`. The kernel therefore routed robot traffic out the
   **WiFi default gateway**, where it was silently dropped. Fixed by
   switching the profile to DHCP:
   `nmcli connection modify "Wired connection 1" ipv4.method auto && nmcli connection up "Wired connection 1"`.

The diagnostic that actually localises this class of failure is
`ip route get <robot-ip>` — it must report `dev enp4s0`, not `via <gw> dev
wlp0s20f3`. Added to the runbook.

## Bug Found And Fixed: JointState Header Misparse

`deser_joint_state()` in `scripts/py_bridge.py` treated the message as
starting with `time stamp`. Real ROS 1 `std_msgs/Header` is:

```
uint32 seq        <- ROS 2 dropped this; we were not skipping it
time   stamp
string frame_id   <- we were not reading this either
```

Every field after the header was therefore misaligned, producing:

```
ROS1 sub /robot/joint_states deserialize failed: unpack_from requires a
buffer of at least 1600414098 bytes ... (actual buffer size is 637)
```

Fixed by skipping `seq` and reading `frame_id`. After the fix: 0 deserialize
errors, joint names parse correctly.

**Why I10-prep2's loopback test missed it:** that test used
`std_msgs/Float64`, which has no `Header`. It validated the *negotiation*
layer (its actual purpose) but could not exercise header parsing. A
header-bearing message type would be needed to catch this hardware-free.

## Gate Evidence

```text
$ python3 scripts/i10_non_motion_check.py 192.168.1.232
  OK: master alive. 202 publishers, 123 subscribers, 89 services
  OK: 271 topics advertised
  OK: /robot/state (baxter_core_msgs/AssemblyState)
  OK: /robot/joint_states (sensor_msgs/JointState)
  OK: both IK services, /cameras/{list,open,close}
  OK: /robot/joint_states has 2 publisher(s): ['/realtime_loop', '/end_effector_publisher']
GATE: PASS (0 warnings)
```

Live data through the fixed bridge:

```text
$ ros2 topic hz /robot/joint_states
average rate: 100.008   min: 0.009s max: 0.011s std dev: 0.00027s

$ ros2 topic echo --once /robot/joint_states --field name
['head_nod','head_pan','left_e0','left_e1','left_s0','left_s1','left_w0',
 'left_w1','left_w2','right_e0','right_e1','right_s0','right_s1','right_w0',
 'right_w1','right_w2','torso_t0']            # 17 joints

$ ros2 run baxter_hardware_bridge baxter_safety_check
safe_for_motion=False  ready=False enabled=False stopped=False error=False
                       estop_button=0 estop_source=0
```

`safe_for_motion=False` is **correct** — the robot is disabled, so the shims
will refuse motion goals. Enabling is an I12 step and was not done.

Both bridge directions are now proven on real hardware: the subscribe path by
the 100 Hz joint stream, and the publish path by the sonar change below
(`/realtime_loop` connected to our publisher via the `requestTopic` handler
added in I10-prep2).

## Head Sonar Disabled (user request)

Control is a 12-bit mask on `/robot/sonar/head_sonar/set_sonars_enabled`
(`std_msgs/UInt16`), echoed live on `.../sonars_enabled`. Added
`scripts/sonar_ctl.py` (`on` / `off` / `status`), which reads back the robot's
own feedback topic to confirm the write landed. Verified round-trip:
`4095 -> 0 -> 4095 -> 0`. **Left OFF.**

Runtime setting only — resets to all-on at robot reboot. Disabling removes
proximity/approach sensing; e-stop and supervision remain the safety controls.

## Config Fixes

- `scripts/baxter_env.sh`: address the robot by mDNS hostname (lease moves);
  derive `ROS_IP` from `ip route get <robot>` instead of
  `hostname -I | awk '{print $1}'`. The old form returned the stale
  `192.168.2.100`, an address the robot could not reach — ROS 1 would have
  advertised an unreachable callback URI.
- `scripts/py_bridge.py`: `--master` / `--ip` now default to
  `$ROS_MASTER_URI` / `$ROS_IP`; no IP hardcoded anywhere.
- `docs/hardware_runbook.md`: network setup section, route check, sonar
  procedure; stale `192.168.1.224` removed.

## Next

I11 (action shim gate on hardware) is unblocked. It needs the shims launched
and a bad-joint-name rejection test — still no motion. I12 additionally
requires enabling the robot from the robot side over SSH, a clear workspace,
and a reachable e-stop.

## Artifacts

- `scripts/py_bridge.py` (JointState header fix, env-based defaults)
- `scripts/baxter_env.sh` (hostname + route-derived ROS_IP)
- `scripts/sonar_ctl.py` (new)
- `docs/hardware_runbook.md`
- `logs/I10_hardware_bridge_non_motion.log.md` (this file)
