# bot_bringup — SLAM without encoders (scan-matching only)

For: 4-wheel DC motor bot, ESP32 + micro-ROS, RPi5 running ROS2 **Jazzy**,
YDLidar X2 publishing `/scan`, no wheel encoders / no `/odom` yet.

## What this package does

- Publishes `base_link -> laser_link` as a **static** transform, using the
  real physical mount offset of your lidar (edit the launch args).
- Publishes `odom -> base_link` as an **identity** placeholder transform
  (since you have no encoders). `slam_toolbox`'s scan matcher then
  estimates the actual pose by publishing `map -> odom` on top of this,
  so mapping still works — it's just relying purely on matching
  consecutive lidar scans instead of wheel odometry.
- Launches `slam_toolbox` in **online_async** mapping mode with params
  tuned to lean on scan matching.

## 1. Install dependencies

```bash
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-tf2-ros
```

## 2. Copy this package into your workspace

```bash
cp -r bot_bringup ~/apna_ws/src/
cd ~/apna_ws
colcon build --packages-select bot_bringup
source install/setup.bash
```

## 3. Edit the lidar mount offset

Open `launch/slam_bringup.launch.py` and set the default values for
`lidar_x`, `lidar_y`, `lidar_z`, `lidar_yaw` to match where the YDLidar X2
is physically mounted relative to the center of your robot base
(`base_link`). If the lidar faces backwards relative to your robot's
front, set `lidar_yaw` to `3.14159`.

You can also override these at launch time without editing the file:

```bash
ros2 launch bot_bringup slam_bringup.launch.py lidar_x:=0.05 lidar_z:=0.12
```

## 4. Make sure your lidar driver is already running

This package does NOT start the YDLidar driver itself — start that
separately first (in another terminal), e.g.:

```bash
ros2 launch ydlidar_ros2_driver X2.launch.py
```

Confirm `/scan` is publishing: `ros2 topic echo /scan`

## 5. Launch SLAM

```bash
ros2 launch bot_bringup slam_bringup.launch.py
```

## 6. Visualize in RViz2

```bash
rviz2
```

- Set **Fixed Frame** to `map`
- Add displays: `Map` (topic `/map`), `LaserScan` (topic `/scan`), `TF`

## 7. Drive slowly with teleop

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Move in small, slow, deliberate steps — especially rotations. Without
real odometry, if the scan matcher briefly loses tracking (fast turns,
long empty corridors), the map can jump or distort. If that happens,
stop and either restart mapping or drive back to a previously-mapped
area to let it re-localize.

## 8. Save the map once fully mapped

```bash
ros2 run nav2_map_server map_saver_cli -f ~/apna_ws/my_map
```

This produces `my_map.yaml` and `my_map.pgm`, ready to feed into Nav2
later.

## Next step (later)

Once mapping works, come back before wiring up Nav2 — without real
`/odom`, Nav2's local controller (which needs live velocity feedback,
not just pose) will be shaky. Adding cheap wheel encoders is the
recommended upgrade before autonomous navigation.
