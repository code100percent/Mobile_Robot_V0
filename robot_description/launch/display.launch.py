import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # Get robot_description package share directory
    pkg_share = get_package_share_directory('robot_description')

    # Path to URDF
    default_urdf_path = os.path.join(
        pkg_share,
        'urdf',
        'mobile_robot.urdf'
    )

    # Launch configuration
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Read URDF file
    with open(default_urdf_path, 'r') as urdf_file:
        robot_description = urdf_file.read()

    # Declare use_sim_time argument
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description,
        }],
    )
    joint_state_publisher_node = Node(
    package='joint_state_publisher_gui',
    executable='joint_state_publisher_gui',
    name='joint_state_publisher_gui',
    output='screen',
    )

    # RViz
    rviz_config = os.path.join(
        pkg_share,
        'rviz2',
        'mobile_robot.rviz'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([
        declare_use_sim_time,
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node,
    ])

