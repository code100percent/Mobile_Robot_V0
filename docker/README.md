# ROS 2 Humble Docker environment

This folder replaces `l2_slam_docker/` and contains the container setup for
Point-LIO, the Unitree L2 driver, encoder odometry, and robot description. The
explicit `scripts/build.sh` core scope is shared with the native build.
`pointcloud_compression` stays untouched in the repository and is excluded from
the Docker context. Its `zstandard` dependency is not installed. Firmware and
experiments are also excluded. Optional `sensor_bringup` is not built by default.
Run the commands below from the **Mobile_Manipulation_Robot_V0 repository root**.
Use a Linux host with Docker Engine and the Docker Compose plugin.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Installs dependencies, builds Livox, and builds local robot source. |
| `Dockerfile.dockerignore` | Excludes local build output, virtual environments, Git metadata, and recordings from the build context. |
| `entrypoint.sh` | Sources ROS and both workspaces before executing the container command. |
| `compose.yaml` | Provides a shell with host networking and IPC for ROS communication. |

## Build and open a shell

```bash
docker compose -f docker/compose.yaml build
docker compose -f docker/compose.yaml run --rm robot
```

The image is `l2-slam:humble`. It includes source from your local checkout,
including uncommitted edits. Rebuild after changing source; no host source
folder is mounted over the compiled workspace. The first build downloads ROS
and Livox dependencies and can take a while.

Equivalent commands without Compose:

```bash
docker build -f docker/Dockerfile -t l2-slam:humble .
docker run --rm -it --init --network host --ipc host l2-slam:humble
```

The build context must be the repository root (`.`), not `docker/`.
Compilation defaults to two jobs for CMake/Make and one colcon package at a
time. On a larger machine you can set `BUILD_JOBS=4` before the Compose build,
or pass `--build-arg BUILD_JOBS=4` to `docker build`. Upstream build scripts
may choose their own parallelism.

## Run commands

ROS and both workspace overlays are sourced for shell and direct commands:

```bash
docker compose -f docker/compose.yaml run --rm robot ros2 pkg list
docker compose -f docker/compose.yaml run --rm robot \
  ros2 launch point_lio mapping_unilidar_l2.launch.py rviz:=false
```

Use the same ROS domain as other machines/nodes on your network:

```bash
ROS_DOMAIN_ID=10 docker compose -f docker/compose.yaml run --rm robot
```

Host networking supports LiDAR UDP traffic and ROS discovery. Host IPC allows
shared-memory communication with host ROS processes. These settings target
Linux and share the host's network and IPC namespaces.

## Hardware, GUI, and data

Serial devices must be passed explicitly when needed; for example:

```bash
docker compose -f docker/compose.yaml run --rm \
  --device /dev/ttyUSB0:/dev/ttyUSB0 robot
```

Replace the device path with your hardware's actual path. Containers run as
root, matching the original environment. Files written through bind mounts
may therefore be owned by root on the host.

Containers started with `run --rm` are removed on exit. To keep generated data,
mount a directory and configure the ROS node to write to `/data`:

```bash
mkdir -p data
docker compose -f docker/compose.yaml run --rm \
  -v "$PWD/data:/data" robot
```

This is a headless SLAM environment. GUI forwarding and camera USB access are
not configured. Launch files that start RViz require additional GUI setup or
must have RViz disabled. The optional `sensor_bringup` package is outside the core build and depends on
`depthai_ros_driver_v3` and the sibling `mobile_nav_bringup` package, which this
standalone repository image does not supply. YOLO's host virtual environment
is intentionally excluded.

## Maintenance and checks

```bash
docker compose -f docker/compose.yaml config --quiet
bash -n docker/entrypoint.sh
docker compose -f docker/compose.yaml run --rm robot \
  bash -c 'ros2 pkg prefix point_lio && ros2 pkg prefix unitree_lidar_ros2'
```

Livox repositories currently follow their default branches, as in the original
Dockerfile, and the ROS base image uses a tag. Pin commits and an image digest
before relying on byte-for-byte reproducible release builds. Keep the Unitree
SDK's bundled static libraries in the build context; they are link dependencies.
