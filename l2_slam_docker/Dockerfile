FROM ros:humble-ros-base

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    nano \
    git \
    build-essential \
    cmake \
    libpcl-dev \
    libeigen3-dev \
    libusb-1.0-0-dev \
    python3-colcon-common-extensions \
    ros-humble-pcl-ros \
    ros-humble-pcl-conversions \
    ros-humble-visualization-msgs \
    ros-humble-tf2-eigen \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/unitree_ws/src

RUN git clone https://github.com/unitreerobotics/unilidar_sdk2.git
RUN git clone https://github.com/dfloreaa/point_lio_ros2.git

WORKDIR /root/unitree_ws

RUN source /opt/ros/humble/setup.bash && \
    colcon build --packages-select unitree_lidar_ros2  point_lio_ros2 

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /root/unitree_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]