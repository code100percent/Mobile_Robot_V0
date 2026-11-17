# PIPER - Mobile Robot (V0)

A ROS 2-based mobile platform integrating autonomous navigation, multi-modal SLAM, 3D LiDAR perception, and robotic arm control.

The repository brings together multiple robotics subsystems, including **Point-LIO 3D LiDAR-Inertial SLAM**, **Cartographer**, **RTAB-Map visual SLAM**, **Nav2 autonomous navigation**, and robotic arm hardware and simulation configurations.


## System Overview

<table>
  <tr>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/267519e9-1fc2-43e2-885e-6ab0c90d2c9e" width="400" alt="Mobile Manipulation Robot"/>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/4ce039ac-ff57-4c08-9bd9-2af368b17a31" width="400" alt="Mobile Manipulation Robot"/>
    </td>
  </tr>
</table>

---

## SLAM & Autonomous Navigation

### 1. 2D SLAM – Cartographer

<p align="center">
  <img src="https://github.com/user-attachments/assets/93cc2f9b-0184-4043-83cc-a4e0e9655074" width="750" alt="Cartographer 2D SLAM Map"/>
</p>

### 2. Autonomous Navigation – Nav2

<p align="center">
  <img src="https://github.com/user-attachments/assets/a813d1f4-5a67-4a75-9b31-16cdb1cbcee8" width="650" alt="Nav2 Autonomous Navigation"/>
</p>

### 3. Visual SLAM – RTAB-Map

<p align="center">
  <img src="https://github.com/user-attachments/assets/ddd771d1-30e1-4299-81af-e666b2a5319e" width="750" alt="RTAB-Map Visual SLAM"/>
</p>

### 4. 3D LiDAR-Inertial SLAM – Point-LIO

<p align="center">
  <img src="https://github.com/user-attachments/assets/de675176-15c4-4204-8e16-633442ad04cd" width="750" alt="Point-LIO SLAM using Unitree L2 LiDAR"/>
</p>

---

## Features

- **Mobile Robot Platform:** ROS 2-based robot description, URDF/Xacro models, and configuration.
- **3D LiDAR SLAM:** Point-LIO integration for LiDAR-Inertial Odometry and 3D mapping.
- **2D SLAM:** LiDAR-based scan-matching mapping and localization.
- **Visual SLAM:** RTAB-Map integration for RGB-D-based mapping.
- **Autonomous Navigation:** Nav2 integration with 2D occupancy grid maps.
- **LiDAR Integration:** Unitree L2 LiDAR driver and data processing.
- **Robotic Manipulation:** Robotic arm hardware drivers, control, and simulation configurations.
- **Point Cloud Processing:** Point cloud compression utilities.
- **Docker Support:** Containerized environment for LiDAR and SLAM dependencies.

---

## Technology Stack

| Component | Technology |
|---|---|
| Robotics Middleware | ROS 2 Humble / Jazzy |
| Programming Languages | C++, Python |
| Robot Description | URDF / Xacro |
| 2D SLAM | Cartographer, SLAM Toolbox |
| Visual SLAM | RTAB-Map |
| 3D SLAM | Point-LIO |
| Autonomous Navigation | Nav2 |
| LiDAR | Unitree L2, YDLIDAR X2 |
| Visualization | RViz2 |
| Point Cloud Processing | PCL |
| Containerization | Docker |

---

## Prerequisites

### 1. System Requirements

| Requirement | Version |
|---|---|
| Operating System | Ubuntu 22.04 LTS (recommended) |
| ROS 2 | Humble Hawksbill / Jazzy Jalisco |
| Build System | Colcon |
| CMake | 3.8+ |
| Docker | Optional |

See [setup](docs/setup.md) for installation instructions.

## Repository layout

| Path | Responsibility |
| --- | --- |
| `docker/` | Headless ROS 2 Humble core image and Compose configuration |
| `mobile_robot_driver/` | Encoder odometry, launch file, and calibration YAML |
| `robot_description/` | URDF and RViz display configuration |
| `sensor_bringup/` | Optional camera/LiDAR and scan-converter launches |
| `point_lio_ros2/` | Vendored Point-LIO implementation with local changes |
| `unilidar_sdk2/` | Vendored Unitree SDK and ROS 2 driver |
| `firmware/` | Separate ESP32 Arduino sketches and local network configuration |
| `experiments/` | Object-detection prototypes, outside the core build/image |
| `pointcloud_compression/` | Untested package, left untouched and excluded from the supported build/image |
| `scripts/` | Explicit core build and offline checks |
| `docs/` | Dependency setup, operation, calibration, and vendor provenance |


## 🚀 Quick Start

### 1. Build Workspace

```bash
cd ~/ws_mobile
colcon build --symlink-install
source install/setup.bash
```

---

### 2. Launching 3D SLAM (Unitree L2 + Point-LIO)

**Start Unitree L2 LiDAR node:**
```bash
ros2 launch unitree_lidar_ros2 launch.py
```

**Start Point-LIO 3D Mapping:**
```bash
ros2 launch point_lio mapping_unilidar_l2.launch.py
```

---

### 3. Launching 2D SLAM (Scan-Matching)

If running 2D mapping without wheel encoders using `bot_bringup`:

```bash
# 1. Start LiDAR driver (e.g., YDLidar X2)
ros2 launch ydlidar_ros2_driver X2.launch.py

# 2. Launch SLAM Toolbox bringup
ros2 launch bot_bringup slam_bringup.launch.py

# 3. Teleop & RViz2
ros2 run teleop_twist_keyboard teleop_twist_keyboard
rviz2
```

---

## 🐳 Running with Docker

Build and run the ROS 2 Humble container for Point-LIO & LiDAR drivers:

```bash
# Build image
docker build -t l2-slam:humble ./l2_slam_docker

# Run container with host network access
docker run -it --network host --name l2_run l2-slam:humble
```

---

## 🔧 Network & Buffer Tuning

If experiencing UDP packet drops or high network latency from LiDAR point clouds (e.g. Unitree L2 on Raspberry Pi), increase socket receive buffer limits:

```bash
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
```

---

## 🔗 References & Dependencies

- [Unitree Unilidar SDK 2](https://github.com/unitreerobotics/unilidar_sdk2)
- [Point-LIO ROS 2](https://github.com/dfloreaa/point_lio_ros2)
- [Livox ROS Driver 2](https://github.com/Livox-SDK/livox_ros_driver2)
- [Livox SDK 2](https://github.com/Livox-SDK/Livox-SDK2)




## Build the core

Docker targets ROS 2 Humble. The host workspace also uses Jazzy; hardware and
cross-distribution compatibility must be checked separately. See
[setup](docs/setup.md) for dependencies before building natively.

From the workspace root (the directory containing `src/`):

```bash
source /opt/ros/humble/setup.bash
bash src/Mobile_Manipulation_Robot_V0/scripts/build.sh --symlink-install
source install/setup.bash
```

The script selects only `mobile_robot_driver`, `robot_description`, `point_lio`,
and `unitree_lidar_ros2`. It does not discover or build the compression package,
experiments, or unrelated sibling packages. A plain workspace-wide `colcon build`
does not have this restriction. Use a clean workspace when you need to ensure
previously installed experimental packages cannot appear in the environment.

From this repository root, the Docker equivalent is:

```bash
docker compose -f docker/compose.yaml build
docker compose -f docker/compose.yaml run --rm robot
```

See [Docker instructions](docker/README.md) for hardware access and limitations.
The reorganized image has not yet completed full build verification.

## Run and verify

- [Operation](docs/operation.md): odometry, LiDAR, headless mapping, optional sensors.
- [Calibration](docs/calibration.md): robot dimensions, encoder scale, frames, and network settings.
- [Firmware](firmware/README.md): choose one sketch and configure the board.
- [Experiments](experiments/README.md): dependencies and unsupported prototypes.
- [Third-party code](docs/third-party.md): provenance and update policy.





From the repository root:

```bash
bash scripts/check.sh
# With ROS sourced:
PYTHONPATH="$PWD/mobile_robot_driver${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m unittest discover -s mobile_robot_driver/test -p 'test_odometry.py'
```

Checks validate structure and odometry behavior; they do not connect to hardware.
CI runs these checks on Humble. Record hardware validation results, ROS distro,
firmware variant, and calibration alongside each release.

## Contribution and licensing

Keep firmware, experiments, and runtime packages separate. Add runtime dependencies
to `package.xml`, keep calibration in package configuration, and use focused commits.
Do not commit network credentials, virtual environments, recordings, or model weights.

Upstream licenses remain with their vendor code. Some original packages still have
an undecided license; this cleanup does not assign new licensing rights. See
[license status](docs/license-status.md) before redistribution.
