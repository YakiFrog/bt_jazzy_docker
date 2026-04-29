from setuptools import setup

package_name = 'bt_python_logic'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
            'action_server = bt_python_logic.action_server:main'
        ],
    },
)
