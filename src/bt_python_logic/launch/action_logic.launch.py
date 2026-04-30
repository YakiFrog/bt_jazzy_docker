import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # --- [ACTION_NODES_MARKER] ---
        Node(
            package='bt_python_logic',
            name='tekito_action2_node',
            output='screen'
        ),
        Node(
            package='bt_python_logic',
            executable='tekito_action_node',
            name='tekito_action_node',
            output='screen'
        ),
        Node(
            package='bt_python_logic',
            executable='clean_room_node',
            name='clean_room_node',
            output='screen'
        ),
        Node(
            package='bt_python_logic',
            executable='pick_up_item_node',
            name='pick_up_item_node',
            output='screen'
        ),
        Node(
            package='bt_python_logic',
            executable='say_something_node',
            name='say_something_node',
            output='screen'
        ),
        Node(
            package='bt_python_logic',
            executable='move_to_target_node',
            name='move_to_target_node',
            output='screen'
        ),
    ])
