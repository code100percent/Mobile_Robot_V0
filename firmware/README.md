# ESP32 firmware

Each directory is a separate Arduino sketch. Open the `.ino` matching its folder
name and flash only one variant to a board.

| Sketch | Purpose | Dependencies |
| --- | --- | --- |
| `uros_teleop_diff_motor` | micro-ROS Wi-Fi `/cmd_vel` motor control | ESP32 Arduino core, micro_ros_arduino |
| `uros_teleop_diff_enc_imu_motor` | Motor control plus wheel ticks and MPU6050 IMU | ESP32 Arduino core, micro_ros_arduino, Wire |
| `joystick_file` | Bluetooth gamepad control | ESP32 Arduino core, DabbleESP32 |

The micro-ROS sketches target an ESP32 and MDD3A motor driver. The exact ESP32 board
variant, board-core version, and library versions used for hardware validation are
not recorded yet. Select compatible versions and record them before a release;
these sketches have not been compiled as part of the repository cleanup.

## Network configuration

For each micro-ROS sketch, copy `network_config.example.h` to `network_config.h`
in that sketch's directory, then set your SSID, password, agent IPv4 address, and
port. The local file is ignored by Git and excluded from Docker. Existing local
settings were preserved in these ignored files during reorganization.

Use a micro-ROS agent matching your chosen ROS/firmware setup. The old command
notes use Jazzy whereas the core Docker image uses Humble; they are separate
environments, not a verified mixed-distribution configuration.

## Pins and flashing

Read the selected sketch's pin constants before wiring. Current micro-ROS motor
pins are 26, 27, 32, and 33. The encoder/IMU variant declares left encoder pins
35/34, right encoder pins 13/14, and MPU6050 I2C on 21/22. Verify these against
your board and electrical wiring. Select the matching board and serial port in
Arduino IDE, install its libraries, compile, and upload the selected sketch.

Check wheel direction, encoder count direction, command timeout behavior, and
agent reconnect behavior with the robot supported before conducting motion tests.
See [calibration](../docs/calibration.md) for the unresolved wheel-track discrepancy.
