#!/bin/bash
set -e

# Source ROS 2
source "/opt/ros/jazzy/setup.bash"

# Source workspace if it exists
if [ -f "/ros2_ws/install/setup.bash" ]; then
    source "/ros2_ws/install/setup.bash"
fi

if [ -f "/ros2_ws/.bashrc_docker" ]; then
    source "/ros2_ws/.bashrc_docker"
fi

exec "$@"
