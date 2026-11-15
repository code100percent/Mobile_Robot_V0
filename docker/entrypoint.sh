#!/usr/bin/env bash
set -e

# ROS setup scripts may reference unset variables; do not enable nounset.
source /opt/ros/humble/setup.bash
source /root/ws_livox/install/setup.bash
source /root/unitree_ws/install/setup.bash

exec "$@"
