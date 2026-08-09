# Mobile_Manipulation_Robot_V0

ros2 launch unitree_lidar_ros2 launch.py
ros2 launch point_lio mapping_unilidar_l2.launch.py


### building docker image

```
docker build -t l2-slam:humble 

docker run -it \
  --network host \
  --name l2_run \
  l2-slam:humble
```

Problems and solutions :

buffer overflow to docker latency (solved ig) way suggested by claude to increase the ethernet buffer size on pi  :
```
sudo sysctl -w net.core.rmem_max=26214400

sudo sysctl -w net.core.rmem_default=26214400
```
