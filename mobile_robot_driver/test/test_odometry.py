"""Exercise odometry math with real ROS message types, without DDS or hardware."""
import math
from types import SimpleNamespace
import unittest

from std_msgs.msg import Int32MultiArray
from mobile_robot_driver.encoder_odometry import EncoderOdometry


class TestOdometry(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.outputs = []
        self.warnings = []
        self.node = SimpleNamespace(
            wheel_diameter=0.10, wheel_track=0.35, ticks_per_revolution=900.0,
            x=0.0, y=0.0, yaw=0.0, previous_ticks=None, previous_time_ns=None,
            get_clock=lambda: SimpleNamespace(
                now=lambda: SimpleNamespace(nanoseconds=self.now)),
            get_logger=lambda: SimpleNamespace(warning=self.warnings.append),
            _counter_delta=EncoderOdometry._counter_delta,
            _publish=lambda stamp, linear, angular: self.outputs.append((linear, angular)),
        )

    def ticks(self, left, right):
        self.now += 1_000_000_000
        EncoderOdometry.ticks_callback(
            self.node, Int32MultiArray(data=[left, right]))

    def test_first_sample_is_baseline(self):
        self.ticks(100, 200)
        self.assertEqual(self.node.x, 0.0)
        self.assertEqual(self.outputs, [(0.0, 0.0)])

    def test_one_revolution_straight(self):
        self.ticks(0, 0)
        self.ticks(900, 900)
        self.assertAlmostEqual(self.node.x, math.pi * 0.10)
        self.assertAlmostEqual(self.node.y, 0.0)
        self.assertAlmostEqual(self.node.yaw, 0.0)
        self.assertAlmostEqual(self.outputs[-1][0], math.pi * 0.10)

    def test_in_place_rotation(self):
        self.ticks(0, 0)
        self.ticks(-90, 90)
        self.assertAlmostEqual(self.node.x, 0.0)
        self.assertAlmostEqual(self.node.y, 0.0)
        self.assertAlmostEqual(self.node.yaw, 2 * math.pi * 0.01 / 0.35)
        self.assertAlmostEqual(self.outputs[-1][1], self.node.yaw)

    def test_signed_counter_wrap_both_directions(self):
        self.assertEqual(EncoderOdometry._counter_delta(-2147483648, 2147483647), 1)
        self.assertEqual(EncoderOdometry._counter_delta(2147483647, -2147483648), -1)

    def test_malformed_sample_does_not_change_baseline(self):
        self.ticks(10, 10)
        EncoderOdometry.ticks_callback(self.node, Int32MultiArray(data=[20]))
        self.assertEqual(self.node.previous_ticks, (10, 10))
        self.assertEqual(len(self.warnings), 1)


if __name__ == '__main__':
    unittest.main()
