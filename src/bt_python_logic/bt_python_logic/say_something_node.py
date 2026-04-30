import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import SaySomething

class SaySomethingNode(Node):
    def __init__(self):
        super().__init__('say_something_node')
        self._action_server = ActionServer(
            self, SaySomething, 'say_something', self.execute_callback)
        self.get_logger().info('SaySomething Node initialized')

    def execute_callback(self, goal_handle):
        message = goal_handle.request.message
        self.get_logger().info(f'Executing SaySomething: {message}')
        
        # --- [具体的な発話ロジックをここに実装してください] ---
        # 例: TTS (Text-to-Speech) ノードにリクエストを送る、スピーカーから音を出すなど
        
        for i in range(1, 6):
            goal_handle.publish_feedback(SaySomething.Feedback(progress=i*20.0))
            time.sleep(0.3)
            
        # --------------------------------------------------------
            
        goal_handle.succeed()
        return SaySomething.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = SaySomethingNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
