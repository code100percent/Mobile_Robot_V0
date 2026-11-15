FROM ros:humble-ros-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Limit parallel compilation on memory-constrained robot computers.
ARG BUILD_JOBS=2
ENV CMAKE_BUILD_PARALLEL_LEVEL=${BUILD_JOBS}
ENV MAKEFLAGS="-j${BUILD_JOBS}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    git \
    iputils-ping \
    libeigen3-dev \
    libpcl-dev \
    libusb-1.0-0-dev \
    nano \
    python3-colcon-common-extensions \
    python3-dev \
    python3-serial \
    ros-humble-pcl-conversions \
    ros-humble-pcl-ros \
    ros-humble-pointcloud-to-laserscan \
    ros-humble-tf2-eigen \
    ros-humble-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

# Keep the Livox workspace separate so robot edits reuse this build layer.
WORKDIR /root/ws_livox/src
RUN git clone https://github.com/Livox-SDK/livox_ros_driver2.git \
    && git clone https://github.com/Livox-SDK/Livox-SDK2.git
RUN cmake -S Livox-SDK2 -B Livox-SDK2/build \
    && cmake --build Livox-SDK2/build --parallel "${BUILD_JOBS}" \
    && cmake --install Livox-SDK2/build \
    && ldconfig

WORKDIR /root/ws_livox
RUN source /opt/ros/humble/setup.bash \
    && ./src/livox_ros_driver2/build.sh humble

# The repository root is the build context: include local source changes.
WORKDIR /root/unitree_ws
COPY . src/Mobile_Manipulation_Robot_V0/
RUN source /opt/ros/humble/setup.bash \
    && source /root/ws_livox/install/setup.bash \
    && bash src/Mobile_Manipulation_Robot_V0/scripts/build.sh --cmake-args -DCMAKE_BUILD_TYPE=Release

COPY docker/entrypoint.sh /usr/local/bin/robot-entrypoint.sh
RUN chmod +x /usr/local/bin/robot-entrypoint.sh \
    && printf '\nsource /opt/ros/humble/setup.bash\nsource /root/ws_livox/install/setup.bash\nsource /root/unitree_ws/install/setup.bash\n' >> /root/.bashrc

ENTRYPOINT ["/usr/local/bin/robot-entrypoint.sh"]
CMD ["bash"]
