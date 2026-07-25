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
  source scripts/baxter_env.sh && python3 py_bridge.py
  python3 py_bridge.py --master http://<robot>:11311 --ip <this-host-on-robot-net>
"""

import argparse
import atexit
import os
import queue
import socket
import struct
import threading
import time
import xmlrpc.client
from typing import Callable, Optional
from urllib.parse import urlparse
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from baxter_core_msgs.msg import AssemblyState, JointCommand
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

# Reject absurd TCPROS frames (corrupt length / DoS).
MAX_TCPROS_FRAME_BYTES = 16 * 1024 * 1024
# Drop slow ROS 1 peers rather than block the ROS 2 callback path.
TCPROS_SEND_TIMEOUT_SEC = 0.5
# Bound the inbound-subscriber handshake so a silent peer cannot leak a thread.
TCPROS_HEADER_TIMEOUT_SEC = 10.0
ROS2_PUBLISH_QUEUE_SIZE = 200
ROS2_PUBLISH_TIMER_SEC = 0.01
# How far the robot's joint_states stamps may sit from this host's clock before
# we say so. Well inside MoveIt's own tolerance, but past anything routine.
CLOCK_SKEW_WARN_SEC = 0.5

# Real ROS 1 md5sum + message definition per type we publish. rosbag stores the
# publisher's connection header and nothing else, so advertising md5sum "*" with
# no definition records a topic that cannot be deserialised afterwards -- it cost
# us the joint_command payload in the I12 bag (F23). Values are `rosmsg md5` and
# the .msg text from baxter-noetic:n07, the image the robot path uses.
# Only the publish side needs these: the wildcard on the subscribe side is what
# lets the bridge take any type with no schema, and it stays.
ROS1_MSG_META: dict[str, tuple[str, str]] = {
    "baxter_core_msgs/JointCommand": (
        "19bfec8434dd568ab3c633d187c36f2e",
        "int32 mode\n"
        "float64[] command\n"
        "string[]  names\n"
        "\n"
        "int32 POSITION_MODE=1\n"
        "int32 VELOCITY_MODE=2\n"
        "int32 TORQUE_MODE=3\n"
        "int32 RAW_POSITION_MODE=4\n",
    ),
    "std_msgs/Float64": ("fdb28210bfa9d7c91146260178d9a584", "float64 data\n"),
    # Not published today; here because they are the rest of the Baxter command
    # surface (gripper/enable topics) and cost one line each.
    "std_msgs/Bool": ("8b94c1b53db61fb6aed406028ad6332a", "bool data\n"),
    "std_msgs/Empty": ("d41d8cd98f00b204e9800998ecf8427e", "\n"),
}


# ─── TCPROS protocol ─────────────────────────────────────────────

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("TCPROS connection closed")
        buf += chunk
    return buf


def _recv_frame(sock: socket.socket) -> bytes:
    length = struct.unpack("<I", _recv_exact(sock, 4))[0]
    if length > MAX_TCPROS_FRAME_BYTES:
        raise ValueError(f"TCPROS frame too large: {length} bytes")
    return _recv_exact(sock, length)


def _parse_tcpros_header(data: bytes) -> dict:
    fields = {}
    i = 0
    while i < len(data):
        flen = struct.unpack("<I", data[i:i + 4])[0]
        i += 4
        field = data[i:i + flen].decode("utf-8", errors="replace")
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
    s = buf[off:off + n].decode("utf-8", errors="replace")
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
    # ROS 1 std_msgs/Header is: uint32 seq, time stamp, string frame_id.
    # ROS 2 dropped seq — read and discard it, or every later field misaligns.
    off += 4
    secs, nsecs, off = _read_time(data, off)
    msg.header.stamp.sec = secs
    msg.header.stamp.nanosec = nsecs
    msg.header.frame_id, off = _read_string(data, off)
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
    return (
        _ser_int32(msg.mode)
        + _ser_float64_array(list(msg.command))
        + _ser_string_array(list(msg.names))
    )


def ser_float64_msg(msg: Float64) -> bytes:
    return _ser_float64(msg.data)


def detect_local_ip(master_uri: str) -> str:
    """Pick the local interface that routes toward the ROS 1 master host."""
    parsed = urlparse(master_uri)
    host = parsed.hostname
    port = parsed.port or 11311
    if not host:
        raise SystemExit(f"Cannot parse host from --master URI: {master_uri}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((host, port))
        return sock.getsockname()[0]
    except OSError as exc:
        raise SystemExit(
            f"Could not auto-detect local IP toward {host}:{port} ({exc}). "
            "Pass --ip explicitly."
        ) from exc
    finally:
        sock.close()


# ─── ROS 1 Slave API (XML-RPC) ────────────────────────────────────
# Real ROS 1 nodes negotiate TCPROS via each other's Slave API: a publisher's
# registerSubscriber reply gives XML-RPC URIs, not TCPROS addresses — you
# then call requestTopic on that URI to get the actual host/port to connect
# to. This class is that Slave API for our one bridge "node".
# ponytail: only requestTopic/publisherUpdate/getPid/getMasterUri are
# implemented — enough for TCPROS negotiation, not a full slave API.

class _QuietHandler(SimpleXMLRPCRequestHandler):
    def log_message(self, *args):
        pass


class SlaveApi:
    def __init__(self, ip: str, master_uri: str):
        self.ip = ip
        self.master_uri = master_uri
        self.pub_ports: dict[str, tuple[str, int]] = {}
        self._publisher_update_handlers: dict[str, list[Callable]] = {}
        self._server = SimpleXMLRPCServer(
            (ip, 0),
            requestHandler=_QuietHandler,
            logRequests=False,
            allow_none=True,
        )
        self.port = self._server.server_address[1]
        self._server.register_function(self.requestTopic, "requestTopic")
        self._server.register_function(self.publisherUpdate, "publisherUpdate")
        self._server.register_function(self.getPid, "getPid")
        self._server.register_function(self.getMasterUri, "getMasterUri")
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        # Registrations outlive the process on the ROS 1 master otherwise: it
        # keeps trying to reach our dead XML-RPC endpoint, and short-lived
        # scripts accumulate as phantom nodes in `rosnode list`.
        self._registered: list = []
        atexit.register(self.unregister_all)

    def track(self, endpoint) -> None:
        self._registered.append(endpoint)

    def unregister_all(self) -> None:
        for endpoint in self._registered:
            try:
                endpoint.stop()
            except Exception:
                pass
        self._registered = []

    @property
    def uri(self) -> str:
        return f"http://{self.ip}:{self.port}/"

    def register_publisher_port(self, topic: str, port: int) -> None:
        self.pub_ports[topic] = (self.ip, port)

    def register_publisher_update_handler(self, topic: str, handler: Callable) -> None:
        self._publisher_update_handlers.setdefault(topic, []).append(handler)

    def requestTopic(self, caller_id, topic, protocols):
        if topic not in self.pub_ports:
            return (0, f"not publishing {topic}", [])
        host, port = self.pub_ports[topic]
        return (1, "", ["TCPROS", host, port])

    def publisherUpdate(self, caller_id, topic, publishers):
        for handler in self._publisher_update_handlers.get(topic, []):
            try:
                handler(list(publishers))
            except Exception:
                pass
        return (1, "", 0)

    def getPid(self, caller_id):
        return (1, "", os.getpid())

    def getMasterUri(self, caller_id):
        return (1, "", self.master_uri)


# ─── ROS 1 subscriber (TCPROS client) ────────────────────────────

class ROS1Subscriber:
    """Connects to a ROS 1 publisher via TCPROS and calls callback on each message."""

    def __init__(
        self,
        master_uri: str,
        topic: str,
        msg_type: str,
        caller_id: str,
        slave: "SlaveApi",
        callback,
        deserializer,
        log_fn: Optional[Callable[[str], None]] = None,
    ):
        self.master_uri = master_uri
        self.topic = topic
        self.msg_type = msg_type
        self.caller_id = caller_id
        self.slave = slave
        self.callback = callback
        self.deserializer = deserializer
        self._log = log_fn or (lambda _msg: None)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        # One socket and one receive thread per publisher of this topic.
        self._socks: dict = {}
        self._threads: dict = {}
        self._pub_uris: set = set()
        self._sock_lock = threading.Lock()
        self._last_deser_warn = 0.0
        slave.register_publisher_update_handler(topic, self._on_publisher_update)

    def start(self):
        self._running = True
        self.slave.track(self)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._close_sock()
        # The in-loop unregister only runs on a clean receive-loop exit; on an
        # abrupt process exit the master would keep a stale subscriber entry.
        try:
            master = xmlrpc.client.ServerProxy(self.master_uri)
            master.unregisterSubscriber(self.caller_id, self.topic, self.slave.uri)
        except Exception:
            pass

    def _close_sock(self) -> None:
        with self._sock_lock:
            socks = list(self._socks.values())
            self._socks.clear()
        for sock in socks:
            try:
                sock.close()
            except Exception:
                pass

    def _on_publisher_update(self, _publishers) -> None:
        # Force every receive loop to drop and re-negotiate TCPROS. The poll in
        # _run picks the new publisher set up on its next pass.
        self._close_sock()

    def _run(self):
        # A ROS 1 topic may have several publishers, and they carry different
        # data: /robot/joint_states is /realtime_loop (head + arm joints) *and*
        # /end_effector_publisher (gripper joints). Connecting to only the first
        # silently drops the rest -- that cost us the gripper joints entirely,
        # which in turn left MoveIt without a complete robot state. So keep one
        # receive thread per publisher and re-poll for new ones.
        while self._running:
            try:
                master = xmlrpc.client.ServerProxy(self.master_uri)
                code, msg, pub_uris = master.registerSubscriber(
                    self.caller_id, self.topic, self.msg_type, self.slave.uri
                )
                if code != 1:
                    raise RuntimeError(f"registerSubscriber failed: {msg}")
                with self._sock_lock:
                    self._pub_uris = set(pub_uris)
                for uri in pub_uris:
                    thread = self._threads.get(uri)
                    if thread is None or not thread.is_alive():
                        thread = threading.Thread(
                            target=self._receive_from, args=(uri,), daemon=True
                        )
                        self._threads[uri] = thread
                        thread.start()
            except Exception as exc:
                if self._running:
                    self._log(f"ROS1 sub {self.topic} reconnecting after: {exc}")
            time.sleep(2)

    def _receive_from(self, pub_uri: str):
        """Hold one TCPROS connection to a single publisher of this topic."""
        while self._running:
            with self._sock_lock:
                if pub_uri not in self._pub_uris:
                    return
            sock = None
            try:
                # pub_uri is the publisher's Slave API (XML-RPC) address, not a
                # TCPROS one -- ask it where its TCPROS socket actually is.
                pub = xmlrpc.client.ServerProxy(pub_uri)
                code, msg, proto = pub.requestTopic(
                    self.caller_id, self.topic, [["TCPROS"]]
                )
                if code != 1 or not proto:
                    raise RuntimeError(f"requestTopic failed: {msg}")
                _, pub_host, pub_port = proto

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((pub_host, pub_port))
                header = _build_tcpros_header({
                    "md5sum": "*",
                    "type": self.msg_type,
                    "topic": self.topic,
                    "callerid": self.caller_id,
                })
                sock.sendall(header)
                _parse_tcpros_header(_recv_frame(sock))

                with self._sock_lock:
                    self._socks[pub_uri] = sock

                while self._running:
                    with self._sock_lock:
                        if self._socks.get(pub_uri) is not sock:
                            break
                    data = _recv_frame(sock)
                    try:
                        self.callback(self.deserializer(data))
                    except Exception as exc:
                        now = time.monotonic()
                        if now - self._last_deser_warn > 5.0:
                            self._last_deser_warn = now
                            self._log(
                                f"ROS1 sub {self.topic} deserialize failed: {exc}"
                            )
            except Exception as exc:
                if self._running:
                    self._log(
                        f"ROS1 sub {self.topic} <- {pub_uri} reconnecting after: {exc}"
                    )
                    time.sleep(2)
            finally:
                with self._sock_lock:
                    if self._socks.get(pub_uri) is sock:
                        del self._socks[pub_uri]
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass


# ─── ROS 1 publisher (TCPROS server) ─────────────────────────────

class ROS1Publisher:
    """Registers as a publisher on the ROS 1 master and serves TCPROS to subscribers."""

    def __init__(
        self,
        master_uri: str,
        topic: str,
        msg_type: str,
        caller_id: str,
        slave: "SlaveApi",
        port: int,
        serializer,
    ):
        self.master_uri = master_uri
        self.topic = topic
        self.msg_type = msg_type
        self.caller_id = caller_id
        self.slave = slave
        self.port = port
        self.serializer = serializer
        self._subscribers: list[socket.socket] = []
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        self._running = True
        self.slave.track(self)
        self.slave.register_publisher_port(self.topic, self.port)
        master = xmlrpc.client.ServerProxy(self.master_uri)
        code, msg, _ = master.registerPublisher(
            self.caller_id, self.topic, self.msg_type, self.slave.uri
        )
        if code != 1:
            raise RuntimeError(f"registerPublisher failed: {msg}")
        threading.Thread(target=self._listen, daemon=True).start()

    def stop(self):
        """Unregister from the ROS 1 master so Baxter is not left with a stale
        publisher entry that only a roscore restart clears."""
        self._running = False
        try:
            master = xmlrpc.client.ServerProxy(self.master_uri)
            master.unregisterPublisher(self.caller_id, self.topic, self.slave.uri)
        except Exception:
            pass
        with self._lock:
            subscribers, self._subscribers = self._subscribers, []
        for sock in subscribers:
            try:
                sock.close()
            except Exception:
                pass

    def _listen(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(5)
        srv.settimeout(1)
        while self._running:
            try:
                conn, _ = srv.accept()
                threading.Thread(
                    target=self._handle_sub, args=(conn,), daemon=True
                ).start()
            except socket.timeout:
                continue
        srv.close()

    def _handle_sub(self, conn: socket.socket):
        try:
            # Bound the header wait too, or a peer that connects and never
            # sends leaks this thread forever.
            conn.settimeout(TCPROS_HEADER_TIMEOUT_SEC)
            hdr = _parse_tcpros_header(_recv_frame(conn))
            del hdr  # the subscriber's half; rospy validates ours, not vice versa
            md5sum, msg_def = ROS1_MSG_META.get(self.msg_type, ("*", ""))
            resp = _build_tcpros_header({
                "md5sum": md5sum,
                "type": self.msg_type,
                "topic": self.topic,
                "message_definition": msg_def,
                "callerid": self.caller_id,
            })
            conn.settimeout(TCPROS_SEND_TIMEOUT_SEC)
            conn.sendall(resp)
            with self._lock:
                self._subscribers.append(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def publish(self, msg):
        data = self.serializer(msg)
        if len(data) > MAX_TCPROS_FRAME_BYTES:
            raise ValueError(f"serialized message too large: {len(data)}")
        framed = struct.pack("<I", len(data)) + data
        with self._lock:
            subscribers = list(self._subscribers)
        dead: list[socket.socket] = []
        for sock in subscribers:
            try:
                sock.settimeout(TCPROS_SEND_TIMEOUT_SEC)
                sock.sendall(framed)
            except Exception:
                dead.append(sock)
        if dead:
            with self._lock:
                self._subscribers = [s for s in self._subscribers if s not in dead]
            for sock in dead:
                try:
                    sock.close()
                except Exception:
                    pass


# ─── Bridge node ─────────────────────────────────────────────────

class BaxterPyBridge(Node):
    def __init__(self, master_uri: str, local_ip: str):
        super().__init__("baxter_py_bridge")
        self.master_uri = master_uri
        self.local_ip = local_ip
        self.base_port = 30000
        self._ros2_queue: queue.Queue = queue.Queue(maxsize=ROS2_PUBLISH_QUEUE_SIZE)

        qos10 = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        qos1 = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ROS 2 publishers (ROS 1 -> ROS 2)
        self.state_pub = self.create_publisher(AssemblyState, "/robot/state", qos10)
        self.js_pub = self.create_publisher(JointState, "/robot/joint_states", qos10)

        # Shared ROS 1 Slave API (XML-RPC) — used as caller_api for every
        # registerPublisher/registerSubscriber call below.
        self.slave = SlaveApi(local_ip, master_uri)

        # ROS 1 publishers (ROS 2 -> ROS 1)
        self.ros1_pubs: dict[str, ROS1Publisher] = {}
        for side in ("left", "right"):
            jc_pub = ROS1Publisher(
                master_uri,
                f"/robot/limb/{side}/joint_command",
                "baxter_core_msgs/JointCommand",
                f"/py_bridge_{side}_jc",
                self.slave,
                self._next_port(),
                ser_joint_command,
            )
            sr_pub = ROS1Publisher(
                master_uri,
                f"/robot/limb/{side}/set_speed_ratio",
                "std_msgs/Float64",
                f"/py_bridge_{side}_sr",
                self.slave,
                self._next_port(),
                ser_float64_msg,
            )
            to_pub = ROS1Publisher(
                master_uri,
                f"/robot/limb/{side}/joint_command_timeout",
                "std_msgs/Float64",
                f"/py_bridge_{side}_to",
                self.slave,
                self._next_port(),
                ser_float64_msg,
            )
            self.ros1_pubs[f"/robot/limb/{side}/joint_command"] = jc_pub
            self.ros1_pubs[f"/robot/limb/{side}/set_speed_ratio"] = sr_pub
            self.ros1_pubs[f"/robot/limb/{side}/joint_command_timeout"] = to_pub

        # ROS 2 subscribers (ROS 2 -> ROS 1)
        for side in ("left", "right"):
            self.create_subscription(
                JointCommand,
                f"/robot/limb/{side}/joint_command",
                lambda msg, t=f"/robot/limb/{side}/joint_command": self._ros2_to_ros1(
                    t, msg
                ),
                qos1,
            )
            self.create_subscription(
                Float64,
                f"/robot/limb/{side}/set_speed_ratio",
                lambda msg, t=f"/robot/limb/{side}/set_speed_ratio": self._ros2_to_ros1(
                    t, msg
                ),
                qos1,
            )
            self.create_subscription(
                Float64,
                f"/robot/limb/{side}/joint_command_timeout",
                lambda msg, t=f"/robot/limb/{side}/joint_command_timeout": (
                    self._ros2_to_ros1(t, msg)
                ),
                qos1,
            )

        # ROS 1 subscribers (ROS 1 -> ROS 2) — enqueue for main-thread publish
        log_fn = lambda m: self.get_logger().warn(m, throttle_duration_sec=5.0)
        self.ros1_subs: list[ROS1Subscriber] = []
        self.ros1_subs.append(
            ROS1Subscriber(
                master_uri,
                "/robot/state",
                "baxter_core_msgs/AssemblyState",
                "/py_bridge_state",
                self.slave,
                lambda msg: self._enqueue_ros2(self.state_pub, msg),
                deser_assembly_state,
                log_fn=log_fn,
            )
        )
        self.ros1_subs.append(
            ROS1Subscriber(
                master_uri,
                "/robot/joint_states",
                "sensor_msgs/JointState",
                "/py_bridge_js",
                self.slave,
                lambda msg: self._enqueue_ros2(self.js_pub, msg),
                deser_joint_state,
                log_fn=log_fn,
            )
        )

        self.create_timer(ROS2_PUBLISH_TIMER_SEC, self._flush_ros2_queue)

    def _next_port(self) -> int:
        self.base_port += 1
        return self.base_port

    def _enqueue_ros2(self, publisher, msg) -> None:
        try:
            self._ros2_queue.put_nowait((publisher, msg))
        except queue.Full:
            try:
                self._ros2_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._ros2_queue.put_nowait((publisher, msg))
            except queue.Full:
                self.get_logger().warn(
                    "ROS 2 publish queue full; dropping bridged message",
                    throttle_duration_sec=5.0,
                )

    def _flush_ros2_queue(self) -> None:
        while True:
            try:
                publisher, msg = self._ros2_queue.get_nowait()
            except queue.Empty:
                break
            if publisher is self.js_pub and isinstance(msg, JointState):
                self._keep_robot_stamp(msg)
            publisher.publish(msg)

    def _keep_robot_stamp(self, msg: JointState) -> None:
        """Publish the robot's own sample time, not bridge receive time.

        Overwriting it destroyed the only sample-time reference the recordings
        had and made cross-bag latency work impossible (F14). Nothing downstream
        needs it to be "now": the action shim measures staleness from its own
        receive time, not from this stamp.
        """
        stamp_ns = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
        if stamp_ns == 0:
            # A ROS 1 peer that never stamped. Receive time is still better
            # than 1970 for anything time-ordered downstream.
            msg.header.stamp = self.get_clock().now().to_msg()
            return
        # The robot's clock and this host's are independent. If they drift,
        # MoveIt quietly discards the state as out of date and TF lookups fail,
        # which is expensive to diagnose with the robot in front of you.
        skew_sec = (self.get_clock().now().nanoseconds - stamp_ns) / 1e9
        if abs(skew_sec) > CLOCK_SKEW_WARN_SEC:
            self.get_logger().warn(
                f"/robot/joint_states stamps are {skew_sec:+.2f}s from this "
                f"host's clock; MoveIt will treat them as stale. Check that the "
                f"robot and this host agree on the time (NTP).",
                throttle_duration_sec=30.0,
            )

    def _ros2_to_ros1(self, topic: str, msg):
        pub = self.ros1_pubs.get(topic)
        if pub:
            pub.publish(msg)

    def start_ros1(self):
        for sub in self.ros1_subs:
            sub.start()
        for pub in self.ros1_pubs.values():
            pub.start()
        self.get_logger().info(
            f"Bridge started: master={self.master_uri} ip={self.local_ip}"
        )

    def destroy_node(self):
        for sub in getattr(self, "ros1_subs", []):
            sub.stop()
        for pub in getattr(self, "ros1_pubs", {}).values():
            pub.stop()
        super().destroy_node()


def main():
    parser = argparse.ArgumentParser(description="Pure Python Baxter ROS 1->2 bridge")
    parser.add_argument(
        "--master",
        default=os.environ.get("ROS_MASTER_URI"),
        help="ROS 1 master URI (default: $ROS_MASTER_URI, set by scripts/baxter_env.sh)",
    )
    parser.add_argument(
        "--ip",
        default=os.environ.get("ROS_IP"),
        help="Local IP the robot can reach us on (default: $ROS_IP, else auto-detect)",
    )
    args = parser.parse_args()

    if not args.master:
        parser.error("no --master and $ROS_MASTER_URI unset; "
                     "run 'source scripts/baxter_env.sh' first")

    local_ip = args.ip if args.ip else detect_local_ip(args.master)

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
