"""
Runs on the laptop. Subscribes to the compressed byte stream published by
compress_node.py, decompresses it, deserializes it back into a real
PointCloud2, and republishes it on the normal topic so Point-LIO (or
anything else) can consume it exactly as if it came straight off the lidar.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import UInt8MultiArray
import zstandard as zstd


class DecompressorNode(Node):
    def __init__(self):
        super().__init__('pointcloud_decompressor')

        self.declare_parameter('input_topic', '/unilidar/cloud_compressed')
        self.declare_parameter('output_topic', '/unilidar/cloud')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        self.dctx = zstd.ZstdDecompressor()

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=2,
        )

        self.pub = self.create_publisher(PointCloud2, output_topic, qos)
        self.sub = self.create_subscription(
            UInt8MultiArray, input_topic, self.callback, qos)

        self.get_logger().info(
            f'Decompressing {input_topic} -> {output_topic}'
        )

    def callback(self, msg: UInt8MultiArray):
        try:
            compressed = bytes(msg.data)
            raw = self.dctx.decompress(compressed)
            cloud = deserialize_message(raw, PointCloud2)
            self.pub.publish(cloud)
        except Exception as e:
            # A partially-dropped frame on a lossy link shouldn't kill the
            # node - just skip that frame and keep going.
            self.get_logger().warn(f'Dropped a bad/incomplete frame: {e}')


def main():
    rclpy.init()
    node = DecompressorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
