# Third-party source and update policy

| Tree | Recorded upstream | Revision status |
| --- | --- | --- |
| `point_lio_ros2/` | https://github.com/dfloreaa/point_lio_ros2 | Exact imported commit unknown; local modifications exist |
| `unilidar_sdk2/` | https://github.com/unitreerobotics/unilidar_sdk2 | Bundled VERSION.md ends at v2.0.10; exact imported commit unknown; local modifications exist |
| Livox SDK in Docker | https://github.com/Livox-SDK/Livox-SDK2 | Default branch, not pinned |
| Livox ROS driver in Docker | https://github.com/Livox-SDK/livox_ros_driver2 | Default branch, not pinned |

These upstream URLs come from repository documentation; no exact commit provenance
has been inferred from file similarity. Preserve vendor licenses and bundled SDK
libraries. Keep the Unitree ROS driver and SDK relative layout intact.

Before updating a vendor tree: record the existing local diff, select and record an
upstream commit, apply the update separately from local patches, then build and run
hardware checks. Do not replace the trees wholesale and lose local changes.

Before a reproducible release, identify the imported vendor commits, pin both Livox
clones and the ROS base-image digest, and record the verified architecture and ROS
version. The current image is a development environment, not a locked release.
