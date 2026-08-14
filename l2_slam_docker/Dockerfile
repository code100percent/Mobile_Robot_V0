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
    iputils-ping \
    python3-colcon-common-extensions \
    python3-pip \
    ros-humble-pcl-ros \
    ros-humble-pcl-conversions \
    ros-humble-visualization-msgs \
    ros-humble-tf2-eigen \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install zstandard --break-system-packages

WORKDIR /root/ws_livox/src

RUN git clone https://github.com/Livox-SDK/livox_ros_driver2.git
RUN git clone https://github.com/Livox-SDK/Livox-SDK2.git

WORKDIR /root/ws_livox/src/Livox-SDK2
RUN mkdir build

WORKDIR /root/ws_livox/src/Livox-SDK2/build
RUN cmake .. && make -j && make install

WORKDIR /root/ws_livox/
RUN source /opt/ros/humble/setup.bash && \
    ./src/livox_ros_driver2/build.sh humble

WORKDIR /root/unitree_ws/src

RUN git clone https://github.com/code100percent/Mobile_Manipulation_Robot_V0.git

WORKDIR /root/unitree_ws

RUN source /opt/ros/humble/setup.bash && \
    source /root/ws_livox/install/setup.bash && \
    colcon build

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /root/ws_livox/install/setup.bash" >> /root/.bashrc && \
    echo "source /root/unitree_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]