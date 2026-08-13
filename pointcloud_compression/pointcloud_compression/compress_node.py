"""
Runs on the Pi. Subscribes to the raw PointCloud2 stream coming from the
unitree_lidar_ros2_node and republishes it as compressed bytes on a
std_msgs/UInt8MultiArray topic, which is much cheaper to push over WiFi.

We don't define a custom .msg for this: we serialize the *entire* PointCloud2
message (header, fields, layout, data - everything) using ROS2's own
serialize_message(), compress that byte blob with zstd, and ship it as a
plain UInt8MultiArray. The decompress_node.py on the other end reverses this
exactly, so nothing about the message content or layout is lost.
"""

import array

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.serialization import serialize_message
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import UInt8MultiArray
import zstandard as zstd


class CompressorNode(Node):
    def __init__(self):
        super().__init__('pointcloud_compressor')

        self.declare_parameter('input_topic', '/unilidar/cloud')
        self.declare_parameter('output_topic', '/unilidar/cloud_compressed')
        # 1 = fastest/lowest CPU, 22 = smallest output/highest CPU.
        # Start low (1-3) on a Pi; raise only if the Pi has CPU headroom
        # (check with the "Check the Pi isn't CPU-starved" step first).
        self.declare_parameter('compression_level', 3)

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        level = self.get_parameter('compression_level').value

        self.cctx = zstd.ZstdCompressor(level=level)

        # Best-effort + small queue: on a lossy/slow link we want to drop
        # stale frames rather than let ROS2 retry-queue them and add lag.
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=2,
        )

        self.pub = self.create_publisher(UInt8MultiArray, output_topic, qos)
        self.sub = self.create_subscription(
            PointCloud2, input_topic, self.callback, qos)

        self._in_bytes = 0
        self._out_bytes = 0
        self._count = 0
        self.create_timer(5.0, self._log_stats)

        self.get_logger().info(
            f'Compressing {input_topic} -> {output_topic} '
            f'(zstd level {level})'
        )

    def callback(self, msg: PointCloud2):
        raw = serialize_message(msg)
        compressed = self.cctx.compress(raw)

        out = UInt8MultiArray()
        out.data = array.array('B', compressed).tolist()
        self.pub.publish(out)

        self._in_bytes += len(raw)
        self._out_bytes += len(compressed)
        self._count += 1

    def _log_stats(self):
        if self._count == 0:
            return
        ratio = self._in_bytes / max(self._out_bytes, 1)
        self.get_logger().info(
            f'{self._count} frames | avg in {self._in_bytes // self._count} B '
            f'-> avg out {self._out_bytes // self._count} B '
            f'| ratio {ratio:.2f}x'
        )
        self._in_bytes = self._out_bytes = self._count = 0


def main():
    rclpy.init()
    node = CompressorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
