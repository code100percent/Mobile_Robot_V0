#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from tf2_ros import TransformBroadcaster

from rclpy.qos import qos_profile_sensor_data


# Update TICKS_PER_REV to the number of published encoder counts for one
# complete wheel revolution, including quadrature decoding and gearbox ratio.
WHEEL_DIAMETER = 0.10
WHEEL_TRACK = 0.35
TICKS_PER_REV = 900.0
TICKS_PER_COUNTER_WRAP = 2**32


class EncoderOdometry(Node):
    """Estimate planar odometry from cumulative differential-drive ticks."""

    def __init__(self) -> None:
        super().__init__('encoder_odometry')

        self.declare_parameter('wheel_diameter', WHEEL_DIAMETER)
        self.declare_parameter('wheel_track', WHEEL_TRACK)
        self.declare_parameter('ticks_per_revolution', TICKS_PER_REV)
        self.declare_parameter('ticks_topic', '/wheel_ticks')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')

        self.wheel_diameter = float(
            self.get_parameter('wheel_diameter').value
        )
        self.wheel_track = float(self.get_parameter('wheel_track').value)
        self.ticks_per_revolution = float(
            self.get_parameter('ticks_per_revolution').value
        )
        if self.wheel_diameter <= 0.0:
            raise ValueError('wheel_diameter must be greater than zero')
        if self.wheel_track <= 0.0:
            raise ValueError('wheel_track must be greater than zero')
        if self.ticks_per_revolution <= 0.0:
            raise ValueError('ticks_per_revolution must be greater than zero')

        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        ticks_topic = str(self.get_parameter('ticks_topic').value)
        odom_topic = str(self.get_parameter('odom_topic').value)

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.previous_ticks: tuple[int, int] | None = None
        self.previous_time_ns: int | None = None

        self.odom_publisher = self.create_publisher(Odometry, odom_topic, 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.ticks_subscription = self.create_subscription(
            Int32MultiArray,
            ticks_topic,
            self.ticks_callback,
            qos_profile_sensor_data,
        )

        self.get_logger().info(
            f'Listening on {ticks_topic}; publishing {odom_topic} and '
            f'{self.odom_frame} -> {self.base_frame}'
        )

    @staticmethod
    def _counter_delta(current: int, previous: int) -> int:
        """Return signed delta while accounting for an Int32 counter wrap."""
        return int(
            (current - previous + TICKS_PER_COUNTER_WRAP // 2)
            % TICKS_PER_COUNTER_WRAP
            - TICKS_PER_COUNTER_WRAP // 2
        )

    def ticks_callback(self, message: Int32MultiArray) -> None:
        if len(message.data) < 2:
            self.get_logger().warning(
                'Ignoring /wheel_ticks message: expected left and right counts'
            )
            return

        current_ticks = (int(message.data[0]), int(message.data[1]))
        now = self.get_clock().now()
        now_ns = now.nanoseconds

        if self.previous_ticks is None:
            self.previous_ticks = current_ticks
            self.previous_time_ns = now_ns
            self._publish(now, 0.0, 0.0)
            return

        assert self.previous_time_ns is not None
        left_delta = self._counter_delta(
            current_ticks[0], self.previous_ticks[0]
        )
        right_delta = self._counter_delta(
            current_ticks[1], self.previous_ticks[1]
        )

        meters_per_tick = (
            math.pi * self.wheel_diameter / self.ticks_per_revolution
        )
        left_distance = left_delta * meters_per_tick
        right_distance = right_delta * meters_per_tick
        distance = (left_distance + right_distance) / 2.0
        rotation = (right_distance - left_distance) / self.wheel_track

        old_yaw = self.yaw
        new_yaw = old_yaw + rotation
        if abs(rotation) < 1e-9:
            self.x += distance * math.cos(old_yaw)
            self.y += distance * math.sin(old_yaw)
        else:
            radius = distance / rotation
            self.x += radius * (math.sin(new_yaw) - math.sin(old_yaw))
            self.y -= radius * (math.cos(new_yaw) - math.cos(old_yaw))
        self.yaw = math.atan2(math.sin(new_yaw), math.cos(new_yaw))

        elapsed = (now_ns - self.previous_time_ns) * 1e-9
        linear_velocity = distance / elapsed if elapsed > 0.0 else 0.0
        angular_velocity = rotation / elapsed if elapsed > 0.0 else 0.0

        self.previous_ticks = current_ticks
        self.previous_time_ns = now_ns
        self._publish(now, linear_velocity, angular_velocity)

    def _publish(
        self,
        stamp: rclpy.time.Time,
        linear_velocity: float,
        angular_velocity: float,
    ) -> None:
        stamp_msg = stamp.to_msg()

        odometry = Odometry()
        odometry.header.stamp = stamp_msg
        odometry.header.frame_id = self.odom_frame
        odometry.child_frame_id = self.base_frame
        odometry.pose.pose.position.x = self.x
        odometry.pose.pose.position.y = self.y
        odometry.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odometry.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        odometry.twist.twist.linear.x = linear_velocity
        odometry.twist.twist.angular.z = angular_velocity
        self.odom_publisher.publish(odometry)

        transform = TransformStamped()
        transform.header.stamp = stamp_msg
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation.z = math.sin(self.yaw / 2.0)
        transform.transform.rotation.w = math.cos(self.yaw / 2.0)
        self.tf_broadcaster.sendTransform(transform)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = EncoderOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()