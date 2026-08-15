# Baxter ROS 2 Jazzy Migration Research Report

## Executive Summary
Migrating the Baxter Research Robot SDK to ROS 2 Jazzy is highly feasible, but it requires a **hybrid architecture** due to hardware constraints. The physical Baxter robot contains an internal PC running an older, locked-down version of ROS 1. Installing ROS 2 directly on the robot's hardware is not viable without risking bricking the system. Therefore, physical hardware support requires a specialized ROS 1/ROS 2 bridge running on the user's workstation. Conversely, the simulation stack can and should be rebuilt as a **100% native ROS 2 Jazzy** environment.

---

## 1. Feasibility
*   **Real Robot:** Feasible, but requires bridging. We must run a specialized bridge (e.g., a pre-compiled `baxter_bridge` to avoid the overhead of a generic `ros1_bridge`) on the workstation to translate custom `baxter_core_msgs` and standard ROS topics between the robot's internal ROS 1 master and the user's ROS 2 workspace.
*   **Simulation:** Highly feasible and recommended. A pure ROS 2 Jazzy simulation can be built from scratch, entirely dropping the ROS 1 dependency for users who do not have physical hardware.
*   **Community Groundwork:** The community has already laid the foundation by porting `baxter_common` (URDF, meshes, custom messages) to ROS 2. We are not starting from scratch.

## 2. Architecture
*   **Core Packages (`baxter_common`):** Must be ported to use `ament_cmake`. This includes compiling ROS 2 versions of all custom Baxter messages.
*   **Simulation Stack:** The legacy `baxter_simulator` (built for Gazebo Classic) must be discarded. ROS 2 Jazzy defaults to **Gazebo Harmonic**. The robot's URDF/Xacro files must be updated to use `<gz>` plugin tags instead of `<gazebo>`, and the control stack must transition to `gz_ros2_control` and `ros_gz_bridge`.
*   **SDK (`baxter_interface` & Examples):** The core Python SDK needs to be rewritten from `rospy` to `rclpy`, adopting modern ROS 2 paradigms such as node composition, QoS profiles, and executors.
*   **Motion Planning (`baxter_moveit_config`):** Must be rebuilt using **MoveIt 2**. This will involve migrating the SRDF and configuration files to utilize MoveIt 2's modern planners and standard ROS 2 action servers.

## 3. Real Robot vs. Simulation
*   **Real Robot:** Users are tied to the legacy network configuration (`ROS_MASTER_URI`, `ROS_IP`). High-frequency, low-latency control (e.g., custom torque control loops) might suffer slightly due to bridge overhead. The robot's internal safety controllers remain untouchable.
*   **Simulation:** An uncompromised, modern ROS 2 environment. We can write a native `ros2_control` hardware interface for the simulated Baxter, completely bypassing any bridging logic.
*   **Gap:** Code written for the real robot relies on bridged topics, while simulation code could theoretically use native ROS 2 hardware interfaces. To maintain SDK parity, the user-facing API (`baxter_interface`) must abstract these differences so that user code runs identically on both.

## 4. Improvements Worth Adding
*   **Docker/Dev Containers:** A major pain point for users is setting up hybrid ROS 1/ROS 2 environments. Shipping a `.devcontainer` that pre-installs ROS 2 Jazzy, Gazebo Harmonic, and the necessary bridging tools will allow university students to start coding in minutes.
*   **Modernized Documentation:** A comprehensive GitHub Pages/Sphinx site explaining the bridge setup.
*   **CI/CD:** GitHub Actions to automatically build the ROS 2 packages and run tests against the Gazebo Harmonic simulation.
*   **Ignition/Harmonic Demos:** Updated examples showcasing sensor integration (cameras, depth sensors) in the new Gazebo environment.

## 5. Risks and Unknowns
*   **Hardware Maintenance:** Rethink Robotics is defunct. Parts are scarce, and physical hardware will eventually fail. The long-term value of this port heavily leans on the simulation aspect.
*   **Bridge Stability:** Relying on a community-maintained `baxter_bridge` introduces a potential point of failure if ROS 2 networking paradigms shift in future releases.
*   **MoveIt 2 Migration Effort:** Tuning MoveIt 2 controllers and kinematics for a 7-DOF dual-arm robot can be complex and time-consuming.

## 6. Recommendation
**Recommendation:** Proceed with a **phased migration** to a ROS 2 Jazzy repository.

A full rewrite in one go is unnecessary and risky. I recommend the following phased approach to meet the goals for students and external users quickly:

1.  **Phase 1: Core & Bridge (Hardware First):** Port `baxter_common`, integrate a `baxter_bridge`, and provide a Docker Dev Container. This immediately unblocks university students and researchers who need to command the real robot using ROS 2 Jazzy pub/sub.
2.  **Phase 2: Simulation (Gazebo Harmonic):** Build the native ROS 2 simulation using `gz_ros2_control`. This unblocks users without hardware.
3.  **Phase 3: Python SDK & MoveIt 2:** Port the user-friendly `baxter_interface` (`rclpy`) and create the `baxter_moveit_config` for advanced motion planning.