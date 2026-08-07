"""
slam_bringup.launch.py

Starts (no encoders / no odometry hardware):
  1. base_link -> laser_link   static transform (your lidar's real mount offset)
  2. odom -> base_link         identity transform (placeholder; slam_toolbox's
                                scan matcher corrects the map->odom part on top
                                of this so mapping still works)
  3. slam_toolbox              online_async mapping node

EDIT THE LIDAR OFFSET ARGS BELOW to match where your YDLidar X2 is physically
mounted on the robot before running this.

Usage:
  ros2 launch bot_bringup slam_bringup.launch.py
  ros2 launch bot_bringup slam_bringup.launch.py lidar_x:=0.05 lidar_yaw:=3.1416
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ---- Lidar mount offset relative to base_link (EDIT THESE) ----
    # Units: meters for x/y/z, radians for yaw (roll/pitch left at 0 = flat mount)
    lidar_x = LaunchConfiguration('lidar_x')
    lidar_y = LaunchConfiguration('lidar_y')
    lidar_z = LaunchConfiguration('lidar_z')
    lidar_yaw = LaunchConfiguration('lidar_yaw')

    declare_args = [
        DeclareLaunchArgument('lidar_x', default_value='0.0',
                               description='Lidar X offset from base_link (m)'),
        DeclareLaunchArgument('lidar_y', default_value='0.0',
                               description='Lidar Y offset from base_link (m)'),
        DeclareLaunchArgument('lidar_z', default_value='0.10',
                               description='Lidar Z offset / mount height (m)'),
        DeclareLaunchArgument('lidar_yaw', default_value='0.0',
                               description='Lidar yaw offset (rad); use 3.14159 if mounted backwards'),
    ]

    # 1) base_link -> laser_link (real physical offset — EDIT defaults above)
    base_to_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser_tf',
        arguments=[lidar_x, lidar_y, lidar_z, lidar_yaw, '0', '0',
                   'base_link', 'laser_link'],
        output='screen',
    )

    # 2) odom -> base_link (identity placeholder — no encoders yet)
    odom_to_base = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='odom_to_base_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
        output='screen',
    )

    # 3) slam_toolbox (online async mapping), using our params file
    slam_params_file = PathJoinSubstitution(
        [FindPackageShare('bot_bringup'), 'config', 'mapper_params_online_async.yaml']
    )

    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('slam_toolbox'), 'launch', 'online_async_launch.py']
            )
        ),
        launch_arguments={'slam_params_file': slam_params_file}.items(),
    )

    return LaunchDescription(declare_args + [
        base_to_laser,
        odom_to_base,
        slam_toolbox_launch,
    ])
