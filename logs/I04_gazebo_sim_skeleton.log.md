---
step: I04
title: "Gazebo Harmonic Sim Skeleton"
agent_date: 2026-07-08
status: completed
previous_steps: [I00, I01, I02, I03]
---

# I04: Gazebo Harmonic Sim Skeleton

## Task

Created the smallest local `baxter_gz_sim` package needed to start Gazebo Harmonic and spawn Baxter from the I03 `baxter_bringup` model path. The package adds only `launch/sim.launch.py`; no custom world, ros2_control, controller YAML, MoveIt, examples, CI, docs, hardware, bridge, or compatibility scaffolding was added.

## Findings

- Added config-only `ament_cmake` package `src/baxter_gz_sim` with one launch file: `launch/sim.launch.py`.
- `sim.launch.py` launches Gazebo through `ros_gz_sim`'s `gz_sim.launch.py` with `gz_args` selected by `headless`:
  - `headless:=true`: `-r -s empty.sdf`
  - `headless:=false`: `-r empty.sdf`
- The launch includes the I03 model launch, `baxter_bringup/launch/baxter_description.launch.py`, and spawns Baxter with `ros_gz_sim create -topic /robot_description -name baxter`.
- While checking the spawn path, the imported `baxter_description/urdf/baxter.urdf.xacro` was found to include `gazebosim.urdf.xacro` unconditionally even when the existing `gazebo` xacro argument was `false`. That included deprecated `ignition::gazebo` plugin tags and camera/range sensors in the default model path. The include is now guarded by the existing `gazebo` argument, and I04 passes `gazebo:=false` to stay camera-less and avoid legacy plugin tags.

Build command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.27s]
Starting >>> baxter_description
Finished <<< baxter_description [0.23s]
Starting >>> baxter_bringup
Finished <<< baxter_bringup [0.16s]
Starting >>> baxter_gz_sim
Finished <<< baxter_gz_sim [0.16s]
Finished <<< baxter_maintenance_msgs [1.29s]
Finished <<< baxter_core_msgs [2.48s]

Summary: 6 packages finished [2.59s]
```

Generated model check after the Xacro guard:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3 - <<'PY'
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
import xacro

path = Path(get_package_share_directory('baxter_description')) / 'urdf' / 'baxter.urdf.xacro'
xml = xacro.process_file(str(path), mappings={'gazebo': 'false'}).toxml()
tokens = ['libignition', 'ignition::gazebo']
present = [token for token in tokens if token in xml]
print(f'robot_description_length={len(xml)}')
print(f'legacy_ignition_tokens_present={present}')
PY
robot_description_length=43120
legacy_ignition_tokens_present=[]
```

Gate command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && timeout 30s ros2 launch baxter_gz_sim sim.launch.py headless:=true
[INFO] [launch]: All log files can be found below /home/yunusdanabas/.ros/log/2026-07-08-17-25-51-621835-yunusdanabas-504036
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [gazebo-1]: process started with pid [504053]
[INFO] [robot_state_publisher-2]: process started with pid [504054]
[INFO] [create-3]: process started with pid [504056]
[robot_state_publisher-2] [INFO] [1783520752.511943749] [robot_state_publisher]: Robot initialized
[create-3] [INFO] [1783520752.525767961] [ros_gz_sim]: Requesting list of world names.
[create-3] [INFO] [1783520753.007446908] [ros_gz_sim]: Waiting messages on topic [/robot_description].
[create-3] [INFO] [1783520753.019101886] [ros_gz_sim]: Entity creation successful.
[INFO] [create-3]: process has finished cleanly [pid 504056]
[gazebo-1] [Err] [Physics.cc:1808] Attempting to create a mimic constraint for joint [l_gripper_r_finger_joint] but the chosen physics engine does not support mimic constraints, so no constraint will be created.
```

- Gate result: passed. Gazebo started, `robot_state_publisher` initialized, `ros_gz_sim create` read `/robot_description`, and Baxter entity creation succeeded.
- No missing mesh errors or Classic Gazebo plugin errors appeared in the gate output. The mimic-joint physics warning is not a mesh/plugin spawn failure.

## Decisions

- Kept `baxter_gz_sim` config-only and limited to a single launch file for I04.
- Used `ros_gz_sim` / `gz_args` naming only in the new launch path.
- Reused the I03 model launch instead of duplicating robot description construction.
- Used the built-in `empty.sdf`; no custom world file was added.
- Used CLI arguments for `ros_gz_sim create` (`-topic /robot_description -name baxter`) because that is the executable's advertised Jazzy interface.
- Guarded the imported legacy Gazebo Xacro include with the existing `gazebo` argument so default model launches remain free of deprecated `ignition::gazebo` plugins and camera/range sensors. Future sim overlays should add Harmonic/`gz_ros2_control` content explicitly instead of relying on `gazebosim.urdf.xacro`.

## Open Questions

- Gazebo reports that the selected physics engine does not support the Baxter gripper mimic constraint. This does not block I04, but later gripper simulation work should decide whether to ignore, remodel, or explicitly control gripper mimic behavior.
- Project license selection remains unresolved; local package `package.xml` files still use `TODO`.

## Artifacts

- `src/baxter_gz_sim/CMakeLists.txt`
- `src/baxter_gz_sim/package.xml`
- `src/baxter_gz_sim/launch/sim.launch.py`
- `src/baxter_common_ros2/baxter_description/urdf/baxter.urdf.xacro`
- `logs/I04_gazebo_sim_skeleton.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
