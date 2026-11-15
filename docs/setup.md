# Workspace setup

Keep this repository under `<workspace>/src/Mobile_Manipulation_Robot_V0`.
Source exactly one ROS distribution per shell. Docker targets Humble on Ubuntu
22.04; the current host has Jazzy. Do not reuse build/install directories between
distributions. Install ROS separately using its official installation instructions.

## Native core dependencies

With ROS sourced and rosdep initialized, run from the workspace root:

```bash
rosdep install --from-paths \
  src/Mobile_Manipulation_Robot_V0/mobile_robot_driver \
  src/Mobile_Manipulation_Robot_V0/robot_description \
  src/Mobile_Manipulation_Robot_V0/point_lio_ros2 \
  src/Mobile_Manipulation_Robot_V0/unilidar_sdk2/unitree_lidar_ros2/src/unitree_lidar_ros2 \
  --ignore-src -r -y --rosdistro "$ROS_DISTRO" --skip-keys pcl
sudo apt-get install build-essential cmake libpcl-dev libeigen3-dev \
  libusb-1.0-0-dev python3-dev python3-colcon-common-extensions
bash src/Mobile_Manipulation_Robot_V0/scripts/build.sh --symlink-install
```

`pcl` is a legacy vendor manifest key; `libpcl-dev` is installed explicitly.
The Unitree driver links bundled libraries for x86_64 or aarch64. Do not delete
those libraries as generic build artifacts. Other architectures need a compatible SDK.

The Docker image retains the original separate Livox SDK/driver workspace.
The current Point-LIO manifest and CMake file comment out its Livox dependency;
it is therefore not advertised here as a mandatory dependency for native Unitree builds.
Review that dependency again if enabling Livox sensor support.

## Optional sensor integration

`sensor_bringup` requires `depthai_ros_driver_v3`, `pointcloud_to_laserscan`, and
`mobile_nav_bringup`. The latter is a sibling package in the existing workspace,
not part of this repository. Its source origin is not recorded here; a standalone
clone cannot reproduce full sensor bringup without supplying it.

Install/build the camera driver compatible with your ROS distribution and obtain
the matching `mobile_nav_bringup` source. Resolve their dependencies, build them,
and source their install overlay before using:

```bash
bash src/Mobile_Manipulation_Robot_V0/scripts/build.sh --with-sensors --symlink-install
source install/setup.bash
ros2 pkg prefix depthai_ros_driver_v3
ros2 pkg prefix mobile_nav_bringup
ros2 pkg prefix pointcloud_to_laserscan
```

`--with-sensors` installs this repository's launch package; it does not fetch or
build those external dependencies. It still excludes compression and experiments.
