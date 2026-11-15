from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    camera_launch = os.path.join(
        get_package_share_directory('depthai_ros_driver_v3'),
        'launch',
        'driver.launch.py',
    )
    lidar_launch = os.path.join(
        get_package_share_directory('unitree_lidar_ros2'),
        'launch.py',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_cmdvel_serial',
            default_value='false',
            description='Start the optional Arduino /cmd_vel serial relay.',
        ),
        DeclareLaunchArgument(
            'motor_serial_port',
            default_value='/dev/ttyUSB0',
            description='Arduino serial device used by cmdvel_serial.',
        ),
        DeclareLaunchArgument(
            'start_lidar',
            default_value='true',
            description=(
                'Start the Unitree driver. Set false when another bringup, '
                'such as mobile_nav_bringup, already owns the LiDAR.'
            ),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(camera_launch),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch),
            condition=IfCondition(LaunchConfiguration('start_lidar')),
        ),
        Node(
            package='mobile_nav_bringup',
            executable='legacy_cmd_vel_serial',
            name='cmd_vel_to_relay',
            parameters=[{
                'port': LaunchConfiguration('motor_serial_port'),
                'topic': '/cmd_vel',
            }],
            condition=IfCondition(LaunchConfiguration('start_cmdvel_serial')),
            output='screen',
        ),
    ])
