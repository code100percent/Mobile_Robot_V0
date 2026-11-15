# Robot operation

Source ROS and the workspace install overlay in each terminal. These commands
start individual components; they are not an automated hardware acceptance test.

## Encoder odometry

```bash
ros2 launch mobile_robot_driver driver.launch.py
# Override calibration without editing code:
ros2 launch mobile_robot_driver driver.launch.py params_file:=/absolute/path/odometry.yaml
```

Input: cumulative left/right `Int32MultiArray` counts on `/wheel_ticks`.
Output: `/odom` and `odom -> base_footprint` TF. The encoder firmware must be
running with matching count scale and wheel direction. Do not run another publisher
for the same odometry TF edge.

## LiDAR and mapping

Start the driver and mapping in separate terminals:

```bash
ros2 launch unitree_lidar_ros2 launch.py
ros2 launch point_lio mapping_unilidar_l2.launch.py rviz:=false
```

Check the vendor launch's network/device configuration for your LiDAR. Headless
Docker does not configure GUI forwarding. On a desktop with RViz installed, set
`rviz:=true` for mapping visualization. `robot_description display.launch.py`
starts a GUI joint-state publisher and RViz, so it is a desktop visualization tool.

## Optional sensors

After completing the optional setup in [setup.md](setup.md):

```bash
ros2 launch sensor_bringup sensors.launch.py
ros2 launch sensor_bringup pointcloud_to_laserscan.launch.py
```

The sensor launch starts the camera and LiDAR. Set `start_lidar:=false` if another
launch owns the LiDAR. The scan converter uses the mount from the external
`mobile_nav_bringup/config/robot_params.yaml` and assumes a level LiDAR.

The legacy discrete-character serial relay is opt-in:

```bash
ros2 launch sensor_bringup sensors.launch.py \
  start_cmdvel_serial:=true motor_serial_port:=/dev/ttyUSB0
```

Select the control path matching the flashed firmware. Do not run the legacy
serial relay and a micro-ROS motor-control path against the same hardware.
Historical command notes are retained in [command-notes.md](command-notes.md);
they are not the supported setup guide.
