---
step: S03
title: "Local Repo Detailed Analysis"
agent_date: 2026-06-17
status: completed
previous_steps: [S01, S02]
---

# S03: Local Repo Detailed Analysis

## Task

Performed a read-only analysis of the local ROS 1 Noetic Baxter reference repository at `baxter_noetic_ref/`. Extracted the package graph, custom message/service surface, topics, services, actions, parameters, launch files, scripts, hidden dependencies, and package-by-package preserve/replace/simplify/drop decisions for the ROS 2 Jazzy migration blueprint.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `MASTER_PLAN.md`

The Noetic reference repository was inspected only as source material and was not modified.

## Findings

### Executive Summary

The local Noetic API is centered on a stable `/robot/*` topic/service/action surface. The ROS 2 blueprint should preserve this surface for real-hardware bridging where it affects student workflows, but should not line-by-line port the Classic Gazebo simulator or every SDK example.

| Area | Finding | Planning Impact |
|---|---|---|
| Package count | Confirmed 17 `package.xml` files under `baxter_noetic_ref/`. | S08 should map exactly these 17 packages. |
| Custom interfaces | `baxter_core_msgs` has 26 `.msg` and 6 `.srv`; `baxter_maintenance_msgs` has 7 `.msg`; no custom `.action` files. | Adopt/port message packages through `baxter_common_ros2`; bridge must know these types. |
| Student API | `baxter_interface` exposes `Limb`, `Gripper`, `Head`, `CameraController`, `RobotEnable`, `DigitalIO`, `AnalogIO`, `Navigator`, plus action servers. | Preserve core behavior, but a thin ROS 2 facade can be smaller than the ROS 1 package. |
| Actions | No custom actions; uses `control_msgs/FollowJointTrajectory`, `control_msgs/GripperCommand`, and `control_msgs/SingleJointPosition`. | S04 must decide action bridging or ROS 2-side action shim. |
| Simulation | C++ is isolated in `baxter_simulator/*` and depends on Gazebo Classic, `gazebo_ros_control`, ROS 1 `controller_interface`, `hardware_interface`, `effort_controllers`, Qt, KDL, OpenCV. | Replace with Gazebo Harmonic + `ros2_control`; do not port Classic plugins. |
| MoveIt | `baxter_moveit_config` is MoveIt 1 config with Baxter controller action names. | Regenerate MoveIt 2 config, preserving groups/joint names/controller intent. |
| Networking | `baxter/baxter.sh` hardcodes ROS 1 shell model: `ROS_MASTER_URI`, `ROS_IP`/`ROS_HOSTNAME`, robot hostname, `devel/setup.bash`. | Replace with bridge/devcontainer/networking docs, not a direct port. |

### Package Inventory And Dependencies

All package manifests use Catkin. Python packages use `catkin_python_setup()` where noted; C++ simulator packages use Catkin CMake targets.

| Package | Path | Build Type | Manifest/CMake Dependencies | Decision | Effort | Reason |
|---|---|---|---|---|---|---|
| `baxter_common` | `baxter_common/baxter_common` | Catkin metapackage | Runtime deps: `baxter_description`, `baxter_core_msgs`, `baxter_maintenance_msgs`, `rethink_ee_description`, `roscpp`; manifest marks `<metapackage/>` at `package.xml:32-34`. | Preserve via community ROS 2 common | Low | Metadata only; ECN common covers this role. |
| `baxter_core_msgs` | `baxter_common/baxter_core_msgs` | Catkin messages/services | `message_generation`, `message_runtime`, `geometry_msgs`, `sensor_msgs`, `std_msgs`; manifest lines `25-33`; CMake adds messages/services and generates interfaces. | Preserve | Low | Bridge-critical API, already available in S02 ECN `baxter_common_ros2`. |
| `baxter_description` | `baxter_common/baxter_description` | Catkin data package | Runtime `rethink_ee_description`; manifest lines `23-25`; URDF/Xacro/meshes. | Preserve geometry, replace Classic Gazebo tags | Medium | Robot model needed, but `baxter_base.gazebo.xacro` uses Classic plugins. |
| `baxter_maintenance_msgs` | `baxter_common/baxter_maintenance_msgs` | Catkin messages | `message_generation`, `message_runtime`, `std_msgs`; manifest lines `25-29`. | Simplify or drop most | Low | Tare/update/calibration messages are not minimum student workflow. |
| `rethink_ee_description` | `baxter_common/rethink_ee_description` | Catkin data package | Catkin only; manifest lines `21-23`; electric/null/pneumatic gripper URDFs. | Preserve/simplify | Low | End-effector geometry matters; Classic `EffortJointInterface` tags need ROS 2 review. |
| `baxter_sdk` | `baxter/baxter_sdk` | Catkin metapackage + shell setup | Runtime deps: `baxter_interface`, `baxter_examples`, `baxter_tools`, `baxter_common`; manifest lines `25-31`; `baxter.sh` manages ROS 1 env. | Replace | Low | Use ROS 2 workspace/devcontainer docs instead of ROS 1 shell wrapper. |
| `baxter_interface` | `baxter_interface` | Catkin Python package + dynamic reconfigure | `rospy`, `actionlib`, `baxter_core_msgs`, `control_msgs`, `dynamic_reconfigure`, `sensor_msgs`, `std_msgs`, `trajectory_msgs`, `diagnostic_msgs`; manifest lines `25-42`; setup packages in `setup.py:5-8`. | Preserve core behavior | High | Main SDK API and action shims; action/parameter semantics need design. |
| `baxter_tools` | `baxter_tools` | Catkin Python scripts | `rospy`, `sensor_msgs`, `geometry_msgs`, `cv_bridge`, `baxter_interface`, `baxter_core_msgs`, `baxter_maintenance_msgs`; manifest lines `25-39`; scripts installed by `CMakeLists.txt:29-38`. | Simplify | Medium | Keep enable/tuck/camera/smoke-test subset; drop maintenance unless lab requires it. |
| `baxter_examples` | `baxter_examples` | Catkin Python package + dynamic reconfigure | `rospy`, `xacro`, `actionlib`, `sensor_msgs`, `control_msgs`, `trajectory_msgs`, `cv_bridge`, `dynamic_reconfigure`, `baxter_core_msgs`, `baxter_interface`; manifest lines `24-44`; `JointSpringsExample.cfg`. | Simplify | Medium | Rewrite curated examples in ROS 2; many scripts are stale or overly broad. |
| `baxter_moveit_config` | `baxter_moveit_config` | Catkin config package | MoveIt 1 deps: `moveit_ros_move_group`, `moveit_planners_ompl`, `moveit_ros_visualization`, `joint_state_publisher`, `robot_state_publisher`, `xacro`, `moveit_simple_controller_manager`, `baxter_description`; manifest lines `17-30`. | Replace with MoveIt 2 | Medium | Preserve groups/controllers as reference, regenerate for Jazzy. |
| `baxter_simulator` | `baxter_simulator/baxter_simulator` | Catkin metapackage | Runtime deps all simulator packages; manifest lines `23-31`. | Drop/replace | Low | Metapackage for Classic simulator only. |
| `baxter_gazebo` | `baxter_simulator/baxter_gazebo` | Catkin C++ plugin + launch | `roscpp`, `baxter_core_msgs`, `gazebo_ros_control`, `controller_manager_msgs`, `tf2_ros`, `gazebo_ros`, `baxter_description`, `baxter_sim_hardware`; manifest lines `25-40`; builds `baxter_gazebo_ros_control` in CMake. | Replace | High | Gazebo Classic plugin path, not Harmonic-compatible. |
| `baxter_sim_controllers` | `baxter_simulator/baxter_sim_controllers` | Catkin C++ controller plugins | `controller_interface`, `control_toolbox`, `effort_controllers`, `baxter_core_msgs`, `yaml-cpp`; manifest lines `25-38`; exports five `ControllerBase` plugins. | Replace | High | ROS 1 controller API and `EffortJointInterface` plugins. |
| `baxter_sim_examples` | `baxter_simulator/baxter_sim_examples` | Catkin Python scripts/models | `rospy`, `rospack`, `baxter_core_msgs`, `baxter_gazebo`, `baxter_interface`, `baxter_tools`, `gazebo_ros`, `gazebo_msgs`; manifest lines `23-43`. | Replace/simplify | Medium | Classic Gazebo pick-place demos; use Harmonic/MoveIt 2 examples. |
| `baxter_sim_hardware` | `baxter_simulator/baxter_sim_hardware` | Catkin C++ emulator | `std_msgs`, `tf`, `roscpp`, `baxter_core_msgs`, `cv_bridge`, `image_transport`, `baxter_sim_kinematics`, `cmake_modules`, `libopencv-dev`, `controller_manager`, `robot_state_publisher`; manifest lines `28-49`; builds `baxter_emulator`. | Replace | High | Fake hardware and state emulator for Classic/ROS 1 controller stack. |
| `baxter_sim_io` | `baxter_simulator/baxter_sim_io` | Catkin C++ Qt GUI node | `roscpp`, `baxter_core_msgs`; Qt build remnants in CMake; publishes navigator/digital IO. | Drop or optional later | Medium | Not required for minimum sim/hardware workflow. |
| `baxter_sim_kinematics` | `baxter_simulator/baxter_sim_kinematics` | Catkin C++ library/node | `baxter_core_msgs`, `gazebo_msgs`, `sensor_msgs`, `kdl_parser`, `tf`, `tf_conversions`, `roscpp`; manifest lines `24-42`; builds library and `kinematics` executable. | Replace | Medium | Use MoveIt 2 IK in sim; bridge real IK service if needed. |

### Custom Messages And Services

#### `baxter_core_msgs`

Messages from `baxter_common/baxter_core_msgs/msg/`:

| Message | Fields Summary | Preserve Priority |
|---|---|---|
| `AnalogIOState` | `time timestamp`, `float64 value`, `bool isInputOnly`; lines `1-3`. | Medium |
| `AnalogIOStates` | arrays of names and `AnalogIOState`; lines `1-2`. | Low |
| `AnalogOutputCommand` | output `name`, `uint16 value`; lines `1-4`. | Low |
| `AssemblyState` | `ready`, `enabled`, `stopped`, `error`, `estop_button`, `estop_source`; lines `1-18`. | High |
| `AssemblyStates` | arrays of names and `AssemblyState`; lines `1-2`. | Low |
| `BridgePublisher` | topic/user/time for bridge arbitration; lines `1-3`. | High for ECN-style bridge |
| `CameraControl` | camera control ID/value plus exposure/gain/white-balance/window/flip/mirror/half-res constants; lines `1-13`. | High for camera tools |
| `CameraSettings` | width, height, fps, `CameraControl[]`; lines `1-4`. | High for camera tools |
| `CollisionAvoidanceState` | header, `other_arm`, collision object names; lines `1-3`. | Medium for tuck |
| `CollisionDetectionState` | header, `collision_state`; lines `1-2`. | Medium |
| `DigitalIOState` | state, `isInputOnly`, ON/OFF/PRESSED constants; lines `1-7`. | Medium |
| `DigitalIOStates` | arrays of names and `DigitalIOState`; lines `1-2`. | Low |
| `DigitalOutputCommand` | output `name`, bool `value`; lines `1-4`. | Medium |
| `EndEffectorCommand` | gripper/end-effector `id`, command string, JSON args, sender, sequence; lines `1-21`. | High |
| `EndEffectorProperties` | gripper type, identity, firmware, capability booleans, JSON properties; lines `1-27`. | High |
| `EndEffectorState` | timestamp/id, tristate flags, position/force, JSON state, last command sender/sequence; lines `1-34`. | High |
| `EndpointState` | header, pose, twist, wrench; lines `1-4`. | High |
| `EndpointStates` | arrays of names and `EndpointState`; lines `1-2`. | Low |
| `HeadPanCommand` | target, speed ratio, pan enable request constants; lines `1-12`. | High for head tools |
| `HeadState` | pan, turning/nodding/pan-enabled booleans; lines `1-4`. | Medium |
| `JointCommand` | mode, command values, names, `POSITION_MODE`, `VELOCITY_MODE`, `TORQUE_MODE`, `RAW_POSITION_MODE`; lines `1-8`. | High |
| `NavigatorState` | button names/states, wheel, light names/states; lines `1-11`. | Low/medium |
| `NavigatorStates` | arrays of names and `NavigatorState`; lines `1-3`. | Low |
| `RobustControllerStatus` | enable/completion state, control UID, timeout flag, errors, labels; lines `1-29`. | Low unless maintenance preserved |
| `SEAJointState` | commanded/actual joint arrays plus gravity/hysteresis/crosstalk efforts; lines `21-40`. | Medium for diagnostics/sim |
| `URDFConfiguration` | timestamp, parent link, joint, URDF fragment; lines `1-10`. | Low |

Services from `baxter_common/baxter_core_msgs/srv/`:

| Service | Fields Summary | Preserve Priority |
|---|---|---|
| `SolvePositionIK` | request: `PoseStamped[]`, optional seed `JointState[]`, seed mode; response: solution `JointState[]`, `isValid[]`, `result_type[]`; lines `1-29`. | High for hardware compatibility |
| `ListCameras` | response `string[] cameras`; lines `1-2`. | High for camera tools |
| `OpenCamera` | request name + `CameraSettings`, response err; lines `1-4`. | High for camera tools |
| `CloseCamera` | request name, response err; lines `1-3`. | High for camera tools |
| `BridgePublishersAuth` | topic/user request; response current publishers and forced left/right users; lines `1-6`. | High if ECN bridge chosen |
| `BridgePublishersForce` | force left/right bridge users; lines `1-3`. | High if ECN bridge chosen |

#### `baxter_maintenance_msgs`

Messages from `baxter_common/baxter_maintenance_msgs/msg/`:

| Message | Fields Summary | Preserve Priority |
|---|---|---|
| `UpdateStatus` | status/progress/long description plus update state constants; lines `5-19`. | Drop or hardware-admin only |
| `UpdateSource` | device, filename, version, uuid; lines `1-4`. | Drop or hardware-admin only |
| `UpdateSources` | uuid plus `UpdateSource[]`; lines `1-2`. | Drop or hardware-admin only |
| `TareEnable` | enable flag, uid, `TareData`; lines `1-3`. | Optional maintenance |
| `TareData` | `tuneGravitySpring`; line `1`. | Optional maintenance |
| `CalibrateArmEnable` | enable flag, uid, `CalibrateArmData`; lines `1-3`. | Optional maintenance |
| `CalibrateArmData` | `suppressWriteToFile`; line `1`. | Optional maintenance |

### ROS API Surface To Preserve For Hardware

#### Core State And Safety

| Name | Direction From Student/SDK | Type | Found In | Notes |
|---|---|---|---|---|
| `robot/state` | subscribe | `baxter_core_msgs/AssemblyState` | `baxter_interface/src/baxter_interface/robot_enable.py:77-80`; sim publishes at `baxter_sim_hardware/src/baxter_emulator.cpp:225` | Required for enable/fault/estop flow. |
| `robot/set_super_enable` | publish | `std_msgs/Bool` | `robot_enable.py:97-105`; `tuck_arms.py:95-97`; sim subscribes `baxter_emulator.cpp:255` | Required. Bridge must preserve command delivery. |
| `robot/set_super_reset` | publish | `std_msgs/Empty` | `robot_enable.py:152-166`; sim subscribes `baxter_emulator.cpp:257` | Required for stopped/error recovery. |
| `robot/set_super_stop` | publish | `std_msgs/Empty` | `robot_enable.py:179-184`; sim subscribes `baxter_emulator.cpp:256` | Safety-critical; avoid exposing casually in examples. |
| `rethink/software_version` | parameter read/write | string | `robot_enable.py:196-217`; sim sets in `baxter_world.launch:37-38`; `baxter.sh:30-31` selects Noetic | Preserve as diagnostic only. |

#### Limb Control And State

| Name | Direction From Student/SDK | Type | Found In | Notes |
|---|---|---|---|---|
| `/robot/joint_states` or `robot/joint_states` | subscribe | `sensor_msgs/JointState` | `limb.py:110-116`; sim FK subscribes `position_kinematics.cpp:41,67-69`; MoveIt remaps at `move_group.launch:38` | Required. QoS must suit high-rate state. |
| `/robot/limb/{left,right}/joint_command` | publish | `baxter_core_msgs/JointCommand` | `limb.py:91-95`; sim controller topics in `baxter_sim_controllers.yaml:18-21,44-47,71-74,97-100,182-204` | Required for hardware personality; differs from standard `ros2_control`. |
| `/robot/limb/{left,right}/set_speed_ratio` | publish | `std_msgs/Float64` | `limb.py:85-89,316-330` | Preserve if mimicking `Limb`; can be ignored by standard sim. |
| `/robot/limb/{left,right}/joint_command_timeout` | publish | `std_msgs/Float64` | `limb.py:97-101,295-313` | Required for velocity/torque safety semantics. |
| `/robot/limb/{left,right}/endpoint_state` | subscribe | `baxter_core_msgs/EndpointState` | `limb.py:103-108`; sim FK publishes `position_kinematics.cpp:61-69` | Required for SDK facade and IK examples. |
| `/robot/limb/{left,right}/inverse_dynamics_command` | publish by action server | `trajectory_msgs/JointTrajectoryPoint` | `joint_trajectory_action.py:121-125,288-290` | Needed only if preserving ROS 1 position-with-ID trajectory server behavior. |
| `/robot/joint_state_publish_rate` | publish | `std_msgs/UInt16` | `joint_trajectory_action.py:114-119`; examples publish in `joint_velocity_wobbler.py:52` | Optional tuning; bridge must handle if ROS 1 action server remains. |
| `robot/limb/{left,right}/suppress_collision_avoidance` | publish | `std_msgs/Empty` | `tuck_arms.py:87-93` | Preserve for tuck/untuck if hardware supports it. |
| `robot/limb/{left,right}/collision_avoidance_state` | subscribe | `baxter_core_msgs/CollisionAvoidanceState` | `tuck_arms.py:79-86` | Needed for safe tuck logic. |
| `robot/limb/{side}/suppress_cuff_interaction` | publish | `std_msgs/Empty` | `joint_torque_springs.py:80-81` | Drop with torque spring example unless needed. |

#### End Effectors, Head, Cameras, IO

| Name | Direction From Student/SDK | Type | Found In | Notes |
|---|---|---|---|---|
| `robot/end_effector/{left,right}_gripper/command` | publish | `baxter_core_msgs/EndEffectorCommand` | `gripper.py:80-91`; sim gripper controller YAML lines `6-7` | Required for gripper workflows. |
| `robot/end_effector/{left,right}_gripper/state` | subscribe | `baxter_core_msgs/EndEffectorState` | `gripper.py:105-108`; sim publishes `baxter_emulator.cpp:226-227` | Required. |
| `robot/end_effector/{left,right}_gripper/properties` | subscribe | `baxter_core_msgs/EndEffectorProperties` | `gripper.py:110-113`; sim publishes `baxter_emulator.cpp:228-229` | Required for gripper type/capabilities. |
| `robot/end_effector/{side}_gripper/rsdk/set_properties` | publish | `EndEffectorProperties` | `gripper.py:93-97` | Simulation/testing helper; optional. |
| `robot/end_effector/{side}_gripper/rsdk/set_state` | publish | `EndEffectorState` | `gripper.py:99-103` | Simulation/testing helper; optional. |
| `/robot/head/command_head_pan` | publish | `baxter_core_msgs/HeadPanCommand` | `head.py:59-62`; sim head controller YAML `baxter_sim_controllers.yaml:9-12` | Medium priority. |
| `/robot/head/command_head_nod` | publish | `std_msgs/Bool` | `head.py:64-67`; sim subscribes `baxter_emulator.cpp:72,262` | Optional. |
| `/robot/head/head_state` | subscribe | `baxter_core_msgs/HeadState` | `head.py:69-73`; sim publishes `baxter_emulator.cpp:250` | Medium priority. |
| `/cameras/list` | service call | `baxter_core_msgs/ListCameras` | `camera.py:76-78`; `camera_control.py:46-47`; smoke tests `smoketests.py:499-500` | Required for camera workflows. |
| `/cameras/open` | service call | `baxter_core_msgs/OpenCamera` | `camera.py:83` | Required for camera workflows. |
| `/cameras/close` | service call | `baxter_core_msgs/CloseCamera` | `camera.py:84` | Required for camera workflows. |
| `/cameras/reset` | service call | `std_srvs/Empty` | `camera_control.py:71-72` | Optional tool convenience. |
| `/cameras/head_camera/image` | subscribe | `sensor_msgs/Image` | `head_cam_display.py:31`; Gazebo camera namespace from `baxter_base.gazebo.xacro:80-94` | Bridge carefully; high bandwidth. |
| `/robot/xdisplay` | publish/subscribe in sim | `sensor_msgs/Image` | `xdisplay_image.py:53`; `head_cam_display.py:27`; sim display publisher `baxter_emulator.cpp:279-293` | Useful for demos; optional in minimum. |
| `/robot/digital_io/{component}/state` | subscribe | `baxter_core_msgs/DigitalIOState` | `digital_io.py:64-70`; sim IO publishes `qnode.cpp:91-102` | Medium; needed for cuff/navigator. |
| `/robot/digital_io/command` | publish | `baxter_core_msgs/DigitalOutputCommand` | `digital_io.py:79-84`; sim subscribes `baxter_emulator.cpp:61,261` | Medium. |
| `/robot/analog_io/{component}/state` | subscribe | `baxter_core_msgs/AnalogIOState` | `analog_io.py:63-69`; sim range state publishes `baxter_emulator.cpp:232-235` | Low/medium. |
| `/robot/analog_io/command` | publish | `baxter_core_msgs/AnalogOutputCommand` | `analog_io.py:78-83` | Low. |
| `robot/navigators/{left,right,torso_left,torso_right}_navigator/state` | subscribe | `baxter_core_msgs/NavigatorState` | `navigator.py:85-89`; sim IO publishes `qnode.cpp:84-89` | Low unless teaching uses cuff/navigator. |
| `/robot/range/{left,right}_hand_range/state` | publish in sim | `sensor_msgs/Range` | `baxter_emulator.cpp:54-55,230-231` | Optional sim/sensor feature. |

#### Services And Actions

| Name | Role | Type | Found In | Planning Note |
|---|---|---|---|---|
| `ExternalTools/{left,right}/PositionKinematicsNode/IKService` | IK service | `baxter_core_msgs/SolvePositionIK` | examples call `ik_service_client.py:56-57`; sim provides `position_kinematics.cpp:58-64` | Hardware bridge should expose or provide ROS 2 wrapper; sim can use MoveIt 2 IK instead. |
| `/robot/limb/{left,right}/follow_joint_trajectory` | action server | `control_msgs/FollowJointTrajectoryAction` | server namespace `joint_trajectory_action.py:66-72`; MoveIt controller config `baxter_controllers.yaml:1-25`; examples clients `joint_trajectory_client.py:59-61` | Critical for MoveIt/hardware. S04 must solve action crossing. |
| `/robot/end_effector/{side}_gripper/gripper_action` | action server | `control_msgs/GripperCommandAction` | `gripper_action.py:48-83`; client example `gripper_action_client.py:54-56` | Useful; can be ROS 2 shim over gripper topic. |
| `/robot/head/head_action` | action server | `control_msgs/SingleJointPositionAction` | `head_action.py:49-62`; client example `head_action_client.py:53-55` | Optional; ROS 2 `control_msgs` may not keep same action long term, verify in S04/S06. |
| `/gazebo/spawn_sdf_model`, `/gazebo/spawn_urdf_model`, `/gazebo/delete_model` | Classic Gazebo services | `gazebo_msgs/SpawnModel`, `DeleteModel` | `ik_pick_and_place_demo.py:217-276`; legacy PnP examples | Replace with Gazebo Sim workflows. |
| `/gazebo/get_link_properties`, `/gazebo/set_link_properties` | Classic Gazebo link services | `gazebo_msgs` | `arm_kinematics.cpp:74-80` | Replace/drop. |

### Dynamic Reconfigure And Parameters

Dynamic reconfigure files:

- `baxter_interface/cfg/PositionJointTrajectoryActionServer.cfg`: trajectory `goal_time`, stopped velocity tolerance, per-joint goal/path tolerances; lines `37-70`.
- `baxter_interface/cfg/VelocityJointTrajectoryActionServer.cfg`: trajectory tolerances plus per-joint PID gains; lines `37-82`.
- `baxter_interface/cfg/PositionFFJointTrajectoryActionServer.cfg`: position-with-inverse-dynamics tolerances; lines `37-70`.
- `baxter_interface/cfg/GripperActionServer.cfg`: per-gripper timeout/goal/velocity/forces/vacuum/blowoff; lines `37-64`.
- `baxter_interface/cfg/HeadActionServer.cfg`: head timeout and final error; lines `37-57`.
- `baxter_examples/cfg/JointSpringsExample.cfg`: torque spring/damping example; lines `35-57`; low priority.

Key ROS parameters and launch arguments:

- `robot_description` and `robot_description_semantic`: loaded by `baxter_world.launch:23-25`, `planning_context.launch:17-28`, `upload_description.launch:4`.
- Gripper args: `left_electric_gripper`, `right_electric_gripper` appear in sim and MoveIt launch files, including `baxter_world.launch:13-25` and `planning_context.launch:3-28`.
- Sim time/gui args: `paused`, `use_sim_time`, `gui`, `headless`, `debug` in `baxter_world.launch:6-35`.
- Kinematics params: `root_name`, `grav_right_name`, `grav_left_name`, tip names, joint-name arrays in `baxter_sim_kinematics.launch:15-27`; read by `position_kinematics.cpp:75-104`.
- Sim gripper type params: `left_gripper_type`, `right_gripper_type` in `baxter_sdk_control.launch:18-22`; read by `baxter_emulator.cpp:144-165`.
- MoveIt trajectory execution params: controller manager and execution tolerances in `trajectory_execution.launch:5-16`.
- Network/env assumptions: `baxter/baxter.sh` requires a Catkin root with `devel/setup.bash`, sets `ROS_MASTER_URI=http://${baxter_hostname}:11311`, and exports exactly one of `ROS_IP` or `ROS_HOSTNAME`; see `baxter.sh:17-31`, `115-153`.

### Launch Files, Scripts, Nodes, And Commands

Launch files discovered:

- `baxter_tools/launch/upload_description.launch`: loads static URDF text file.
- `baxter_examples/launch/*`: joystick, trajectory, and gripper action client examples.
- `baxter_moveit_config/launch/*`: MoveIt 1 demo, planning, RViz, warehouse, CHOMP/OMPL/STOMP-related launch files, Kinect/Xtion sensor manager variants.
- `baxter_simulator/baxter_gazebo/launch/baxter_world.launch`: Classic Gazebo world, robot spawn, sim controllers.
- `baxter_simulator/baxter_sim_hardware/launch/baxter_sdk_control.launch`: sim emulator, controller manager, robot state publisher, optional Qt IO.
- `baxter_simulator/baxter_sim_kinematics/launch/baxter_sim_kinematics.launch`: C++ FK/IK nodes.
- `baxter_simulator/baxter_sim_examples/launch/baxter_pick_and_place_demo.launch`: Classic pick-place.

User-facing scripts and executables:

- `baxter_interface/scripts/joint_trajectory_action_server.py`: starts left/right/both `FollowJointTrajectory` action servers; args `--limb`, `--rate`, `--mode`, `--interpolation`; lines `89-112`.
- `baxter_interface/scripts/gripper_action_server.py`: starts gripper action server for left/right/both; lines `65-72`.
- `baxter_interface/scripts/head_action_server.py`: starts head action server; lines `47-60`.
- `baxter_tools/scripts/enable_robot.py`: enable/disable/reset/stop entrypoint over `RobotEnable`.
- `baxter_tools/scripts/tuck_arms.py`: tuck/untuck using `Limb`, collision-avoidance suppression, and robot enable; key topics at lines `79-97`.
- `baxter_tools/scripts/camera_control.py`: camera list/open/close/reset through camera services.
- `baxter_tools/scripts/head_cam_display.py`: OpenCV display of `/cameras/head_camera/image` and optional `/robot/xdisplay` publishing.
- `baxter_tools/scripts/smoke_test.py`: hardware smoke tests for state, IK, xdisplay, cameras, grippers.
- `baxter_tools/scripts/tare.py`, `calibrate_arm.py`, `update_robot.py`: maintenance/admin tools using robust controller/update topics.
- `baxter_examples/scripts/*`: keyboard/joystick joint control, trajectory clients, IK client, gripper/head actions, IO examples, image display, recording/playback, URDF fragment, torque springs.
- `baxter_simulator/baxter_sim_hardware` executable `baxter_emulator`: publishes fake hardware state and xdisplay.
- `baxter_simulator/baxter_sim_io` executable `baxter_sim_io`: Qt-style navigator/IO simulation.
- `baxter_simulator/baxter_sim_kinematics` executable `kinematics`: provides sim FK/IK endpoint/IK service.

### Hidden Dependencies And Assumptions

- `tf`/`tf2`: Classic sim launches `tf2_ros/static_transform_publisher` in `baxter_world.launch:40-41`; sim kinematics uses `tf` and `tf_conversions`; MoveIt sensor launch uses `tf/static_transform_publisher` for external RGB-D cameras.
- OpenCV/cv_bridge: `baxter_tools` depends on `cv_bridge`; `smoketests.py` and `head_cam_display.py` use `cv2`/`CvBridge`; `baxter_sim_hardware` depends on `cv_bridge`, `image_transport`, `libopencv-dev`.
- Gazebo Classic: `baxter_description/urdf/baxter_base/baxter_base.gazebo.xacro` includes `libbaxter_gazebo_ros_control.so` and `libgazebo_ros_camera.so`; sim examples call `/gazebo/*` services.
- ROS 1 controller APIs: `baxter_sim_controllers` exports five `controller_interface::ControllerBase` plugins in `baxter_sim_controllers_plugins.xml:1-43`; sim YAML uses `joint_state_controller`, `effort_controllers`, and custom Baxter controllers.
- MoveIt 1 assumptions: controller configs use action names `/robot/limb/{right,left}/follow_joint_trajectory` in `baxter_controllers.yaml:1-25`; fake/simple controllers use `FollowJointTrajectory` for arms/hands.
- Robot namespace: code inconsistently uses `/robot/...` and `robot/...`; ROS 1 resolves many relative names globally depending on node namespace. S04 should define explicit bridge namespaces to avoid accidental ROS 2 remapping differences.
- Camera namespace: cameras live under `/cameras/{head_camera,left_hand_camera,right_hand_camera}/...`, separate from `/robot`.
- Hardware identity: `baxter.sh:21-31` contains a specific local robot hostname and workstation hostname; S07 should replace with template/env docs.
- Python compatibility: `baxter_examples/scripts/joint_velocity_puppet.py` and `joint_velocity_wobbler.py` use `xrange`; `send_urdf_fragment.py` imports `xacro_jade`; these are evidence against direct example porting.

### Package-By-Package API Notes

#### `baxter_common/baxter_common`

- No topics/services/actions/parameters.
- Metapackage dependency aggregator only.
- Decision: **Preserve** concept through ROS 2 common package grouping from ECN; no local code to port.
- Effort: **Low**.

#### `baxter_common/baxter_core_msgs`

- Provides all hardware-facing custom messages/services except maintenance.
- Critical bridge messages: `JointCommand`, `AssemblyState`, `EndEffector*`, `EndpointState`, `Head*`, `Camera*`, `BridgePublisher`.
- Critical bridge services: `SolvePositionIK`, camera open/list/close, bridge publisher arbitration services.
- No topics/actions directly.
- Decision: **Preserve**. Prefer S02 `CentraleNantesRobotics/baxter_common_ros2`; only fork if mapping gaps appear.
- Effort: **Low** for adoption; **Medium** if manually porting interfaces.

#### `baxter_common/baxter_description`

- URDF/Xacro and meshes. Main file `baxter.urdf.xacro` includes Baxter base, pedestal, and left/right end effectors.
- Classic-only pieces: `baxter_base.gazebo.xacro` inserts `libbaxter_gazebo_ros_control.so`, Gazebo camera plugins, material/sensor tags.
- Launch consumers: sim, MoveIt planning context, `upload_description.launch`.
- Decision: **Preserve geometry, replace simulation tags**. Use ROS 2 Xacro/URDF model as base for `robot_state_publisher`, MoveIt 2, Gazebo Harmonic/SDF conversion.
- Effort: **Medium** due to URDF cleanup and Gazebo Sim tags.

#### `baxter_common/baxter_maintenance_msgs`

- Used by `baxter_tools` maintenance/update/tare/calibration scripts.
- Tare/calibrate use robust controller namespaces `robustcontroller/{limb}/Tare` and `robustcontroller/{limb}/CalibrateArm`; see `tare.py:52-60`, `calibrate_arm.py:52-59`.
- Update tool topics: `/usb/update_sources`, `/updater/status`, `/updater/start`, `/updater/stop`; see `update_robot.py:62-80`.
- Decision: **Simplify/drop most**. Keep only if the lab requires robot-side maintenance through ROS 2.
- Effort: **Low**.

#### `baxter_common/rethink_ee_description`

- Electric/null/pneumatic gripper URDFs and meshes.
- Electric gripper Xacro uses `transmission_interface/SimpleTransmission` and `hardware_interface/EffortJointInterface`; grep found lines `86-105` in `rethink_electric_gripper.xacro`.
- Decision: **Preserve/simplify**. Keep geometry and gripper joint names; adapt transmissions for `ros2_control` if sim uses grippers.
- Effort: **Low/Medium**.

#### `baxter/baxter_sdk`

- Metapackage plus `baxter.sh` shell setup.
- `baxter.sh` configures Baxter hostname, workstation IP/hostname, ROS distro, `ROS_MASTER_URI`, and prompt; lines `21-31`, `147-153`.
- Decision: **Replace** with ROS 2 devcontainer/launch/networking documentation and bridge profiles.
- Effort: **Low**.

#### `baxter_interface`

- Main user-facing ROS 1 Python API.
- Classes and behavior to preserve selectively:
  - `Limb`: joint state/endpoint reads, `JointCommand` position/velocity/torque/raw modes, speed ratio, command timeout, neutral move.
  - `Gripper`: command/state/properties topics, JSON args/state, firmware/version checks, electric/suction behavior, open/close/calibrate/reset/parameter helpers.
  - `Head`: pan/nod command/state wrappers.
  - `CameraController`: list/open/close services and camera settings properties.
  - `RobotEnable`: enable/disable/reset/stop and estop/error semantics.
  - `DigitalIO`, `AnalogIO`, `Navigator`: IO/navigator wrappers.
  - `RobustController`: maintenance controller wrapper.
- Action servers:
  - `JointTrajectoryActionServer`: standard `FollowJointTrajectory` action server that commands Baxter `JointCommand`; important for hardware MoveIt and examples.
  - `GripperActionServer`: standard `GripperCommand` action over Baxter gripper API.
  - `HeadActionServer`: standard `SingleJointPosition` action over head pan API.
- Decision: **Preserve core behavior, not full implementation**. A ROS 2 facade should be thin; avoid reimplementing every blocking helper unless used by curated examples.
- Effort: **High**, because actions, safety state, Python 3.12, QoS, and bridge topology interact.

#### `baxter_tools`

- User-facing operational tools.
- Preserve/minimum hardware set:
  - `enable_robot.py`
  - `tuck_arms.py`
  - `camera_control.py`
  - `head_cam_display.py` or modern replacement viewer instructions
  - `smoke_test.py` logic as bridge/hardware smoke tests
- Optional/drop:
  - `update_robot.py`, `tare.py`, `calibrate_arm.py` unless lab explicitly needs maintenance workflows.
  - `description_publisher.py` can be replaced by `robot_state_publisher`/launch params.
- Decision: **Simplify**.
- Effort: **Medium**.

#### `baxter_examples`

- Contains broad tutorial scripts for joint control, trajectories, grippers, head, IO, cameras, recording/playback, URDF fragments, torque springs, project-specific PnP.
- Important examples to rewrite in ROS 2:
  - enable/untuck smoke flow from tools rather than an example script
  - joint position command
  - `FollowJointTrajectory` client
  - IK service or MoveIt 2 planning demo
  - camera view and gripper open/close
- Drop/simplify:
  - torque springs and raw torque/velocity examples for safety unless specifically taught
  - old joystick/keyboarding variants beyond one canonical teleop
  - `baxter_pnpcode*.py` and Classic Gazebo spawn demos
  - `send_urdf_fragment.py` using `xacro_jade`
- Decision: **Simplify**.
- Effort: **Medium**.

#### `baxter_moveit_config`

- MoveIt 1 package with OMPL/CHOMP/STOMP launch/config variants, SRDF, joint limits, kinematics, controller manager configs.
- Preserve concepts:
  - groups `left_arm`, `right_arm`, `both_arms`, `left_hand`, `right_hand` from `baxter.srdf:12-45`
  - neutral states from `baxter.srdf:47-64`
  - end effectors from `baxter.srdf:65-67`
  - virtual joint `world_joint` from `baxter.srdf:68-71`
  - controller action names from `baxter_controllers.yaml:1-25`
  - KDL solver settings as a reference from `kinematics.yaml:1-14`
- Replace:
  - MoveIt 1 launch files and plugin names
  - warehouse/mongo launch unless a modern equivalent is needed
  - Kinect/Xtion sensor manager unless courses require depth sensors
- Decision: **Replace with regenerated MoveIt 2 config**.
- Effort: **Medium**.

#### `baxter_simulator/baxter_simulator`

- Metapackage aggregating Classic simulator packages.
- Decision: **Drop/replace** with a Jazzy/Harmonic metapackage only if S05/S08 wants equivalent grouping.
- Effort: **Low**.

#### `baxter_simulator/baxter_gazebo`

- Classic Gazebo world launch and custom `baxter_gazebo_ros_control` plugin.
- `baxter_world.launch` loads URDF with `gazebo:=true`, starts `gazebo_ros/empty_world`, spawns model, static transform, and includes `baxter_sdk_control.launch`; lines `23-66`.
- Decision: **Replace** with Gazebo Harmonic + `ros_gz` + `gz_ros2_control` architecture.
- Effort: **High**.

#### `baxter_simulator/baxter_sim_controllers`

- C++ custom ROS 1 controller plugins:
  - `BaxterPositionController`
  - `BaxterVelocityController`
  - `BaxterEffortController`
  - `BaxterHeadController`
  - `BaxterGripperController`
- Each subscribes to Baxter-native command topics when `topic` param is set; grep found `JointCommand` subscribers in position/velocity/effort controllers and `EndEffectorCommand`/`HeadPanCommand` in gripper/head controllers.
- Decision: **Replace** with standard `ros2_control` controllers unless S05 explicitly wants a Baxter `JointCommand` compatibility shim.
- Effort: **High**.

#### `baxter_simulator/baxter_sim_examples`

- Classic Gazebo pick-and-place demo, duplicate script copy included.
- Uses `SolvePositionIK` service and `/gazebo/spawn_*`/`delete_model` services.
- Decision: **Replace/simplify** with Gazebo Harmonic + MoveIt 2 example.
- Effort: **Medium**.

#### `baxter_simulator/baxter_sim_hardware`

- `baxter_emulator` publishes ROS 1 fake hardware state and display, subscribes to enable/stop/reset/joint_states/laser/nav/head topics.
- Controller config `baxter_sim_controllers.yaml` sets custom controllers to consume Baxter `JointCommand` topics and individual effort controllers.
- Decision: **Replace** with `ros2_control` hardware/simulation interfaces, optional state shim for hardware-faithful API.
- Effort: **High**.

#### `baxter_simulator/baxter_sim_io`

- C++ Qt-style navigator and cuff/digital IO simulator.
- Publishes navigator and digital IO state topics; subscribes light command state topics.
- Decision: **Drop initially**. Add only if navigator/cuff simulation becomes a teaching requirement.
- Effort: **Medium**.

#### `baxter_simulator/baxter_sim_kinematics`

- C++ KDL FK/IK service and endpoint publisher.
- Provides `ExternalTools/{side}/PositionKinematicsNode/IKService` and `/robot/limb/{side}/endpoint_state`; uses `/robot/joint_states` and `/robot/state`.
- Uses Gazebo link property services for gravity/kinematics support.
- Decision: **Replace**. In sim, use MoveIt 2 kinematics and `robot_state_publisher`; for hardware, bridge the real IK service or provide a ROS 2 wrapper.
- Effort: **Medium**.

### Preserve/Replace/Simplify/Drop Summary

Preserve:

- `baxter_core_msgs` message/service definitions.
- Baxter URDF/meshes and end-effector geometry, excluding Classic-specific simulation tags.
- Hardware-facing `/robot/*`, `/cameras/*`, and `ExternalTools/*/IKService` names needed by bridge/hardware mode.
- Standard action intent for `FollowJointTrajectory`, gripper, and head where used by MoveIt/examples.
- Robot enable/reset/state semantics.

Replace:

- `baxter.sh` with ROS 2/bridge/devcontainer setup docs.
- MoveIt 1 config with regenerated MoveIt 2.
- Entire Gazebo Classic simulator implementation with Gazebo Harmonic + `ros2_control`.
- ROS 1 `controller_interface` plugins with standard Jazzy controllers or small compatibility shims.

Simplify:

- `baxter_interface` to the subset needed for student hardware examples.
- `baxter_tools` to enable, tuck/untuck, camera, and bridge smoke tests.
- `baxter_examples` to 3-5 curated examples.
- Maintenance messages/tools unless the lab has a concrete need.

Drop initially:

- Robot software update workflow.
- Tare/calibrate robust controller flows from ROS 2 student side.
- Qt navigator simulator.
- Classic Gazebo spawn/delete demos and project-specific PnP scripts.
- Warehouse/mongo and old RGB-D sensor launch variants unless courses require them.

## Decisions

1. **Use `baxter_core_msgs` as the bridge contract.** S04 should build its allowlist around `AssemblyState`, `JointCommand`, `EndpointState`, `EndEffector*`, `Head*`, `Camera*`, `DigitalIO*`, `NavigatorState`, `SolvePositionIK`, camera services, and bridge publisher arbitration services.
2. **Do not bridge every topic by default.** The minimum hardware allowlist should cover enable/reset/state, joint state, limb commands, trajectory actions or equivalent shims, IK, one camera stream/control path, and gripper state/command. IO/navigator/range/head/xdisplay are secondary.
3. **Treat `FollowJointTrajectory` as critical.** Hardware MoveIt/examples depend on `/robot/limb/{left,right}/follow_joint_trajectory`. S04 must choose between bridging ROS 1 actions, running ROS 1 action servers behind a ROS 2 shim, or implementing a ROS 2 action server that commands bridged `JointCommand` topics.
4. **Treat `JointCommand` as hardware-personality-specific.** Standard ROS 2 sim should use `joint_trajectory_controller`; a Baxter-native `JointCommand` sim shim is optional and should be justified by course parity needs.
5. **Regenerate MoveIt 2 config.** Reuse SRDF group/joint/end-effector concepts and controller names as references, but do not carry MoveIt 1 launch/plugin files forward.
6. **Replace the simulator, not port it.** All C++ code under `baxter_simulator/*` depends on ROS 1/Gazebo Classic/controller APIs. S05 should design a Harmonic stack from standard Jazzy components and community references from S02.
7. **Keep the ROS 2 SDK facade thin.** Preserve familiar class names only where they reduce student friction. Do not recreate all blocking helpers, maintenance wrappers, or examples without a concrete workflow.
8. **Make networking explicit.** `baxter.sh` encodes ROS 1 master/hostname assumptions. S04/S07 should replace this with documented topologies for ECN bridge or Rethought Zenoh bridge.

## Open Questions

- Which hardware API subset does the target course actually need: arms only, or arms plus gripper/camera/head/navigator/IO?
- Does the target robot expose the same `/cameras/*`, `ExternalTools/*/IKService`, and `FollowJointTrajectory` action namespaces as this Noetic reference stack?
- Should S04 prefer action bridging, ROS 2 action shims, or direct `JointCommand` topic commands for hardware motion?
- Should the hardware bridge include `BridgePublishersAuth`/`BridgePublishersForce` arbitration services from ECN, or can the university operate with single-user bridge access?
- Is standard `ros2_control` simulation acceptable even though it does not preserve Baxter `JointCommand` behavior?
- Are camera streams required over the bridge for all students, and what QoS/compression/transport policy is acceptable on the lab network?
- Are tare/calibration/update tools allowed from student machines, or should they remain robot-admin-only on the ROS 1 side?
- Which physical end effectors are installed: electric grippers, pneumatic/suction grippers, passive/custom hands, or mixed?

## Artifacts

- Updated this S03 analysis log: `logs/S03_local_repo_analysis.log.md`
- Updated S03 status in `MASTER_PLAN.md`
- Appended S04 handoff prompt to `PROMPTS.md`
- Read-only reference inspected: `baxter_noetic_ref/`
- Important local source paths inspected:
  - `baxter_noetic_ref/**/package.xml`
  - `baxter_noetic_ref/baxter_common/baxter_core_msgs/msg/*.msg`
  - `baxter_noetic_ref/baxter_common/baxter_core_msgs/srv/*.srv`
  - `baxter_noetic_ref/baxter_common/baxter_maintenance_msgs/msg/*.msg`
  - `baxter_noetic_ref/baxter_interface/src/baxter_interface/*.py`
  - `baxter_noetic_ref/baxter_interface/src/joint_trajectory_action/joint_trajectory_action.py`
  - `baxter_noetic_ref/baxter_interface/src/gripper_action/gripper_action.py`
  - `baxter_noetic_ref/baxter_interface/src/head_action/head_action.py`
  - `baxter_noetic_ref/baxter_tools/scripts/*.py`
  - `baxter_noetic_ref/baxter_examples/scripts/*.py`
  - `baxter_noetic_ref/baxter_moveit_config/{launch,config}/`
  - `baxter_noetic_ref/baxter_simulator/**/{src,include,launch,config}/`
  - `baxter_noetic_ref/baxter/baxter.sh`
