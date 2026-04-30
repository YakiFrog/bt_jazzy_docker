import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import TekitoAction

class TekitoActionNode(Node):
    def __init__(self):
        super().__init__('tekito_action_node')
        self._action_server = ActionServer(
            self, TekitoAction, 'tekito_action', self.execute_callback)
        self.get_logger().info('TekitoAction Node initialized')

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing TekitoAction')
        goal_handle.succeed()
        return TekitoAction.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = TekitoActionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
