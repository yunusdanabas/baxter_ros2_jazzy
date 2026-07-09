# Compatibility Matrix

Statuses are based on I01-I09 gate evidence plus the I14 release-hardening baseline. Anything not listed as passed is not a support claim.

## Tested Profile

| Layer | Version/profile | Status | Evidence |
|---|---|---:|---|
| OS | Ubuntu 24.04 Noble | passed | Local and CI-equivalent checks in I08. |
| ROS 2 | Jazzy | passed | All build/check commands source `/opt/ros/jazzy/setup.bash`. |
| Gazebo | Harmonic via `ros-jazzy-ros-gz` | passed | I04 spawn, I05 controllers, I06 tiny trajectories. |
| ros2_control | Jazzy `gz_ros2_control` and controllers | passed | Active arm controllers and 14 arm joints in `/joint_states`. |
| MoveIt 2 | `ros-jazzy-moveit` | passed, manual/local smoke | I07 `/move_action` plus tiny left-arm plan+execute. |
| Source pin | ECN `678bfabea8c895b4134951a6c076217a90b9e0e6` | passed | I01/I08 SHA checks. |
| Devcontainer | `.devcontainer/Dockerfile` | passed | I08 image build and read-only mounted workspace build. |
| Default CI | GitHub Actions Ubuntu 24.04 | passed locally | I08 CI-equivalent build/import/model/MoveIt static checks. |

## Support Profiles

| Profile | Status | Notes |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, active arm controllers, `sim_tiny_trajectory`. |
| `sim_moveit` | passed, manual/local smoke | Planning/execution passed; full runtime remains manual/local. |
| `hardware_bridge` | blocked | I10 not run. |
| `hardware_motion` | blocked | I12 not run. |
| `experimental_zenoh` | deferred | Not in default install/devcontainer/CI. |

## Known Non-Blockers

| Item | Status |
|---|---|
| `move_group` missing `head_pan`, `l_gripper_l_finger_joint`, `r_gripper_l_finger_joint` from `/joint_states` | Non-blocking; only arm joints are controlled. |
| `No 3D sensor plugin(s) defined for octomap updates` | Non-blocking; no 3D sensors in first CI scope. |
| Possible `move_group` SIGINT teardown segfault | Non-blocking after successful execution; keeps full Gazebo+MoveIt runtime as manual/local smoke for now. |
| Full Gazebo+MoveIt runtime in CI | Deferred; manual/local smoke only until teardown stability is proven. |

## Not Tested

Hardware bridge, robot networking, ROS 1 bridge-host builds, grippers, cameras, Zenoh fallback, and supervised hardware motion have not passed gates.
