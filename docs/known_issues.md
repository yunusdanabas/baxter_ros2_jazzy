# Known Issues

Defects in the sim-first baseline, with what is and is not affected. No defect is currently
open. Unsupported hardware scope is not listed here; see `package_map.md`.

## Resolved: MotionPlanning display failed to load its robot model

**Status:** fixed 2026-07-22.

**Symptom:** the MotionPlanning panel opened with a red `NO PLANNING LIBRARY LOADED`, empty
planner dropdowns, no planning group, and no interactive marker on either gripper, while
`move_group` planned and executed normally. `loadRobotModel` aborted with:

```text
[rviz2.moveit.ros.background_processing]: Exception caught while processing action
'loadRobotModel': parameter
'robot_description_kinematics.left_arm.kinematics_solver_search_resolution' has invalid
type: Wrong parameter type, parameter {...} is of type {double}, setting it to {string}
is not allowed.
```

### Cause: a comma-decimal locale

`rviz2`'s `main.cpp` constructs `QApplication` **before** `rclcpp::init`. `QApplication`
calls `setlocale(LC_ALL, "")`, so by the time rcl parses the `--params-file` arguments the
process has left the `C` locale that every C program starts in.
`rcl_yaml_param_parser/src/parse.c` accepts a scalar as a double only when `strtod` consumes
it whole; under `LC_NUMERIC=tr_TR.UTF-8` the decimal separator is `,`, so `strtod("0.005")`
stops at the `.` and the value is stored as a **string**. MoveIt's kinematics `ParamListener`
then declares that key as a statically typed double, rclcpp rejects the string override with
`InvalidParameterTypeException`, and `RobotModelLoader` — which catches only
`rclcpp::ParameterTypeException` — lets it escape and abort the background job.

That is why removing parameters only moved the failure: *every* double reaching `rviz2` was
corrupt, so dropping `joint_limits` (`max_velocity: 0.75`) merely exposed the next one
(`kinematics_solver_search_resolution: 0.005`). `max_acceleration: 2.0` never appeared
because `strtod` does consume `2.0` even in `tr_TR`. `move_group` was never affected because
it has no Qt and stays in the `C` locale.

### Fix

`additional_env={"LC_NUMERIC": "C"}` on the `rviz2` node in `sim_moveit.launch.py`. This
applies to any comma-decimal locale (`tr`, `de`, `fr`, `es`, `it`, `nl`, …), not just Turkish.
An explicit `LC_ALL` in the environment would override it.

### Correction to the earlier investigation

This cause was previously recorded as ruled out because `strtod("0.75")` appeared to consume
the whole string under `tr_TR.UTF-8`. **That test was invalid.** A C program starts in the `C`
locale and only leaves it when something calls `setlocale` — which a standalone test binary
never does and Qt always does. The same flaw invalidated the companion test that drove
`rcl_parse_yaml_file` over the temp params files. Any test of this behaviour must call
`setlocale(LC_ALL, "")` first, or set `LC_NUMERIC` on the process under test.

Two hypotheses from that investigation do still hold and were not the cause:
`moveit_configs_utils` emits correct Python `float`s, and the `.rviz` config is not involved.

## Benign log noise

These appear in normal, healthy runs. They are not defects and need no action.

| Message | Explanation |
|---|---|
| `No root/virtual joint specified in SRDF. Assuming fixed joint` | Correct here. `baxter_gz_control.urdf.xacro` already contains `world_joint`, so the model frame is `world`. The ROS 1 SRDF needed a `<virtual_joint>` only because its URDF root was `base`. |
| `[Err] Physics.cc:1808 ... mimic constraint for l_gripper_r_finger_joint` | The Gazebo physics engine has no mimic-joint support. Gripper fingers are out of scope. |
| `No 3D sensor plugin(s) defined for octomap updates` and the octomap resolution warning | Expected; no depth sensors are configured. |
| `Action server: /recognize_objects not available` | Expected; no object-recognition pipeline. |
| `class_loader ... SEVERE WARNING!!! A namespace collision has occurred with plugin factory for class rviz_default_plugins::displays::InteractiveMarkerDisplay` | Upstream RViz/MoveIt plugin double-registration. Cosmetic. |
| `motion_planning_frame: MoveGroup namespace changed: / -> . Reloading params.` | Prints on every MoveIt RViz start, upstream. `PlanningSceneDisplay` defaults the "Move Group Namespace" property to `""` and compares it against the node namespace `/`, so the branch is always taken. Not a symptom of anything. |
| `Publisher already registered for node name: 'rviz2'` | RViz creates more than one node object with the same name. Cosmetic. |
| `tf2_echo` printing `Invalid frame ID "torso"` for the first second or two | TF is not published yet at startup; it resolves and then streams. |
| `Desired controller update period (0.01 s) is slower than the gazebo simulation period (0.001 s)` | Intentional: controllers run at 100 Hz, physics at 1 kHz. |
| `Executor is not available during hardware component initialization` | `gz_ros2_control` initialises the hardware before the executor exists. |
| `publish_async_failures_ 7` at shutdown | `pal_statistics` counter during teardown. Cosmetic. |
| `moveit_tiny` and `moveit_left_tiny` being the same script | Intentional. `moveit_left_tiny` is the no-argument smoke; `moveit_tiny` is the same client driven with `-p group:=`. |
