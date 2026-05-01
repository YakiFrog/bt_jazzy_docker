import os
from glob import glob
from setuptools import setup

package_name = 'bt_logic'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launchファイルをインストール対象に含める
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Configファイルをインストール対象に含める
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Python logic for BT example',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # --- [CONSOLE_SCRIPTS_MARKER] ---
            'check_battery_node = bt_logic.check_battery_node:main',
            'tekito_action_node = bt_logic.tekito_action_node:main',
            'clean_room_node = bt_logic.clean_room_node:main',
            'pick_up_item_node = bt_logic.pick_up_item_node:main',
            'say_something_node = bt_logic.say_something_node:main',
            'move_to_target_node = bt_logic.move_to_target_node:main',
            'rotate_degrees_node = bt_logic.rotate_degrees_node:main',
        ],
    },
)
