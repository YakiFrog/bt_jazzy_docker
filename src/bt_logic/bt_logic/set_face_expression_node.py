import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from bt_msgs.action import SetFaceExpression

class SetFaceExpressionNode(Node):
    def __init__(self):
        super().__init__('set_face_expression_node')
        self._action_server = ActionServer(
            self, SetFaceExpression, 'set_face_expression', 
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup())
        self.get_logger().info('SetFaceExpression Node initialized')

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing SetFaceExpression...')
        expression = goal_handle.request.expression
        self.get_logger().info(f'Setting face expression to: {expression}')
        
        # Simulate success
        goal_handle.succeed()
        return SetFaceExpression.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = SetFaceExpressionNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
