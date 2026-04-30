import math
import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import MoveToTarget

class MoveToTargetNode(Node):
    def __init__(self):
        super().__init__('move_to_target_node')
        self._action_server = ActionServer(
            self, MoveToTarget, 'move_to_target', self.execute_callback)
        self.get_logger().info('MoveToTarget Node initialized')

    def execute_callback(self, goal_handle):
        target_x = goal_handle.request.x
        target_y = goal_handle.request.y
        self.get_logger().info(f'Moving to ({target_x}, {target_y})')
        
        # --- [具体的なロボットの移動ロジックをここに実装してください] ---
        # 例: Nav2 の Action クライアントを呼ぶ、または直接モーター制御など
        
        current_x, current_y = 0.0, 0.0
        while True:
            dist = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
            goal_handle.publish_feedback(MoveToTarget.Feedback(distance=dist))
            
            if dist < 0.1: break
            
            current_x += (target_x - current_x) * 0.2
            current_y += (target_y - current_y) * 0.2
            time.sleep(0.3)
            
        # ------------------------------------------------------------
            
        goal_handle.succeed()
        return MoveToTarget.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = MoveToTargetNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
