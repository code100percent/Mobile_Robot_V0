# Mobile Manipulation Robot (V0)

A ROS 2-based mobile manipulation platform integrating autonomous navigation, multi-modal SLAM, 3D LiDAR perception, and robotic arm control.

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

## Repository Structure

```text
ws_mobile/
│
├── mobile_robot/
│   └── Robot description, URDF/Xacro, models and configurations
│
├── bot_bringup/
│   └── Robot bringup and 2D SLAM launch configurations
│
├── Desktop-Robotic-Arm/
│   └── Robotic arm drivers, control and simulation configurations
│
├── unilidar_sdk2/
│   └── ROS 2 driver for Unitree L2 LiDAR
│
├── point_lio_ros2/
│   └── Point-LIO 3D LiDAR-Inertial SLAM
│
├── pointcloud_compression/
│   └── Point cloud compression utilities
│
└── l2_slam_docker/
    └── Docker environment for ROS 2 Humble and SLAM dependencies
```

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

### 2. Install Core Dependencies

```bash
sudo apt update

sudo
