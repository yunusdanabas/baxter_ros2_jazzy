"""N2: in-flight tracking lag from the I12 motion bag.

path_tolerance_rad compares the command actually published against the measured
position *during* motion. The 0.0078 rad figure in the log came from the client's
max_error, which is measured after the arm settles -- a different, smaller
quantity. This computes the real one.

Runs inside the Noetic container: genuine rosbag + baxter_core_msgs definitions,
so no msgdef parsing and no new host dependency.

Usage (from the repo root):
  docker run --rm -v "$PWD/data/sessions/<date>/ros1:/data:ro" \
    -v "$PWD/scripts/analyze_tracking_lag.py:/tmp/a.py:ro" baxter-noetic:n07 \
    bash -lc "source /root/baxter_ws/install/setup.bash && python3 /tmp/a.py /data/<bag>"

It reads |ref_joint_states - joint_states| rather than the joint_command payload,
because the I12 bag was recorded while the bridge advertised md5sum "*" with an
empty message definition, so *that* bag's joint_command messages cannot be
deserialised (logs/I18_hardware_day.log.md F23). Their timestamps still delimit
goal windows, which is all this needs them for.

F23 is fixed: py_bridge now sends the real md5sum and message definition, and a
bag recorded through it decodes (verified against rosbag in the Noetic image).
Any capture from here on can be measured as |command - measured| directly --
that rewrite is waiting on a fresh capture, since re-running it against the old
bag would still hit the empty schema.
"""
from __future__ import print_function
import sys
import rosbag

BAG = sys.argv[1]
ARMS = ("left", "right")
JOINTS = ("s0", "s1", "e0", "e1", "w0", "w1", "w2")
IDLE_GAP = 0.5      # s without a command => not executing a goal


def pct(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = int(round((len(sorted_vals) - 1) * p))
    return sorted_vals[k]


cmds = {a: [] for a in ARMS}      # (t, {joint: pos})
meas = []                          # (t, {joint: pos})
refs = []                          # (t, {joint: pos})

topics = ["/robot/joint_states", "/robot/ref_joint_states"]
topics += ["/robot/limb/%s/joint_command" % a for a in ARMS]

with rosbag.Bag(BAG) as bag:
    info = bag.get_type_and_topic_info()[1]
    print("=== bag contents ===")
    for t in sorted(info):
        print("  %-45s %7d msgs  %s" % (t, info[t].message_count, info[t].msg_type))
    print()
    for topic, msg, t in bag.read_messages(topics=topics):
        ts = t.to_sec()
        if topic.endswith("joint_command"):
            arm = topic.split("/")[3]
            cmds[arm].append((ts, None))
        elif topic == "/robot/joint_states":
            meas.append((ts, dict(zip(msg.name, msg.position))))
        else:
            refs.append((ts, dict(zip(msg.name, msg.position))))

print("=== command stream ===")
for a in ARMS:
    print("  %-5s %6d joint_command msgs" % (a, len(cmds[a])))
print("  %6d joint_states, %6d ref_joint_states" % (len(meas), len(refs)))
print()

for arm in ARMS:
    stream = cmds[arm]
    if not stream:
        print("=== %s arm: no commands recorded ===" % arm)
        continue

    # Split the command stream into goal windows.
    windows = []
    start = prev = stream[0][0]
    for ts, _ in stream[1:]:
        if ts - prev > IDLE_GAP:
            windows.append((start, prev))
            start = ts
        prev = ts
    windows.append((start, prev))

    per_joint_max = {j: 0.0 for j in JOINTS}
    all_lags = []
    ri = 0
    for ts, mpos in meas:
        if not any(w0 <= ts <= w1 for w0, w1 in windows):
            continue                      # only while a goal is executing
        while ri + 1 < len(refs) and refs[ri + 1][0] <= ts:
            ri += 1
        cpos = refs[ri][1]
        for j in JOINTS:
            key = "%s_%s" % (arm, j)
            if key in cpos and key in mpos:
                lag = abs(cpos[key] - mpos[key])
                all_lags.append(lag)
                if lag > per_joint_max[j]:
                    per_joint_max[j] = lag

    all_lags.sort()
    print("=== %s arm: in-flight lag |ref_joint_states - measured| ===" % arm)
    print("  goal windows: %d, total %.1f s, %d samples"
          % (len(windows), sum(b - a for a, b in windows), len(all_lags)))
    if all_lags:
        print("  p50=%.4f  p95=%.4f  p99=%.4f  MAX=%.4f rad"
              % (pct(all_lags, .50), pct(all_lags, .95),
                 pct(all_lags, .99), all_lags[-1]))
        worst = sorted(per_joint_max.items(), key=lambda kv: -kv[1])
        print("  worst joints: " + ", ".join("%s=%.4f" % (j, v) for j, v in worst[:4]))
    print()

# The robot's own reference vs measured -- its internal tracking, independent of us.
if refs:
    rlags = []
    ri = 0
    for ts, mpos in meas:
        while ri + 1 < len(refs) and refs[ri + 1][0] <= ts:
            ri += 1
        rpos = refs[ri][1]
        for arm in ARMS:
            for j in JOINTS:
                key = "%s_%s" % (arm, j)
                if key in rpos and key in mpos:
                    rlags.append(abs(rpos[key] - mpos[key]))
    rlags.sort()
    print("=== robot-internal: |ref_joint_states - joint_states| (all samples) ===")
    print("  p50=%.4f  p95=%.4f  MAX=%.4f rad" % (pct(rlags, .50), pct(rlags, .95), rlags[-1]))
