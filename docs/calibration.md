# Calibration and configuration ownership

| Setting | Location | Current status |
| --- | --- | --- |
| Wheel diameter, track, ticks/revolution | `mobile_robot_driver/config/odometry.yaml` | Existing defaults preserved: 0.10 m, 0.35 m, 900 counts |
| Visual geometry and sensor joints | `robot_description/urdf/mobile_robot.urdf` | Check against measured robot |
| Motor wheel base and pins | Selected `firmware/` sketch | micro-ROS sketches use 0.355 m; differs from odometry |
| Wi-Fi and micro-ROS agent address | Ignored `network_config.h` beside each micro-ROS sketch | Local-only settings |
| LiDAR driver transport | Unitree driver launch/configuration | Verify against actual device |
| Scan-converter mount | External `mobile_nav_bringup/config/robot_params.yaml` | Separate workspace dependency |

Do not silently reconcile the 0.35/0.355 m track discrepancy: measure the effective
track and update firmware and odometry together. Count encoder increments over
one wheel revolution, including gearbox ratio and decoding mode; confirm both
wheels count forward as positive. Check straight-line distance and in-place rotation.

The YAML is the normal odometry launch configuration. Python defaults remain for
direct execution. Use a separate parameter file for a different robot. URDF, firmware,
and navigation calibration are not automatically synchronized yet.
