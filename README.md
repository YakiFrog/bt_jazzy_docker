# BehaviorTree.CPP v4 for ROS 2 Jazzy (Docker Environment)

This repository provides a ready-to-use Docker environment for developing with **BehaviorTree.CPP v4** on **ROS 2 Jazzy**.

## Features
- **ROS 2 Jazzy**: Built on the official `ros:jazzy-ros-base` image.
- **BehaviorTree.CPP v4**: Pre-installed and ready to use.
- **Persistent Workspace**: Build artifacts (`build`, `install`, `log`) are stored on the host machine via Docker volumes.
- **Sample Package**: Includes a `bt_example` package to get you started.

## Prerequisites
- Docker
- Docker Compose

## Getting Started

### 1. Initial Setup & Build
Run the following script to build the Docker image and compile the ROS 2 workspace inside the container:
```bash
chmod +x setup_workspace.sh
./setup_workspace.sh
```

### 2. Start the Development Environment
To enter the container:
```bash
docker compose run --rm bt_dev
```

### 3. Run the Example
Inside the container, run the sample Behavior Tree node:
```bash
ros2 run bt_example bt_node
```

## Directory Structure
- `src/`: ROS 2 source code (your packages go here).
- `Dockerfile`: Container definition.
- `docker-compose.yml`: Container orchestration and volume settings.
- `setup_workspace.sh`: Utility script for building everything.
- `build/`, `install/`, `log/`: Generated build files (persistent on host).

## Why build inside Docker?
Building inside the container ensures that you have the exact same dependencies and compiler versions regardless of which PC you are using. It prevents "it works on my machine" issues and keeps your host OS clean.
