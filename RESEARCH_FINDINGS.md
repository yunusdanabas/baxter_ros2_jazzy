# Research Findings — Implementation Cheat Sheet

Pre-implementation research conducted 2026-06-23. These findings inform the implementation steps in `MASTER_PLAN.md`.

---

## 1. ECN `baxter_common_ros2` @ `678bfabe`

### Package Inventory

| Package | Build Type | Dependencies |
|---|---|---|
| `baxter_core_msgs` | `ament_cmake` | `geometry_msgs`, `sensor_msgs`, `std_msgs`, `builtin_interfaces` |
| `baxter_description` | `ament_cmake` | `urdf`, `rethink_ee_description` |
| `baxter_maintenance_msgs` | `ament_cmake` | `std_msgs` |
| `rethink_ee_description` | `ament_cmake` | `urdf` |
| `baxter_bridge` | `ament_cmake` | `rclcpp`, `sensor_msgs`, `baxter_core_msgs`, `diagnostic_msgs`, `trajectory_msgs`, `robot_state_publisher`, OpenCV, **ROS 1 libs** |

### CRITICAL: `baxter_bridge` Requires ROS 1 Libraries

`baxter_bridge` directly links against ROS 1 `.so` libraries:
- `roscpp`, `rosconsole`, `roscpp_serialization`, `rostime`, `xmlrpcpp`
- Loaded from `/opt/ros/${ROS1_VERSION_DEFAULT}` (defaults to `noetic` or `obese`)
- **Not available on Ubuntu 24.04 Noble**
- `rosdep` will NOT resolve these — they're only in `CMakeLists.txt` via filesystem paths
- Pre-generated ROS 1 message headers are vendored in `ros1_msgs/` directory

**Decision:** Skip `baxter_bridge` from default sim builds. Build it only on bridge host in I10.

### Joint Names — Legacy Format Confirmed

From `baxter_base.urdf.xacro`:

**Right arm:** `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`

**Left arm:** `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2`

**Other:** `head_pan` (revolute), `head_nod` (fixed), `torso_t0` (fixed)

### Electric Gripper Joint Names

| Joint | Type | Description |
|---|---|---|
| `l_gripper_l_finger_joint` | prismatic | Left gripper left finger (0.0 to 0.020833m) |
| `l_gripper_r_finger_joint` | prismatic | Mimics left (`multiplier="-1.0"`) |
| `r_gripper_l_finger_joint` | prismatic | Right gripper left finger |
| `r_gripper_r_finger_joint` | prismatic | Mimics left |

### End-Effector Link Names

- `${side}_gripper_base` — gripper body
- `${side}_gripper` — tip frame
- `l_gripper_l_finger`, `l_gripper_r_finger` — left gripper fingers
- `r_gripper_l_finger`, `r_gripper_r_finger` — right gripper fingers

### Known Issues

- **Issue #5:** Build fails without ROS 1 headers/libs installed. Maintainer guidance: install `baxter_legacy` debs.
- **No Jazzy validation** exists in upstream issue tracker. We are breaking new ground.

---

## 2. ros2_control Configuration (Jazzy)

### URDF `<ros2_control>` Block

```xml
<ros2_control name="GazeboSimSystem" type="system">
  <hardware>
    <plugin>gz_ros2_control/GazeboSimSystem</plugin>
  </hardware>
  <joint name="left_s0">
    <command_interface name="position">
      <param name="min">-1.7</param>
      <param name="max">1.7</param>
    </command_interface>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
  <!-- ... repeat for all 14 arm joints ... -->
</ros2_control>
```

### Gazebo Plugin Tag

```xml
<gazebo>
  <plugin filename="libgz_ros2_control-system.so"
          name="gz_ros2_control::GazeboSimROS2ControlPlugin">
    <parameters>$(find baxter_gz_sim)/config/ros2_controllers.yaml</parameters>
  </plugin>
</gazebo>
```

### Controller YAML Format

```yaml
controller_manager:
  ros__parameters:
    update_rate: 100  # Hz

    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

    left_arm_controller:
      type: joint_trajectory_controller/JointTrajectoryController

    right_arm_controller:
      type: joint_trajectory_controller/JointTrajectoryController

left_arm_controller:
  ros__parameters:
    joints:
      - left_s0
      - left_s1
      - left_e0
      - left_e1
      - left_w0
      - left_w1
      - left_w2
    command_interfaces:
      - position
    state_interfaces:
      - position
      - velocity
    action_monitor_rate: 20.0
    allow_partial_joints_goal: false
    interpolate_from_desired_state: true

right_arm_controller:
  ros__parameters:
    joints:
      - right_s0
      - right_s1
      - right_e0
      - right_e1
      - right_w0
      - right_w1
      - right_w2
    command_interfaces:
      - position
    state_interfaces:
      - position
      - velocity
    action_monitor_rate: 20.0
    allow_partial_joints_goal: false
    interpolate_from_desired_state: true
```

### Gripper Controller (NOT deprecated GripperActionController)

```yaml
controller_manager:
  ros__parameters:
    left_gripper_controller:
      type: forward_command_controller/ForwardCommandController

left_gripper_controller:
  ros__parameters:
    joints:
      - l_gripper_l_finger_joint
    interface_name: position
```

### Controller Spawning — NOT Auto-Spawned

Controllers must be explicitly spawned using `spawner` with `OnProcessExit` event handlers:

```python
from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node

# 1. Robot state publisher
rsp = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'robot_description': robot_description_xml}],
)

# 2. Spawn robot in Gazebo
spawn = Node(
    package='ros_gz_sim',
    executable='create',
    parameters=[{'name': 'baxter', 'topic': 'robot_description'}],
)

# 3. Spawn joint_state_broadcaster AFTER entity spawn
jsb_spawner = Node(
    package='controller_manager',
    executable='spawner',
    arguments=['joint_state_broadcaster'],
)

# 4. Spawn arm controllers AFTER broadcaster active
left_arm_spawner = Node(
    package='controller_manager',
    executable='spawner',
    arguments=['left_arm_controller', '--param-file', controllers_yaml],
)

right_arm_spawner = Node(
    package='controller_manager',
    executable='spawner',
    arguments=['right_arm_controller', '--param-file', controllers_yaml],
)

# Sequencing
return LaunchDescription([
    rsp,
    spawn,
    RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn,
            on_exit=[jsb_spawner],
        )
    ),
    RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=jsb_spawner,
            on_exit=[left_arm_spawner, right_arm_spawner],
        )
    ),
])
```

### Spawner CLI

```bash
# Load + configure + activate
ros2 run controller_manager spawner joint_trajectory_controller --param-file /path/to/controllers.yaml

# Load only (don't configure)
ros2 run controller_manager spawner my_controller --load-only

# Unload on kill (for launch files)
ros2 run controller_manager spawner my_controller -u
```

---

## 3. Gazebo Harmonic Setup (Jazzy)

### Minimal World — Use Built-in `empty.sdf`

No custom SDF needed initially. Gazebo ships `empty.sdf`.

### Launch File

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Headless mode: -r -s
    # GUI mode: -r
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r -s empty.sdf'}.items(),  # headless
    )

    return LaunchDescription([gazebo])
```

### `gz_args` Flags

| Flag | Purpose |
|---|---|
| `-r` | Run simulation immediately (auto-play) |
| `-s` | Headless mode (server only, no GUI) |
| `-r -s` | Headless + auto-run |
| `empty.sdf` | Built-in empty world |
| `path/to/world.sdf` | Custom world file |

### Spawning Robot Entity

```python
from launch_ros.actions import Node

spawn = Node(
    package='ros_gz_sim',
    executable='create',
    parameters=[{
        'name': 'baxter',
        'topic': 'robot_description',  # reads URDF from this ROS topic
    }],
    output='screen',
)
```

### ros_gz_bridge for Sensors

```yaml
# bridge.yaml
- ros_topic_name: "clock"
  gz_topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS

- ros_topic_name: "camera/image_raw"
  gz_topic_name: "/camera/image"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS
```

```python
bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=[
        '--ros-args', '-p',
        f'config_file:={os.path.join(pkg_dir, "config", "bridge.yaml")}',
    ],
)
```

### Headless Mode Limitations

- **Stable** for server/CI use
- **Camera/sensor plugins that require rendering will NOT produce data** in pure headless mode
- For camera testing, use Xvfb: `xvfb-run -a ros2 launch your_pkg launch.py`
- **Decision:** Accept camera-less headless for CI; add cameras later when rendering available

### Known Issues

- `ign_*` prefixes fully deprecated in Jazzy — use `gz_*` everywhere
- `/clock` topic: if Gazebo detects another `/clock` publisher, it publishes on `/world/<worldname>/clock` instead. Always use unidirectional clock bridge.
- `hold_joints: true` is default — joints hold position when no controller active

---

## 4. MoveIt 2 Configuration (Jazzy)

### Setup Assistant

```bash
sudo apt install ros-jazzy-moveit-setup-assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
```

### Config Package Structure

```
baxter_moveit_config/
├── config/
│   ├── baxter.srdf
│   ├── kinematics.yaml
│   ├── joint_limits.yaml
│   ├── ompl_planning.yaml
│   ├── moveit_controllers_sim.yaml
│   ├── moveit_controllers_hardware.yaml
│   └── moveit_controllers_fake.yaml
├── launch/
│   ├── demo.launch.py
│   ├── move_group.launch.py
│   ├── moveit_rviz.launch.py
│   └── rsp.launch.py
├── .setup_assistant
├── CMakeLists.txt
└── package.xml
```

### KDL Kinematics (`kinematics.yaml`)

```yaml
left_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.05
  kinematics_solver_attempts: 3

right_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.05
  kinematics_solver_attempts: 3
```

### OMPL Planning (`ompl_planning.yaml`) — NEW JAZZY FORMAT

```yaml
planning:
  planning_pipelines: [ompl]
  ompl:
    planning_plugins: [ompl_interface/OMPLPlanner]
    request_adapters:
      - default_planning_request_adapters/ResolveConstraintFrames
      - default_planning_request_adapters/ValidateWorkspaceBounds
      - default_planning_request_adapters/CheckStartStateBounds
      - default_planning_request_adapters/CheckStartStateCollision
    response_adapters:
      - default_planning_response_adapters/AddTimeOptimalParameterization
      - default_planning_response_adapters/ValidateSolution
      - default_planning_response_adapters/DisplayMotionPath

    planner_configs:
      RRTConnectkConfigDefault:
        type: geometric::RRTConnect
        range: 0.0

    left_arm:
      default_planner_config: RRTConnectkConfigDefault
      planner_configs:
        - RRTConnectkConfigDefault
      projection_evaluator: joints(left_s0,left_s1)
      longest_valid_segment_fraction: 0.005

    right_arm:
      default_planner_config: RRTConnectkConfigDefault
      planner_configs:
        - RRTConnectkConfigDefault
      projection_evaluator: joints(right_s0,right_s1)
      longest_valid_segment_fraction: 0.005
```

**Key change from MoveIt 1:** Uses `planning_plugins`/`request_adapters`/`response_adapters` instead of old pipeline format.

### MoveIt Controller Integration (`moveit_controllers_sim.yaml`)

```yaml
moveit_controller_manager: moveit_simple_controller_manager/MoveItSimpleControllerManager

moveit_simple_controller_manager:
  controller_names:
    - left_arm_controller
    - right_arm_controller

  left_arm_controller:
    type: FollowJointTrajectory
    action_ns: follow_joint_trajectory
    default: true
    joints:
      - left_s0
      - left_s1
      - left_e0
      - left_e1
      - left_w0
      - left_w1
      - left_w2

  right_arm_controller:
    type: FollowJointTrajectory
    action_ns: follow_joint_trajectory
    default: true
    joints:
      - right_s0
      - right_s1
      - right_e0
      - right_e1
      - right_w0
      - right_w1
      - right_w2
```

### SRDF Format — Same as MoveIt 1

```xml
<?xml version="1.0" encoding="UTF-8"?>
<robot name="baxter">
  <virtual_joint name="virtual_joint" type="fixed"
    parent_frame="world" child_link="base" />

  <group name="left_arm">
    <chain base_link="torso" tip_link="left_gripper" />
  </group>

  <group name="right_arm">
    <chain base_link="torso" tip_link="right_gripper" />
  </group>

  <group name="both_arms">
    <group name="left_arm" />
    <group name="right_arm" />
  </group>

  <group_state name="left_neutral" group="left_arm">
    <joint name="left_s0" value="0.0" />
    <joint name="left_s1" value="-0.55" />
    <joint name="left_e0" value="0.0" />
    <joint name="left_e1" value="0.75" />
    <joint name="left_w0" value="0.0" />
    <joint name="left_w1" value="1.26" />
    <joint name="left_w2" value="0.0" />
  </group_state>

  <group_state name="right_neutral" group="right_arm">
    <joint name="right_s0" value="0.0" />
    <joint name="right_s1" value="-0.55" />
    <joint name="right_e0" value="0.0" />
    <joint name="right_e1" value="0.75" />
    <joint name="right_w0" value="0.0" />
    <joint name="right_w1" value="1.26" />
    <joint name="right_w2" value="0.0" />
  </group_state>
</robot>
```

### MoveItConfigsBuilder for Launch Files

```python
from moveit_configs_utils import MoveItConfigsBuilder

moveit_config = (
    MoveItConfigsBuilder("baxter", package_name="baxter_moveit_config")
    .robot_description(file_path="config/baxter.urdf.xacro")
    .robot_description_semantic(file_path="config/baxter.srdf")
    .trajectory_execution(file_path="config/moveit_controllers_sim.yaml")
    .planning_pipelines(pipelines=["ompl"])
    .to_moveit_configs()
)
```

---

## 5. Exact Apt Package Names (Jazzy)

### Core ROS 2

```bash
sudo apt install ros-jazzy-desktop
```

### ros2_control

```bash
sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers
```

Includes: `joint_trajectory_controller`, `joint_state_broadcaster`, `gripper_controllers`, `forward_command_controller`, `position_controllers`, `controller_manager` (with `spawner`/`unspawner`).

### Gazebo Harmonic

```bash
sudo apt install ros-jazzy-ros-gz ros-jazzy-gz-ros2-control
```

Includes: `ros_gz_sim`, `ros_gz_bridge`, `ros_gz_image`, `gz_ros2_control`, Gazebo Harmonic libraries (bundled via vendor packages from `packages.ros.org`).

### MoveIt 2

```bash
sudo apt install ros-jazzy-moveit
```

Includes: `moveit_ros_move_group`, `moveit_kinematics`, `moveit_planners_ompl`, `moveit_ros_visualization`, `moveit_simple_controller_manager`, `moveit_configs_utils`, `moveit_setup_assistant`.

### Full Install Command

```bash
sudo apt install \
  ros-jazzy-desktop \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-ros-gz \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-moveit \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui
```

---

## 6. Critical Implementation Notes

### `baxter_bridge` Build Failure

- **Will fail** on clean Jazzy/Noble without ROS 1 libs
- **Solution:** `colcon build --packages-skip baxter_bridge` for sim builds
- Bridge build belongs in I10 on bridge host with `baxter_legacy` debs installed

### Controller Spawning Order

1. `robot_state_publisher` (provides URDF)
2. Gazebo Sim + spawn entity
3. `spawner joint_state_broadcaster` (after entity spawn)
4. `spawner left_arm_controller` (after broadcaster active)
5. `spawner right_arm_controller` (after broadcaster active)

Use `OnProcessExit` event handlers for sequencing.

### OMPL Config Format Change

MoveIt 2 Jazzy uses `planning_plugins`/`request_adapters`/`response_adapters` — NOT the old MoveIt 1 pipeline format. Copying old `ompl_planning.yaml` will fail.

### Gripper Controller Deprecation

`GripperActionController` is deprecated in Jazzy. Use `forward_command_controller/ForwardCommandController` for Baxter's electric gripper mimic joints.

### Headless Camera Limitation

Pure headless Gazebo (`-s` flag) will NOT produce camera data. Accept camera-less headless for CI; add Xvfb or GUI mode for camera testing.

### Joint Names Unchanged

ECN `baxter_description` uses exact legacy joint names. No migration needed for controllers or MoveIt configs.
