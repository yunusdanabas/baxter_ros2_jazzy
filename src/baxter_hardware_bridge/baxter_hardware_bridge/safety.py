#!/usr/bin/env python3
"""Safety state checker for Baxter hardware bridge.

Reads /robot/state (baxter_core_msgs/AssemblyState) and provides
a gate that rejects motion unless the robot is ready, enabled,
not stopped, not in error, not e-stopped, and the topic has
exactly one publisher.

This module is importable by the action shim and also runnable
standalone as a CLI status tool.
"""

from typing import Optional

import rclpy
from baxter_core_msgs.msg import AssemblyState
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

ROBOT_STATE_TOPIC = "/robot/state"
STATE_TIMEOUT_SEC = 2.0


class SafetyStateChecker:
    """Wraps /robot/state subscription and exposes is_safe_for_motion()."""

    ESTOP_BUTTON_UNPRESSED = 0
    ESTOP_BUTTON_PRESSED = 1
    ESTOP_BUTTON_UNKNOWN = 2
    ESTOP_BUTTON_RELEASED = 3

    def __init__(self, node: Node, topic: str = ROBOT_STATE_TOPIC, callback_group=None):
        self._node = node
        self._topic = topic
        self._latest: Optional[AssemblyState] = None
        self._stamp_ns: int = 0

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        node.create_subscription(
            AssemblyState, topic, self._cb, qos, callback_group=callback_group
        )

    def _cb(self, msg: AssemblyState) -> None:
        self._latest = msg
        self._stamp_ns = self._node.get_clock().now().nanoseconds

    def get_state(self) -> Optional[AssemblyState]:
        return self._latest

    def is_stale(self, timeout_sec: float = STATE_TIMEOUT_SEC) -> bool:
        if self._latest is None:
            return True
        elapsed = (self._node.get_clock().now().nanoseconds - self._stamp_ns) / 1e9
        return elapsed > timeout_sec

    def publisher_count(self) -> int:
        return self._node.count_publishers(self._topic)

    def is_safe_for_motion(self) -> bool:
        """True only when robot is ready, enabled, not stopped, no error, no e-stop,
        and exactly one node is publishing the state we are reading."""
        # A mock or an orphaned shim publishing "safe" alongside the real
        # disabled robot makes this gate accept a goal it must reject (I18 F1,
        # hit twice in one session). Whose message we got is unknowable, so
        # refuse while the topic is contested.
        if self.publisher_count() != 1:
            return False
        if self.is_stale():
            return False
        s = self._latest
        if s is None:
            return False
        if not s.ready:
            return False
        if not s.enabled:
            return False
        if s.stopped:
            return False
        if s.error:
            return False
        if s.estop_button in (
            self.ESTOP_BUTTON_PRESSED,
            self.ESTOP_BUTTON_UNKNOWN,
        ):
            return False
        return True

    def describe(self) -> str:
        count = self.publisher_count()
        contested = (
            ""
            if count == 1
            else f" CONTESTED: {count} publishers on {self._topic}, expected 1"
        )
        s = self._latest
        if s is None:
            return f"NO {self._topic} MESSAGE RECEIVED{contested}"
        stale = " (STALE)" if self.is_stale() else ""
        return (
            f"ready={s.ready} enabled={s.enabled} stopped={s.stopped}"
            f" error={s.error} estop_button={s.estop_button}"
            f" estop_source={s.estop_source}{stale}{contested}"
        )


def main() -> None:
    rclpy.init()
    node = rclpy.create_node("baxter_safety_check")
    checker = SafetyStateChecker(node)
    node.get_logger().info(
        "Waiting for /robot/state... (Ctrl+C to quit)"
    )
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.2)
            safe = checker.is_safe_for_motion()
            state = checker.get_state()
            if state is not None:
                node.get_logger().info(
                    f"safe_for_motion={safe}  {checker.describe()}"
                )
            else:
                node.get_logger().warn(
                    f"safe_for_motion=False  {checker.describe()}"
                )
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
