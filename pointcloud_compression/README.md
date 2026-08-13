# pointcloud_compression

Compresses `sensor_msgs/PointCloud2` for transport over a slow/lossy link
(e.g. WiFi between a Pi running the lidar driver and a laptop running SLAM),
then decompresses it back into a normal `PointCloud2` on the other end.

## How it works

`compress_node` (Pi) subscribes to the raw point cloud topic, serializes the
whole ROS2 message with `serialize_message()`, compresses those bytes with
`zstd`, and publishes them as a `std_msgs/UInt8MultiArray`.

`decompress_node` (laptop) subscribes to that compressed topic, decompresses,
and calls `deserialize_message()` to reconstruct the original `PointCloud2`
exactly, then republishes it on a normal topic for Point-LIO/RViz/etc.

## Install

On **both** the Pi and the laptop:

```bash
pip install zstandard --break-system-packages   # if not using a venv
```

Copy this package into `src/` of a colcon workspace on **both** machines
(you only need `compress_node` on the Pi and `decompress_node` on the
laptop, but building the whole package on both is simplest):

```bash
cd ~/your_ws
colcon build --packages-select pointcloud_compression
source install/setup.bash
```

## Run

On the **Pi** (after the lidar driver is already publishing):

```bash
ros2 run pointcloud_compression compress_node \
  --ros-args \
  -p input_topic:=/unilidar/cloud \
  -p output_topic:=/unilidar/cloud_compressed \
  -p compression_level:=3
```

On the **laptop**:

```bash
ros2 run pointcloud_compression decompress_node \
  --ros-args \
  -p input_topic:=/unilidar/cloud_compressed \
  -p output_topic:=/unilidar/cloud
```

Point Point-LIO's config at `/unilidar/cloud` on the laptop as usual - it
never needs to know compression happened.

## Tuning

- `compression_level` (1-22): start at 1-3 on a Pi. Higher levels shrink the
  output more but cost more CPU on the Pi, which can make things *worse* if
  the Pi becomes the bottleneck instead of the network.
- `compress_node` logs an actual compression ratio every 5 seconds - watch
  this to see if raising the level is even worth it for your data.
- Both nodes use best-effort QoS with a shallow queue on purpose: on a weak
  link, dropping a stale frame is better than queuing and adding lag.

## If 1.3-2x isn't enough

Generic compression on raw float32 XYZ data has limited ceiling because the
bit patterns are fairly high-entropy. Bigger wins, in order of effort:

1. Strip unused `PointField`s before compressing (e.g. `intensity`/`tag`/
   `line`/`timestamp` if Point-LIO's config doesn't need them).
2. Voxel-downsample the cloud on the Pi before compressing (fewer points =
   less data, and less work for Point-LIO downstream too).
3. Quantize XYZ from float32 to int16 with a fixed scale factor before
   compression (lossy, but usually fine since SLAM voxelizes anyway).

Happy to add any of these to `compress_node.py` if the plain zstd ratio
isn't enough for your link.
