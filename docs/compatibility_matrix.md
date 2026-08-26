# Compatibility Matrix

Statuses are based on I01-I09, I14, and I15 gate evidence. Anything not listed as passed is not a support claim.

## Tested Profile

| Layer | Version/profile | Status | Evidence |
|---|---|---:|---|
| OS | Ubuntu 24.04 Noble | passed | Local and CI-equivalent checks in I08. |
| ROS 2 | Jazzy | passed | All build/check commands source `/opt/ros/jazzy/setup.bash`. |
| Gazebo | Harmonic via `ros-jazzy-ros-gz` | passed | Fixed pedestal, numeric/GUI reversible arm motion. |
| ros2_control | Jazzy `gz_ros2_control` and controllers | passed | 14 commanded arm joints, 17 independent states, enforced limits. |
| MoveIt 2 | `2.12.4` from `ros-jazzy-moveit` | passed, manual/local smoke | OMPL plus reversible left/right/both-arm checks; local shutdown workaround for `moveit/moveit2#3721`. |
| Source pin | ECN `678bfabea8c895b4134951a6c076217a90b9e0e6` | passed | I01/I08 SHA checks. |
| Devcontainer | `.devcontainer/Dockerfile` | passed | I08 image build and read-only mounted workspace build. |
| Default CI | GitHub Actions Ubuntu 24.04 | passed locally | I08 CI-equivalent build/import/model/MoveIt static checks. |

## Support Profiles

| Profile | Status | Notes |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, active arm controllers, `sim_tiny_trajectory`. |
| `sim_rviz` | passed, manual/local GUI | Complete RobotModel/TF and live arm-state display. |
| `sim_moveit` | passed, manual/local smoke | Readiness-gated OMPL planning and execution. |
| `sim_moveit_rviz` | passed, manual/local GUI | MotionPlanning on `both_arms`, OMPL planner list, and a 6-DOF marker on each gripper. |
| `hardware_bridge` | experimental | Mock/action-shim code exists; real-robot operation is unvalidated on `main`. |
| `hardware_motion` | unsupported | No support claim. |
| `experimental_zenoh` | deferred | Not in default install/devcontainer/CI. |

## Scoped Limitations

| Item | Status |
|---|---|
| Gripper mimic physics | State/TF only; DART mimic contact fidelity and gripper commands are unsupported. |
| `No 3D sensor plugin(s) defined for octomap updates` | Expected only for empty-world/explicit-scene operation; sensed-obstacle support is not claimed. |
| Visual-only sensor/display links | Their exact geometry is not part of collision checking. |
| Full Gazebo+MoveIt runtime in CI | Manual/local because default CI remains hardware-free and static. |

## Not Tested

Robot networking, ROS 1 bridge-host builds, gripper commands, cameras, tuck/untuck,
Zenoh fallback, and supervised hardware motion are not supported by `main`.
