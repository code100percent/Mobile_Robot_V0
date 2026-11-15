from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory('mobile_robot_driver'),
        'config', 'odometry.yaml',
    )
    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=default_config),
        Node(
            package='mobile_robot_driver',
            executable='encoder_odometry',
            name='encoder_odometry',
            parameters=[LaunchConfiguration('params_file')],
            output='screen',
        ),
    ])
