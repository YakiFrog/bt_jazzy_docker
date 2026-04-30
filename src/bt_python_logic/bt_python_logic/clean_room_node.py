import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import CleanRoom

class CleanRoomNode(Node):
    def __init__(self):
        super().__init__('clean_room_node')
        self._action_server = ActionServer(
            self, CleanRoom, 'clean_room', self.execute_callback)
        self.get_logger().info('CleanRoom Node initialized')

    def execute_callback(self, goal_handle):
        room = goal_handle.request.whichroom
        self.get_logger().info(f'Cleaning room: {room}')
        time.sleep(1.0)
        goal_handle.succeed()
        return CleanRoom.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = CleanRoomNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
