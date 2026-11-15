# Experiments

These prototypes are outside the core build and Docker context. They have no
hardware-validation guarantee. Keep them here until they have a documented ROS
package interface, declared dependencies, and meaningful tests.

`object_detection/` contains:

- `yolo_object_detection.py`: webcam index 0, Ultralytics YOLO, OpenCV display.
- `3d_object_detection.py`: ROS RGB/depth subscriptions, camera calibration, TF
  lookup into `map`, and semantic markers. It assumes the hard-coded OAK topics
  exist and the depth/RGB geometry and timing are suitable.

Python imports require `ultralytics`, `opencv-python`, and `numpy`; the ROS script
also requires the sourced ROS environment, `cv_bridge`, `tf2_ros`, and message
packages. A working version set has not been recorded, so no verified dependency
lock is claimed. Create a separate environment instead of committing `yolo-venv/`.
Both scripts load `yolo11n.pt` relative to the working directory; downloading model
weights may require network access. Weights are ignored by Git.

The separate root `pointcloud_compression/` package is also untested. It remains
untouched and is excluded by the explicit core build and Docker ignore rules.
