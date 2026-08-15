---
step: I10-prep2
title: "py_bridge.py ROS 1 Negotiation Fix and Loopback Proof"
agent_date: 2026-07-22
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09, I10-prep, I14, I15]
---

# I10-prep2: py_bridge.py ROS 1 Negotiation Fix and Loopback Proof

## Task

Prepare the workspace for an upcoming real-Baxter session (robot currently
off, will connect on the lab network at `192.168.1.224` later). I10-prep
(previous step) built and dry-run tested the `baxter_hardware_bridge` action
shims against a mock — it never exercised `scripts/py_bridge.py` against a
real ROS 1 master. Auditing that script surfaced a bug that would have
blocked the very first lab session.

## Findings

`scripts/py_bridge.py` skipped the ROS 1 Slave API (XML-RPC) negotiation
step in both directions:

1. **Subscribe path (ROS1->ROS2)**: `ROS1Subscriber._connect_and_receive()`
   took the URIs returned by `registerSubscriber` — which are publishers'
   **XML-RPC** Slave API URIs, not TCPROS addresses — and opened a raw
   TCPROS socket directly to that port. A real publisher's XML-RPC port
   doesn't speak TCPROS, so the handshake would hang/fail against any real
   `roscore`/`rospy` publisher.
2. **Publish path (ROS2->ROS1, the motion-command path)**:
   `ROS1Publisher.start()` registered its own raw TCPROS listener port as if
   it were the node's Slave API URI. A real ROS 1 subscriber calls
   `requestTopic` (XML-RPC) on that URI to learn where to connect — but our
   listener only spoke raw TCPROS, not XML-RPC, so it could never answer and
   the robot-side subscriber would never connect. `/robot/limb/*/joint_command`
   would have silently gone nowhere.

Both bugs were invisible in I10-prep because that work only exercised the
`baxter_hardware_bridge` action-shim package against `mock_robot.py`
(ROS 2-native), never `py_bridge.py` against genuine ROS 1.

## Fix

Added a minimal `SlaveApi` class (stdlib `xmlrpc.server.SimpleXMLRPCServer`,
~35 lines) implementing `requestTopic`, `publisherUpdate`, `getPid`,
`getMasterUri` — the Slave API surface real ROS 1 nodes expect. One shared
instance is used as the `caller_api` for every `registerPublisher`/
`registerSubscriber` call:

- `ROS1Publisher.start()` now registers its TCPROS port with the shared
  `SlaveApi` (`register_publisher_port`) before announcing itself to the
  master, so `requestTopic` calls resolve correctly.
- `ROS1Subscriber._connect_and_receive()` now calls `requestTopic` on the
  publisher's XML-RPC URI to get the real TCPROS host/port before
  connecting, instead of connecting to the XML-RPC port directly.

No new dependencies — `xmlrpc.server` is stdlib.

## Loopback Test (hardware-free proof)

Real `roscore`/`rostopic` from the existing `baxter-noetic:audit` Docker
image, `--network host`, tested against genuine rospy (not a mock):

```text
$ bash scripts/test_bridge_loopback.sh
=== Starting roscore in baxter_loopback_test ===
=== Publishing /loopback_test/from_ros1 from genuine rostopic ===
=== Running py_bridge negotiation (host side) ===
PASS: ROS1->bridge received 3.14
PASS: bridge->ROS1 publish loop done
=== rostopic echo captured ===
data: 2.71828
---
=== OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy) ===
```

Tested with `std_msgs/Float64` rather than Baxter-specific message types —
this is a protocol-negotiation test (Slave API / TCPROS handshake), not a
message-serialization test. `baxter_core_msgs` isn't built for ROS 1 Noetic
in the audit image and doesn't need to be: the (de)serializers in
`py_bridge.py` are unchanged and already covered indirectly by
`baxter_hardware_bridge`'s dry-run test on the ROS 2 side.

## Regression Check

```text
$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 9 packages finished [5.84s]

$ ros2 run baxter_hardware_bridge dry_run_test
PASS: Test 1 goal succeeded
PASS: Test 2 bad joints rejected
PASS: Test 3 unsafe state rejected
OVERALL: PASS
```

## Other Changes

- `scripts/baxter_env.sh`: removed `export ROS_DOMAIN_ID=42` (standing rule:
  no ROS domain isolation on this single-user machine — a stray unset
  terminal would silently lose all bridge traffic) and added
  `export LC_NUMERIC=C` (known trap: `tr_TR` locale silently turns double
  params into strings in Qt/ROS tools).
- `docs/hardware_runbook.md`: added a pre-lab check section pointing at
  `scripts/test_bridge_loopback.sh` and the dry-run regression test; added
  explicit SSH-based `enable_robot.py`/`tuck_arms.py` steps before/after I12
  motion (robot-side, never from the laptop, never via
  `/robot/set_super_enable`).

## Open Questions

- I10 remains blocked on physical Baxter access only — the bridge itself is
  now proven against real ROS 1 protocol behavior, not just a mock.
- If the real robot's TCPROS header exchange rejects `md5sum: "*"` (some
  strict roscpp publishers do), hardcode the real md5sums from
  `plan/baxter_noetic_ref/baxter_common/baxter_core_msgs/msg/` — not
  observed in this test, but noted as the first thing to check if I10's
  non-motion gate fails on message delivery.

## Artifacts

- `scripts/py_bridge.py` (fixed)
- `scripts/test_bridge_loopback.sh` (new)
- `scripts/baxter_env.sh` (cleanup)
- `docs/hardware_runbook.md` (pre-lab check + SSH enable/tuck notes)
- `logs/I10_prep2_py_bridge_loopback.log.md` (this file)
