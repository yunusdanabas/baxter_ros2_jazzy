#!/usr/bin/env python3
"""Pure Python ROS 1 -> ROS 2 topic bridge for Baxter.

No rospy, no ROS 1 install, no Docker needed.
Uses XML-RPC to discover topics on the ROS 1 master, raw TCPROS to
subscribe, and rclpy to republish as ROS 2.

Bridges these topics (I10 non-motion + I11 motion path):
  ROS 1 -> ROS 2:
    /robot/state               (baxter_core_msgs/AssemblyState)
    /robot/joint_states        (sensor_msgs/JointState)
  ROS 2 -> ROS 1:
    /robot/limb/{side}/joint_command         (baxter_core_msgs/JointCommand)
    /robot/limb/{side}/set_speed_ratio       (std_msgs/Float64)
    /robot/limb/{side}/joint_command_timeout (std_msgs/Float64)

Usage:
  python3 py_bridge.py --master http://192.168.1.224:11311 --ip 192.168.1.108
"""

import argparse
import socket
import struct
import struct as st
import threading
import time
import xmlrpc.client
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from baxter_core_msgs.msg import AssemblyState, JointCommand
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64


# ─── TCPROS protocol ─────────────────────────────────────────────

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("TCPROS connection closed")
        buf += chunk
    return buf

def _parse_tcpros_header(data: bytes) -> dict:
    fields = {}
    i = 0
    while i < len(data):
        flen = struct.unpack("<I", data[i:i+4])[0]
        i += 4
        field = data[i:i+flen].decode("utf-8", errors="replace")
        i += flen
        if "=" in field:
            k, v = field.split("=", 1)
            fields[k] = v
    return fields

def _build_tcpros_header(fields: dict) -> bytes:
    body = b""
    for k, v in fields.items():
        line = f"{k}={v}".encode("utf-8")
        body += struct.pack("<I", len(line)) + line
    return struct.pack("<I", len(body)) + body


# ─── ROS 1 message deserializers (binary format) ─────────────────

def _read_string(buf: bytes, off: int) -> tuple[str, int]:
    n = struct.unpack_from("<I", buf, off)[0]
    off += 4
    s = buf[off:off+n].decode("utf-8", errors="replace")
    return s, off + n

def _read_float64_array(buf: bytes, off: int) -> tuple[list, int]:
    n = struct.unpack_from("<I", buf, off)[0]
    off += 4
    vals = list(struct.unpack_from(f"<{n}d", buf, off))
    return vals, off + n * 8

def _read_float64(buf: bytes, off: int) -> tuple[float, int]:
    v = struct.unpack_from("<d", buf, off)[0]
    return v, off + 8

def _read_bool(buf: bytes, off: int) -> tuple[bool, int]:
    v = struct.unpack_from("<B", buf, off)[0]
    return v != 0, off + 1

def _read_uint8(buf: bytes, off: int) -> tuple[int, int]:
    v = struct.unpack_from("<B", buf, off)[0]
    return v, off + 1

def _read_string_array(buf: bytes, off: int) -> tuple[list, int]:
    n = struct.unpack_from("<I", buf, off)[0]
    off += 4
    vals = []
    for _ in range(n):
        s, off = _read_string(buf, off)
        vals.append(s)
    return vals, off

def _read_time(buf: bytes, off: int) -> tuple[int, int, int]:
    secs = struct.unpack_from("<I", buf, off)[0]
    nsecs = struct.unpack_from("<I", buf, off + 4)[0]
    return secs, nsecs, off + 8


def deser_assembly_state(data: bytes) -> AssemblyState:
    msg = AssemblyState()
    off = 0
    msg.ready, off = _read_bool(data, off)
    msg.enabled, off = _read_bool(data, off)
    msg.stopped, off = _read_bool(data, off)
    msg.error, off = _read_bool(data, off)
    msg.estop_button, off = _read_uint8(data, off)
    msg.estop_source, off = _read_uint8(data, off)
    return msg

def deser_joint_state(data: bytes) -> JointState:
    msg = JointState()
    off = 0
    secs, nsecs, off = _read_time(data, off)
    msg.header.stamp.sec = secs
    msg.header.stamp.nanosec = nsecs
    msg.name, off = _read_string_array(data, off)
    pos, off = _read_float64_array(data, off)
    vel, off = _read_float64_array(data, off)
    eff, off = _read_float64_array(data, off)
    msg.position = pos
    msg.velocity = vel
    msg.effort = eff
    return msg


# ─── ROS 1 message serializers (for ROS 2 -> ROS 1) ──────────────

def _ser_string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<I", len(b)) + b

def _ser_float64_array(vals: list) -> bytes:
    return struct.pack("<I", len(vals)) + struct.pack(f"<{len(vals)}d", *vals)

def _ser_string_array(vals: list) -> bytes:
    out = struct.pack("<I", len(vals))
    for s in vals:
        out += _ser_string(s)
    return out

def _ser_int32(v: int) -> bytes:
    return struct.pack("<i", v)

def _ser_float64(v: float) -> bytes:
    return struct.pack("<d", v)

def ser_joint_command(msg: JointCommand) -> bytes:
    return _ser_int32(msg.mode) + _ser_float64_array(list(msg.command)) + _ser_string_array(list(msg.names))

def ser_float64_msg(msg: Float64) -> bytes:
    return _ser_float64(msg.data)


# ─── ROS 1 subscriber (TCPROS client) ────────────────────────────

class ROS1Subscriber:
    """Connects to a ROS 1 publisher via TCPROS and calls callback on each message."""

    def __init__(self, master_uri: str, topic: str, msg_type: str,
                 caller_id: str, ip: str, port: int, callback, deserializer):
        self.master_uri = master_uri
        self.topic = topic
        self.msg_type = msg_type
        self.caller_id = caller_id
        self.ip = ip
        self.port = port
        self.callback = callback
        self.deserializer = deserializer
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                self._connect_and_receive()
            except Exception as e:
                if self._running:
                    time.sleep(2)  # reconnect after pause

    def _connect_and_receive(self):
        master = xmlrpc.client.ServerProxy(self.master_uri)
        code, msg, pub_uris = master.registerSubscriber(
            self.caller_id, self.topic, self.msg_type,
            f"http://{self.ip}:{self.port}"
        )
        if code != 1:
            raise RuntimeError(f"registerSubscriber failed: {msg}")

        if not pub_uris:
            time.sleep(2)
            return

        pub_uri = pub_uris[0]
        # Parse "http://host:port/"
        pub_host = pub_uri.split("//")[1].split("/")[0].split(":")[0]
        pub_port = int(pub_uri.split("//")[1].split("/")[0].split(":")[1])

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((pub_host, pub_port))

        # Send TCPROS header
        header = _build_tcpros_header({
            "md5sum": "*",
            "type": self.msg_type,
            "topic": self.topic,
            "callerid": self.caller_id,
        })
        sock.sendall(header)

        # Receive header back
        hlen = struct.unpack("<I", _recv_exact(sock, 4))[0]
        hdr_data = _recv_exact(sock, hlen)
        _parse_tcpros_header(hdr_data)

        # Receive messages
        while self._running:
            dlen = struct.unpack("<I", _recv_exact(sock, 4))[0]
            data = _recv_exact(sock, dlen)
            try:
                msg = self.deserializer(data)
                self.callback(msg)
            except Exception:
                pass

        sock.close()

        # Unregister
        try:
            master.unregisterSubscriber(self.caller_id, self.topic)
        except Exception:
            pass


# ─── ROS 1 publisher (TCPROS server) ─────────────────────────────

class ROS1Publisher:
    """Registers as a publisher on the ROS 1 master and serves TCPROS to subscribers."""

    def __init__(self, master_uri: str, topic: str, msg_type: str,
                 caller_id: str, ip: str, port: int, serializer):
        self.master_uri = master_uri
        self.topic = topic
        self.msg_type = msg_type
        self.caller_id = caller_id
        self.ip = ip
        self.port = port
        self.serializer = serializer
        self._subscribers: list[socket.socket] = []
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        self._running = True
        master = xmlrpc.client.ServerProxy(self.master_uri)
        code, msg, _ = master.registerPublisher(
            self.caller_id, self.topic, self.msg_type,
            f"http://{self.ip}:{self.port}"
        )
        if code != 1:
            raise RuntimeError(f"registerPublisher failed: {msg}")
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(5)
        srv.settimeout(1)
        while self._running:
            try:
                conn, _ = srv.accept()
                threading.Thread(target=self._handle_sub, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
        srv.close()

    def _handle_sub(self, conn: socket.socket):
        try:
            hlen = struct.unpack("<I", _recv_exact(conn, 4))[0]
            hdr = _parse_tcpros_header(_recv_exact(conn, hlen))
            resp = _build_tcpros_header({
                "md5sum": "*",
                "type": self.msg_type,
                "topic": self.topic,
                "callerid": self.caller_id,
            })
            conn.sendall(resp)
            with self._lock:
                self._subscribers.append(conn)
        except Exception:
            conn.close()

    def publish(self, msg):
        data = self.serializer(msg)
        framed = struct.pack("<I", len(data)) + data
        with self._lock:
            dead = []
            for i, sock in enumerate(self._subscribers):
                try:
                    sock.sendall(framed)
                except Exception:
                    dead.append(i)
            for i in reversed(dead):
                self._subscribers.pop(i)


# ─── Bridge node ─────────────────────────────────────────────────

class BaxterPyBridge(Node):
    def __init__(self, master_uri: str, local_ip: str):
        super().__init__("baxter_py_bridge")
        self.master_uri = master_uri
        self.local_ip = local_ip
        self.base_port = 30000

        qos10 = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                           history=HistoryPolicy.KEEP_LAST, depth=10)
        qos1 = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                          history=HistoryPolicy.KEEP_LAST, depth=1)

        # ROS 2 publishers (ROS 1 -> ROS 2)
        self.state_pub = self.create_publisher(AssemblyState, "/robot/state", qos10)
        self.js_pub = self.create_publisher(JointState, "/robot/joint_states", qos10)

        # ROS 1 publishers (ROS 2 -> ROS 1)
        self.ros1_pubs: dict[str, ROS1Publisher] = {}
        for side in ("left", "right"):
            jc_pub = ROS1Publisher(master_uri, f"/robot/limb/{side}/joint_command",
                                   "baxter_core_msgs/JointCommand",
                                   f"/py_bridge_{side}_jc", local_ip,
                                   self._next_port(), ser_joint_command)
            sr_pub = ROS1Publisher(master_uri, f"/robot/limb/{side}/set_speed_ratio",
                                   "std_msgs/Float64",
                                   f"/py_bridge_{side}_sr", local_ip,
                                   self._next_port(), ser_float64_msg)
            to_pub = ROS1Publisher(master_uri, f"/robot/limb/{side}/joint_command_timeout",
                                   "std_msgs/Float64",
                                   f"/py_bridge_{side}_to", local_ip,
                                   self._next_port(), ser_float64_msg)
            self.ros1_pubs[f"/robot/limb/{side}/joint_command"] = jc_pub
            self.ros1_pubs[f"/robot/limb/{side}/set_speed_ratio"] = sr_pub
            self.ros1_pubs[f"/robot/limb/{side}/joint_command_timeout"] = to_pub

        # ROS 2 subscribers (ROS 2 -> ROS 1)
        for side in ("left", "right"):
            self.create_subscription(
                JointCommand, f"/robot/limb/{side}/joint_command",
                lambda msg, t=f"/robot/limb/{side}/joint_command": self._ros2_to_ros1(t, msg),
                qos1)
            self.create_subscription(
                Float64, f"/robot/limb/{side}/set_speed_ratio",
                lambda msg, t=f"/robot/limb/{side}/set_speed_ratio": self._ros2_to_ros1(t, msg),
                qos1)
            self.create_subscription(
                Float64, f"/robot/limb/{side}/joint_command_timeout",
                lambda msg, t=f"/robot/limb/{side}/joint_command_timeout": self._ros2_to_ros1(t, msg),
                qos1)

        # ROS 1 subscribers (ROS 1 -> ROS 2)
        self.ros1_subs: list[ROS1Subscriber] = []
        self.ros1_subs.append(ROS1Subscriber(
            master_uri, "/robot/state", "baxter_core_msgs/AssemblyState",
            "/py_bridge_state", local_ip, self._next_port(),
            self._on_state, deser_assembly_state))
        self.ros1_subs.append(ROS1Subscriber(
            master_uri, "/robot/joint_states", "sensor_msgs/JointState",
            "/py_bridge_js", local_ip, self._next_port(),
            self._on_joint_states, deser_joint_state))

    def _next_port(self) -> int:
        self.base_port += 1
        return self.base_port

    def _on_state(self, msg: AssemblyState):
        self.state_pub.publish(msg)

    def _on_joint_states(self, msg: JointState):
        msg.header.stamp = self.get_clock().now().to_msg()
        self.js_pub.publish(msg)

    def _ros2_to_ros1(self, topic: str, msg):
        pub = self.ros1_pubs.get(topic)
        if pub:
            pub.publish(msg)

    def start_ros1(self):
        for sub in self.ros1_subs:
            sub.start()
        for pub in self.ros1_pubs.values():
            pub.start()
        self.get_logger().info(f"Bridge started: master={self.master_uri} ip={self.local_ip}")


def main():
    parser = argparse.ArgumentParser(description="Pure Python Baxter ROS 1->2 bridge")
    parser.add_argument("--master", default="http://192.168.1.224:11311",
                        help="ROS 1 master URI")
    parser.add_argument("--ip", default=None,
                        help="Local IP reachable by Baxter (auto-detect if omitted)")
    args = parser.parse_args()

    local_ip = args.ip
    if not local_ip:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("192.168.1.224", 11311))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = "192.168.1.108"
        finally:
            s.close()

    rclpy.init()
    node = BaxterPyBridge(args.master, local_ip)
    node.start_ros1()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
