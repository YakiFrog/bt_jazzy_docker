#!/bin/bash

# Build the docker image
echo "Building Docker image..."
docker compose build

# Start the container and build the workspace
echo "Building ROS 2 workspace inside container..."
docker compose run --rm bt_dev bash -c "colcon build --symlink-install"

echo "------------------------------------------------"
echo "Setup complete!"
echo "To start the container, run: docker compose run --rm bt_dev"
echo "Inside the container, run the example: ros2 run bt_example bt_node"
echo "------------------------------------------------"
