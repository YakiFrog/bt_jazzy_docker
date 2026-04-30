import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import TekitoAction2

class TekitoAction2Node(Node):
    def __init__(self):
        super().__init__('tekito_action2_node')
        self._action_server = ActionServer(
            self, TekitoAction2, 'tekito_action2', self.execute_callback)
        self.get_logger().info('TekitoAction2 Node initialized')

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing TekitoAction2...')
        nandemoii = goal_handle.request.nandemoii
        
        # TODO: 具体的なロジックをここに実装
        
        goal_handle.succeed()
        return TekitoAction2.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = TekitoAction2Node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
