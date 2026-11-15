#!/usr/bin/env bash
# Run from the colcon workspace root, after sourcing ROS.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == "--help" ]]; then
    printf 'Usage: %s [--with-sensors] [colcon build options]\nRun from your workspace root after sourcing ROS.\n' "$0"
    exit 0
fi
paths=("$repo_dir/mobile_robot_driver" "$repo_dir/robot_description"
       "$repo_dir/point_lio_ros2"
       "$repo_dir/unilidar_sdk2/unitree_lidar_ros2/src/unitree_lidar_ros2")
packages=(mobile_robot_driver robot_description point_lio unitree_lidar_ros2)
if [[ "${1:-}" == "--with-sensors" ]]; then
    paths+=("$repo_dir/sensor_bringup")
    packages+=(sensor_bringup)
    shift
fi
if [[ -z "${ROS_DISTRO:-}" ]]; then
    printf 'Source your ROS setup.bash before building.\n' >&2
    exit 1
fi
exec colcon build --base-paths "${paths[@]}" --packages-select "${packages[@]}" \
    --executor sequential "$@"
