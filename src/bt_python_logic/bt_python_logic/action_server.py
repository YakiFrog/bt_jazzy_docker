import time
import math
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import SaySomething, MoveToTarget, PickUpItem

class MultiActionServer(Node):
    """
    複数のアクションに対応したロジックサーバー
    """
    def pickupitem_callback(self, goal_handle):
        self.get_logger().info('PickUpItem started')
        goal_handle.succeed()
        return PickUpItem.Result(success=True)

    def __init__(self):
        super().__init__('multi_action_server')
        self._pickupitem_server = ActionServer(self, PickUpItem, 'pickupitem', self.pickupitem_callback)
        
        # 1. 挨拶アクションのサーバー
        self._say_something_server = ActionServer(
            self, SaySomething, 'say_something', self.say_something_callback)
        
        # 2. 移動アクションのサーバー
        self._move_to_target_server = ActionServer(
            self, MoveToTarget, 'move_to_target', self.move_to_target_callback)
            
        self.get_logger().info('Python ロジックサーバーが起動しました（SaySomething & MoveToTarget）')

    def say_something_callback(self, goal_handle):
        """挨拶ロジック"""
        message = goal_handle.request.message
        self.get_logger().info(f'挨拶リクエスト: {message}')
        for i in range(1, 6):
            goal_handle.publish_feedback(SaySomething.Feedback(progress=i*20.0))
            time.sleep(0.3)
        goal_handle.succeed()
        return SaySomething.Result(success=True)

    def move_to_target_callback(self, goal_handle):
        """移動ロジック（シミュレーション）"""
        target_x = goal_handle.request.x
        target_y = goal_handle.request.y
        self.get_logger().info(f'移動開始: 目標座標 ({target_x}, {target_y})')
        
        feedback_msg = MoveToTarget.Feedback()
        
        # 現在地 (0,0) から目標まで近づいていくシミュレーション
        current_x, current_y = 0.0, 0.0
        
        while True:
            # 目標までの距離を計算
            dist = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
            feedback_msg.distance = dist
            goal_handle.publish_feedback(feedback_msg)
            
            if dist < 0.1: # 到着判定
                break
                
            self.get_logger().info(f'現在地: ({current_x:.2f}, {current_y:.2f}), 残り距離: {dist:.2f}')
            
            # 少しずつ目標に近づける
            current_x += (target_x - current_x) * 0.2
            current_y += (target_y - current_y) * 0.2
            time.sleep(0.5)

        goal_handle.succeed()
        self.get_logger().info('目標地点に到着しました！')
        return MoveToTarget.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    server = MultiActionServer()
    try:
        rclpy.spin(server)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()
