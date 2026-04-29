FROM ros:jazzy-ros-base

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    ros-jazzy-behaviortree-cpp \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    libncurses5-dev \
    libncursesw5-dev \
    python3-tk \
    python3-pip \
    libxcb-cursor0 \
    libgl1-mesa-dev \
    libegl1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-sync1 \
    libxcb-util1 \
    libxcb-shm0 \
    libxkbcommon0 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Install PySide6
RUN pip3 install --break-system-packages PySide6

# Create workspace
WORKDIR /ros2_ws

# Source ROS 2 setup in bashrc
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
RUN echo "if [ -f /ros2_ws/.bashrc_docker ]; then source /ros2_ws/.bashrc_docker; fi" >> /root/.bashrc

# Set up entrypoint
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
