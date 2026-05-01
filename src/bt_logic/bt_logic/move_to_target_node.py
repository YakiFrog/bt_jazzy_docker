import math
import time
import rclpy
from rclpy.action import ActionServer, GoalResponse
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from bt_msgs.action import MoveToTarget

class MoveToTargetNode(Node):
    def __init__(self):
        super().__init__('move_to_target_node')
        
        # 状態保持用
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        
        # Odom 購読
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        # CmdVel 配信
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Action Server
        self._action_server = ActionServer(
            self, MoveToTarget, 'move_to_target', 
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup()
        )
        
        self.get_logger().info('MoveToTarget Node initialized (Real Motion Mode)')

    def odom_callback(self, msg):
        # 位置の取得
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # クォータニオンから Yaw (向き) を計算
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    async def execute_callback(self, goal_handle):
        target_x = goal_handle.request.x
        target_y = goal_handle.request.y
        self.get_logger().info(f'Moving to ({target_x}, {target_y})')
        
        rate = self.create_rate(10) # 10Hz
        
        while rclpy.ok():
            # 1. 目標までの距離と角度を計算
            dx = target_x - self.current_x
            dy = target_y - self.current_y
            dist = math.sqrt(dx**2 + dy**2)
            angle_to_target = math.atan2(dy, dx)
            
            # 2. フィードバック送信
            goal_handle.publish_feedback(MoveToTarget.Feedback(distance=dist))
            
            # 3. 終了判定（0.1m以内に近づいたら成功）
            if dist < 0.1:
                break
            
            # 4. 中断チェック
            if goal_handle.is_cancel_requested:
                self.stop_robot()
                goal_handle.canceled()
                return MoveToTarget.Result(success=False)

            # 5. 速度計算 (P制御)
            twist = Twist()
            
            # 向きの修正 (Yaw 誤差)
            yaw_error = angle_to_target - self.current_yaw
            # 角度を -pi ~ pi に正規化
            yaw_error = math.atan2(math.sin(yaw_error), math.cos(yaw_error))
            
            if abs(yaw_error) > 0.2:
                # まずはその場で旋回
                twist.angular.z = 0.5 if yaw_error > 0 else -0.5
                twist.linear.x = 0.0
            else:
                # 前進しながら微調整
                twist.linear.x = min(0.3, 0.2 * dist) # 最大 0.3m/s
                twist.angular.z = 0.8 * yaw_error
                
            self.cmd_vel_pub.publish(twist)
            rate.sleep()
            
        self.stop_robot()
        goal_handle.succeed()
        return MoveToTarget.Result(success=True)

    def stop_robot(self):
        self.cmd_vel_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = MoveToTargetNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
