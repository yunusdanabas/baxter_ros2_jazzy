---
step: I08
title: "Devcontainer And Default CI"
agent_date: 2026-07-09
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07]
---

# I08: Devcontainer And Default CI

## Task

Added the default hardware-free devcontainer and the first GitHub Actions CI workflow for the sim-first workspace. The work stayed in tooling scope: no hardware bridge tooling, no ROS 1 dependencies, no Zenoh, no docs baseline, no grippers, no compatibility layer, and no optional examples.

## Findings

Added default devcontainer files:

- `.devcontainer/Dockerfile`: based on `ros:jazzy`, installs the standard Jazzy sim/MoveIt/tooling packages from `RESEARCH_FINDINGS.md` §5, including `ros-jazzy-desktop`, `ros-jazzy-ros-gz`, `ros-jazzy-gz-ros2-control`, `ros-jazzy-ros2-control`, `ros-jazzy-ros2-controllers`, `ros-jazzy-moveit`, `ros-jazzy-xacro`, `python3-colcon-common-extensions`, `python3-vcstool`, and `python3-rosdep`.
- `.devcontainer/devcontainer.json`: imports `repos/baxter_core.repos` only if `src/baxter_common_ros2` is absent, then runs `rosdep install` and the required build command with `--base-paths src` and `--packages-skip baxter_bridge`.
- `.devcontainer/README.md`: documents the default sim/MoveIt devcontainer boundary and explicitly excludes ROS 1, bridge-host, hardware, and Zenoh dependencies.
- `.dockerignore`: excludes `.git/`, `build/`, `install/`, `log/`, `.env`, and read-only `plan/` from Docker build context.

Added default CI workflow:

- `.github/workflows/ci.yml`: hardware-free workflow on Ubuntu 24.04.
- Installs ROS 2 Jazzy apt packages for the sim/MoveIt path only.
- Imports only `repos/baxter_core.repos` when needed and verifies the ECN checkout SHA is exactly `678bfabea8c895b4134951a6c076217a90b9e0e6`.
- Runs `rosdep install --from-paths src --ignore-src -r -y`.
- Builds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
- Sources `/opt/ros/jazzy/setup.bash` and `install/setup.bash` before post-build checks.
- Runs lightweight Python compile/import checks for local launch/example files.
- Runs Xacro/URDF load and static SRDF/MoveIt config checks.

Syntax/tooling checks:

```text
$ python3 -c "import yaml, json; yaml.safe_load(open('.github/workflows/ci.yml')); json.load(open('.devcontainer/devcontainer.json')); print('tooling_syntax=passed')"
tooling_syntax=passed
```

Local CI-equivalent command path passed. The first harness attempt used `set -u` and failed before project checks because ROS setup scripts reference unset `AMENT_TRACE_SETUP_FILES`; the check was rerun without nounset. Two complete rounds then passed against the final tooling state:

```text
$ source /opt/ros/jazzy/setup.bash
$ test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
$ rosdep install --from-paths src --ignore-src -r -y
#All required rosdeps installed successfully
$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 8 packages finished [3.15s]
$ source install/setup.bash
$ python3 -m compileall -q src/baxter_bringup src/baxter_gz_sim src/baxter_moveit_config src/baxter_examples
$ python3 # import local launch/example modules
python_import_checks=passed
$ ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro >/tmp/baxter_gz_control_round1.urdf
$ check_urdf /tmp/baxter_gz_control_round1.urdf
robot name is: baxter
---------- Successfully Parsed XML ---------------
$ python3 # static SRDF/MoveIt config checks
moveit_static_check=passed groups=['both_arms', 'left_arm', 'left_hand', 'right_arm', 'right_hand']

$ source /opt/ros/jazzy/setup.bash
$ test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
$ rosdep install --from-paths src --ignore-src -r -y
#All required rosdeps installed successfully
$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 8 packages finished [2.92s]
$ source install/setup.bash
$ python3 -m compileall -q src/baxter_bringup src/baxter_gz_sim src/baxter_moveit_config src/baxter_examples
$ python3 # import local launch/example modules
python_import_checks=passed
$ ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro >/tmp/baxter_gz_control_round2.urdf
$ check_urdf /tmp/baxter_gz_control_round2.urdf
robot name is: baxter
---------- Successfully Parsed XML ---------------
$ python3 # static SRDF/MoveIt config checks
moveit_static_check=passed groups=['both_arms', 'left_arm', 'left_hand', 'right_arm', 'right_hand']
```

Devcontainer gate evidence:

```text
$ docker build -f .devcontainer/Dockerfile -t baxter_ros2_jazzy-devcontainer .
#9 naming to docker.io/library/baxter_ros2_jazzy-devcontainer:latest done
#9 DONE 0.6s

$ docker run --rm -v "$PWD":/workspaces/baxter_ros2_jazzy:ro -w /workspaces/baxter_ros2_jazzy baxter_ros2_jazzy-devcontainer bash -lc 'source /opt/ros/jazzy/setup.bash && rosdep install --from-paths src --ignore-src -r -y && colcon --log-base /tmp/baxter_log build --base-paths src --symlink-install --packages-skip baxter_bridge --build-base /tmp/baxter_build --install-base /tmp/baxter_install && source /tmp/baxter_install/setup.bash && ros2 pkg prefix baxter_moveit_config'
#All required rosdeps installed successfully
Summary: 8 packages finished [1min 8s]
/tmp/baxter_install/baxter_moveit_config
```

During the first in-container check, auto-sourcing `/workspaces/baxter_ros2_jazzy/install/setup.bash` from `/etc/profile.d` printed stale host-install warnings when the workspace was mounted into the container. The devcontainer was fixed to source only `/opt/ros/jazzy/setup.bash` automatically; build/check commands explicitly source the workspace install after building.

Additional prior-step regression checks requested by the user:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash
$ python3 # I01/I02 pin, joints, mesh refs
i01_pin_check=passed sha=678bfabea8c895b4134951a6c076217a90b9e0e6
i02_model_check=passed joints=14/14 mesh_refs=31 missing_meshes=0
$ check_urdf /tmp/baxter_gz_control_round2.urdf
robot name is: baxter
---------- Successfully Parsed XML ---------------

$ python3 # I03 launch, robot_description, transient-local /tf_static subscriber
i03_bringup_check=passed robot_description_chars=51288 tf_static_transforms=37

$ python3 # I04-I07 combined sim/runtime regression in ROS_DOMAIN_ID=88
i04_i05_sim_controller_check=passed
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active
i05_joint_states_check=passed joints=14/14
i06_tiny_trajectory_check=passed
i07_move_action_check=passed
i07_moveit_tiny_execution_check=passed
```

Gate result: passed. The clean devcontainer image/build path and CI-equivalent local commands pass without hardware, ROS 1, bridge build, or Zenoh.

## Decisions

- Kept default CI hardware-free and static/model-focused. Full Gazebo+MoveIt runtime was not made a default CI gate because I07 documented successful execution followed by possible SIGINT teardown segfaults; it remains suitable for manual/local smoke until CI runner stability is proven.
- Used Python compile/import checks instead of adding ament lint/test dependencies or a new smoke-test package. This is enough for first CI and avoids scaffolding.
- Verified the pinned ECN SHA in CI and local checks instead of trusting the `.repos` file alone.
- Did not add ROS 1, `baxter_legacy`, bridge-host setup, Zenoh, Docker host networking assumptions, broad camera checks, gripper controllers, action shims, or compatibility packages.
- Removed devcontainer workspace auto-source because mounted host installs can contain absolute paths invalid inside the container. Commands still explicitly source `install/setup.bash` after build, as required.

## Open Questions

- Whether headless Gazebo+MoveIt execution should become a required CI gate remains deferred until the chosen CI runner proves teardown stability.
- Project license selection remains unresolved; existing local package manifests still use `TODO`.

## Artifacts

- `.dockerignore`
- `.devcontainer/Dockerfile`
- `.devcontainer/devcontainer.json`
- `.devcontainer/README.md`
- `.github/workflows/ci.yml`
- `logs/I08_devcontainer_ci.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
