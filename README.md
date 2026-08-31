# Mobile Manipulation Robot (V0)

A ROS 2 repository for a mobile manipulation robot platform featuring 3D Point-LIO SLAM, Unitree L2 LiDAR integration, 2D scan-matching SLAM, and robotic arm hardware/simulation configs.




<img width="1204" height="1600" alt="WhatsApp Image 2026-09-01 at 2 28 35 AM" src="https://github.com/user-attachments/assets/4832694c-e622-49a7-9102-96b2108e9c02" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/ddd771d1-30e1-4299-81af-e666b2a5319e" />

## 📋 Prerequisites

### 1. System & ROS 2 Environment
- **OS**: Ubuntu 22.04 LTS (recommended)
- **ROS 2**: Humble Hawksbill or Jazzy Jalisco

### 2. Core Dependencies

```bash
sudo apt update && sudo apt install -y \
    build-essential cmake git \
    libpcl-dev libeigen3-dev libusb-1.0-0-dev \
    python3-colcon-common-extensions python3-pip \
    ros-$ROS_DISTRO-pcl-ros \
    ros-$ROS_DISTRO-pcl-conversions \
    ros-$ROS_DISTRO-visualization-msgs \
    ros-$ROS_DISTRO-tf2-eigen

pip3 install zstandard
```

---

### ⚠️ Critical Requirement: `Livox-SDK2` & `livox_ros_driver2`

> **IMPORTANT**: `point_lio_ros2` **will not build or work** without `Livox-SDK2` installed system-wide and `livox_ros_driver2` built in your workspace.
>
> **Why it's required:**
> - `point_lio_ros2` relies on C++ headers and data structures from **Livox-SDK2** for low-latency point cloud processing.
> - `point_lio_ros2` uses custom ROS message types (`livox_ros_driver2/msg/CustomMsg`) defined by **livox_ros_driver2** to receive timestamped LiDAR & IMU point data streams.

#### Installation Steps:

1. **Install `Livox-SDK2` system-wide:**
   ```bash
   git clone https://github.com/Livox-SDK/Livox-SDK2.git
   cd Livox-SDK2 && mkdir build && cd build
   cmake .. && make -j
   sudo make install
   ```

2. **Build `livox_ros_driver2`:**
   ```bash
   git clone https://github.com/Livox-SDK/livox_ros_driver2.git ~/ws_livox/src/livox_ros_driver2
   cd ~/ws_livox
   ./src/livox_ros_driver2/build.sh humble   # (replace 'humble' with your ROS distro)
   source ~/ws_livox/install/setup.bash
   ```

---

## 📁 Repository Structure

- **`mobile_robot/`** — Mobile robot base description (URDF/Xacro, models, configuration).
- **`bot_bringup/`** — Launch files and configuration for 2D SLAM (`slam_toolbox` scan-matching) and robot bringup.
- **`Desktop-Robotic-Arm/`** — Robotic arm configuration and driver/control packages.
- **`unilidar_sdk2/`** — ROS 2 driver for Unitree L2 LiDAR.
- **`point_lio_ros2/`** — Point-LIO 3D LiDAR-Inertial Odometry and Mapping package.
- **`pointcloud_compression/`** — Utilities for compressing point cloud data streams.
- **`l2_slam_docker/`** — Docker container environment setup for ROS 2 Humble + SLAM dependencies.

---

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

