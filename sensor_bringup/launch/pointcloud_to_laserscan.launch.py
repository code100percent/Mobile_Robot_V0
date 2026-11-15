import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from mobile_nav_bringup.robot_config import load_robot_params


def _make_converter(context):
    config = load_robot_params(
        LaunchConfiguration('robot_params_file').perform(context))
    lidar_z = float(config['sensor_mounts']['lidar']['xyz'][2])
    lidar_roll, lidar_pitch, _ = (
        float(value) for value in config['sensor_mounts']['lidar']['rpy'])
    if abs(lidar_roll) > 1e-6 or abs(lidar_pitch) > 1e-6:
        raise ValueError(
            'LiDAR roll/pitch must be zero for height filtering in its source frame; '
            'use a valid base_link TF target for a tilted sensor')
    min_height = float(LaunchConfiguration('min_height').perform(context))
    max_height = float(LaunchConfiguration('max_height').perform(context))
    if min_height >= max_height:
        raise ValueError('min_height must be less than max_height')

    return [Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        remappings=[
            ('cloud_in', '/unilidar/cloud'),
            ('scan', '/scan'),
        ],
        parameters=[{
            # Empty target_frame keeps conversion in the cloud frame and does
            # not wait for a base_link transform to filter incoming clouds.
            'target_frame': '',
            # Height inputs are measured from the base ground plane; convert
            # them to the LiDAR frame using the centralized mount height.
            'min_height': min_height - lidar_z,
            'max_height': max_height - lidar_z,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 20.0,
            'use_inf': True,
            'inf_epsilon': 1.0,
            'queue_size': 10,
        }],
        output='screen',
    )]


def generate_launch_description():
    config_path = os.path.join(
        get_package_share_directory('mobile_nav_bringup'),
        'config',
        'robot_params.yaml',
    )
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_params_file',
            default_value=config_path,
            description='Shared robot config containing the LiDAR mount height.',
        ),
        DeclareLaunchArgument(
            'min_height',
            default_value='0.15',
            description='Minimum accepted point height above the base ground plane (m).',
        ),
        DeclareLaunchArgument(
            'max_height',
            default_value='1.0',
            description='Maximum accepted point height above the base ground plane (m).',
        ),
        OpaqueFunction(function=_make_converter),
    ])
