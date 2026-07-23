"""Shared executor construction for hardware bridge nodes.

Production entrypoints and dry_run_test must use the same executor type so
blocking action execute callbacks cannot starve cancel/safety subscriptions.
"""

from rclpy.executors import MultiThreadedExecutor

# Enough threads for: execute callback, cancel, joint_states, robot/state, timers.
DEFAULT_SHIM_EXECUTOR_THREADS = 4


def make_shim_executor(num_threads: int = DEFAULT_SHIM_EXECUTOR_THREADS) -> MultiThreadedExecutor:
    return MultiThreadedExecutor(num_threads=num_threads)
