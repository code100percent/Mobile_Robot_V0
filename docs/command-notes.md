# Historical command notes

Retained from `importantcmds.md`. These commands mix environments and have not
been validated as a single setup. Use [operation.md](operation.md) for current
component commands and [setup.md](setup.md) for dependencies.

--for serial

`docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:jazzy serial --dev /dev/ttyUSB0 -b 115200 -v4`

--for wifi 

`docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:jazzy udp4 --port 8888 --dev  -v4`


--camera only 

`ros2 launch depthai_ros_driver_v3 driver.launch.py use_rviz:=true`

--depth point cloud 

`ros2 launch depthai_ros_driver_v3 rgbd_pcl.launch.py use_rviz:=true`


--camera rtabmap 

`ros2 launch depthai_ros_driver_v3 rtabmap.launch.py`

--- mobile robot native pakages 

`ros2 launch robot_description display.launch.py`

`ros2 launch mobile_robot_driver driver.launch.py`



--- visual slam with wheel odometry 

`ros2 launch depthai_ros_driver_v3 driver.launch.py \
  imu_from_descr:=true \
  pointcloud.enable:=false`




ros2 launch sensor_bringup sensors.launch.py \
  start_cmdvel_serial:=true motor_serial_port:=/dev/ttyUSB0