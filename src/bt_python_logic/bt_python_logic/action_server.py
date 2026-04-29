import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import SaySomething

class SaySomethingActionServer(Node):
    def __init__(self):
        super().__init__('say_something_action_server')
        self._action_server = ActionServer(
            self,
            SaySomething,
            'say_something',
            self.execute_callback)
        self.get_logger().info('Python Action Server (Logic) has been started.')

    def execute_callback(self, goal_handle):
        self.get_logger().info(f'Executing goal: "{goal_handle.request.message}"')
        
        feedback_msg = SaySomething.Feedback()
        
        # Simulate some logic/work
        for i in range(1, 6):
            feedback_msg.progress = i * 20.0
            self.get_logger().info(f'Logic progress: {feedback_msg.progress}%')
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(0.5)

        goal_handle.succeed()
        self.get_logger().info('Logic completed successfully.')

        result = SaySomething.Result()
        result.success = True
        return result

def main(args=None):
    rclpy.init(args=args)
    action_server = SaySomethingActionServer()
    rclpy.spin(action_server)
    action_server.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
