import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # パラメータファイルのパスをソースディレクトリから直接指定
    config_dir = '/ros2_ws/src/bt_logic/config'
    config_path = os.path.join(config_dir, 'logic_params.yaml')

    return LaunchDescription([
        # --- [ACTION_NODES_MARKER] ---
        Node(package='bt_logic', executable='check_battery_node', name='check_battery_node', output='screen', parameters=[config_path]),
        Node(package='bt_logic', executable='tekito_action_node', name='tekito_action_node', output='screen', parameters=[config_path]),
        Node(package='bt_logic', executable='clean_room_node', name='clean_room_node', output='screen', parameters=[config_path]),
        Node(package='bt_logic', executable='pick_up_item_node', name='pick_up_item_node', output='screen', parameters=[config_path]),
        Node(package='bt_logic', executable='say_something_node', name='say_something_node', output='screen', parameters=[config_path]),
        Node(package='bt_logic', executable='move_to_target_node', name='move_to_target_node', output='screen', parameters=[config_path]),
    ])
