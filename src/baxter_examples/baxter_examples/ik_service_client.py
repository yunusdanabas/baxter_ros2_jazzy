#!/usr/bin/env python3

"""ROS 2 port of the Baxter RSDK inverse kinematics example.

The ROS 1 script called ``ExternalTools/<limb>/PositionKinematicsNode/IKService``
(``baxter_core_msgs/SolvePositionIK``), which only exists on the robot. Here the
same question is asked of MoveIt's ``/compute_ik`` instead, so it works against
the simulator with no hardware and no controllers -- it only queries, it never moves.
"""

import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from moveit_msgs.msg import MoveItErrorCodes, PositionIKRequest
from moveit_msgs.srv import GetPositionIK
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

# The seven arm joints, in MoveIt/SRDF chain order.
ARM_JOINTS = ("s0", "s1", "e0", "e1", "w0", "w1", "w2")

# Seed poses carried over verbatim from the ROS 1 example (expressed in `base`).
DEFAULT_POSES = {
    "left": (
        (0.657579481614, 0.851981417433, 0.0388352386502),
        (-0.366894936773, 0.885980397775, 0.108155782462, 0.262162481772),
    ),
    "right": (
        (0.656982770038, -0.852598021641, 0.0388609422173),
        (0.367048116303, 0.885911751787, -0.108908281936, 0.261868353356),
    ),
}


class IKServiceClient(Node):
    def __init__(self) -> None:
        super().__init__("ik_service_client")
        self.declare_parameter("limb", "left")
        self.declare_parameter("frame", "base")
        self.declare_parameter("timeout", 1.0)
        self.declare_parameter("avoid_collisions", True)

        self._limb = self.get_parameter("limb").value
        if self._limb not in DEFAULT_POSES:
            raise RuntimeError(
                f"Unsupported limb {self._limb!r}; choose from {sorted(DEFAULT_POSES)}"
            )

        (x, y, z), (qx, qy, qz, qw) = DEFAULT_POSES[self._limb]
        for name, default in (
            ("x", x), ("y", y), ("z", z),
            ("qx", qx), ("qy", qy), ("qz", qz), ("qw", qw),
        ):
            self.declare_parameter(name, default)

        self._frame = self.get_parameter("frame").value
        self._client = self.create_client(GetPositionIK, "/compute_ik")

    def _target_pose(self) -> Pose:
        pose = Pose()
        pose.position.x = self.get_parameter("x").value
        pose.position.y = self.get_parameter("y").value
        pose.position.z = self.get_parameter("z").value
        pose.orientation.x = self.get_parameter("qx").value
        pose.orientation.y = self.get_parameter("qy").value
        pose.orientation.z = self.get_parameter("qz").value
        pose.orientation.w = self.get_parameter("qw").value
        return pose

    def run(self) -> None:
        if not self._client.wait_for_service(timeout_sec=15.0):
            raise RuntimeError("MoveIt IK service not available: /compute_ik")

        pose = self._target_pose()
        self.get_logger().info(
            f"Requesting IK solution for {self._limb} arm in {self._frame}: "
            f"position=({pose.position.x:.3f}, {pose.position.y:.3f}, {pose.position.z:.3f}) "
            f"orientation=({pose.orientation.x:.3f}, {pose.orientation.y:.3f}, "
            f"{pose.orientation.z:.3f}, {pose.orientation.w:.3f})"
        )

        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = self._frame
        pose_stamped.pose = pose

        request = GetPositionIK.Request()
        ik: PositionIKRequest = request.ik_request
        ik.group_name = f"{self._limb}_arm"
        ik.ik_link_name = f"{self._limb}_gripper"
        ik.pose_stamped = pose_stamped
        # An empty diff state makes move_group seed from the live robot state.
        ik.robot_state.is_diff = True
        ik.avoid_collisions = self.get_parameter("avoid_collisions").value
        timeout = self.get_parameter("timeout").value
        ik.timeout.sec = int(timeout)
        ik.timeout.nanosec = int((timeout - int(timeout)) * 1e9)

        future = self._client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=30.0)
        if not future.done():
            raise RuntimeError("Timed out waiting for /compute_ik")

        response = future.result()
        if response.error_code.val != MoveItErrorCodes.SUCCESS:
            raise RuntimeError(
                "INVALID POSE - No Valid Joint Solution Found "
                f"(MoveItErrorCodes {response.error_code.val})"
            )

        solution = dict(
            zip(
                response.solution.joint_state.name,
                response.solution.joint_state.position,
            )
        )
        joints = [f"{self._limb}_{suffix}" for suffix in ARM_JOINTS]
        missing = [name for name in joints if name not in solution]
        if missing:
            raise RuntimeError(f"IK solution is missing joints: {missing}")

        self.get_logger().info("SUCCESS - Valid Joint Solution Found:")
        for name in joints:
            self.get_logger().info(f"  {name}: {solution[name]:+.4f} rad")


def main() -> None:
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = IKServiceClient()
    exit_code = 0
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().warning("Interrupted")
        exit_code = 1
    except Exception as error:
        node.get_logger().error(str(error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
