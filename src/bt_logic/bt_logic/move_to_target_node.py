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
        
        # パラメータの宣言
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('max_linear_speed', 0.3)
        self.declare_parameter('kp_linear', 0.2)
        self.declare_parameter('kp_angular', 0.8)
        self.declare_parameter('goal_tolerance', 0.1)
        self.declare_parameter('yaw_tolerance', 0.2)
        
        # 状態保持用
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        
        # Odom 購読
        odom_topic = self.get_parameter('odom_topic').value
        self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        
        # CmdVel 配信
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.cmd_vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        
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
        count = 0
        
        while rclpy.ok():
            # 常に最新のパラメータを反映（Actionの途中でも変更可能に）
            max_linear_speed = self.get_parameter('max_linear_speed').value
            kp_linear = self.get_parameter('kp_linear').value
            kp_angular = self.get_parameter('kp_angular').value
            goal_tolerance = self.get_parameter('goal_tolerance').value
            yaw_tolerance = self.get_parameter('yaw_tolerance').value

            # 1. 目標までの距離と角度を計算
            dx = target_x - self.current_x
            dy = target_y - self.current_y
            dist = math.sqrt(dx**2 + dy**2)
            angle_to_target = math.atan2(dy, dx)

            # 向きの修正 (Yaw 誤差)
            yaw_error = angle_to_target - self.current_yaw
            yaw_error = math.atan2(math.sin(yaw_error), math.cos(yaw_error))
            
            # 2. フィードバック送信
            dist = round(dist, 3)
            status_msg = ""
            if abs(yaw_error) > yaw_tolerance:
                status_msg = f"Rotating (Err: {yaw_error:.3f})"
            else:
                status_msg = f"Moving (Dist: {dist:.3f})"
            
            goal_handle.publish_feedback(MoveToTarget.Feedback(distance=dist, status=status_msg))
            
            # 3. 終了判定
            if dist < goal_tolerance:
                self.get_logger().info('Goal Reached!')
                break
            
            # 4. 中断チェック
            if goal_handle.is_cancel_requested:
                self.stop_robot()
                goal_handle.canceled()
                return MoveToTarget.Result(success=False)

            # 5. 速度計算 (P制御)
            twist = Twist()
            
            if abs(yaw_error) > yaw_tolerance:
                # 旋回中
                twist.angular.z = 0.3 if yaw_error > 0 else -0.3
                twist.linear.x = 0.0
            else:
                # 前進中
                twist.linear.x = min(max_linear_speed, kp_linear * dist)
                twist.angular.z = kp_angular * yaw_error
                
            self.cmd_vel_pub.publish(twist)
            
            # ターミナルデバッグ用 (10Hzなので10回に1回 = 1秒おき)
            if count % 10 == 0:
                self.get_logger().info(f"DIST: {dist:.2f}m, YAW_ERR: {yaw_error:.2f}rad -> V: {twist.linear.x:.2f}, W: {twist.angular.z:.2f}")
            
            count += 1
            rate.sleep()
            
        self.stop_robot()
        goal_handle.succeed()
        return MoveToTarget.Result(success=True)

    def stop_robot(self):
        self.cmd_vel_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = MoveToTargetNode()
    
    # マルチスレッド実行エグゼキュータを使用して、Action実行中もOdom購読を並行して行えるようにする
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
