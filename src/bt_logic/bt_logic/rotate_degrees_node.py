import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from bt_msgs.action import RotateDegrees
import math

class RotateDegreesNode(Node):
    def __init__(self):
        super().__init__('rotate_degrees_node')
        
        # パラメータの宣言 (move_to_target_node に合わせる)
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('max_angular_speed', 0.6)
        self.declare_parameter('kp_angular', 0.8)
        self.declare_parameter('yaw_tolerance', 0.05)
        
        # 状態保持用
        self.current_yaw = 0.0
        
        # Odom 購読
        odom_topic = self.get_parameter('odom_topic').value
        self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        
        # CmdVel 配信
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.cmd_vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        
        # Action Server (ReentrantCallbackGroup を使用)
        self._action_server = ActionServer(
            self, RotateDegrees, 'rotate_degrees', 
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup()
        )
        
        self.get_logger().info('RotateDegrees Node initialized')

    def odom_callback(self, msg):
        # クォータニオンから Yaw (向き) を計算
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, angle):
        """角度を -pi から pi の範囲に正規化"""
        return math.atan2(math.sin(angle), math.cos(angle))

    async def execute_callback(self, goal_handle):
        target_degrees = goal_handle.request.degrees
        self.get_logger().info(f'Executing RotateDegrees: {target_degrees} degrees')
        
        # 目標角度をラジアンに変換 (相対)
        target_offset_rad = math.radians(target_degrees)
        start_yaw = self.current_yaw
        target_yaw = self.normalize_angle(start_yaw + target_offset_rad)
        
        rate = self.create_rate(10) # 10Hz
        count = 0
        
        while rclpy.ok():
            # 常に最新のパラメータを反映
            max_angular_speed = self.get_parameter('max_angular_speed').value
            kp_angular = self.get_parameter('kp_angular').value
            yaw_tolerance = self.get_parameter('yaw_tolerance').value

            # 1. 現在の誤差を計算 (最短経路)
            yaw_error = self.normalize_angle(target_yaw - self.current_yaw)
            
            # 2. フィードバック送信
            current_yaw_deg = round(math.degrees(self.current_yaw), 2)
            status_msg = f"Rotating... (Err: {math.degrees(yaw_error):.1f} deg)"
            goal_handle.publish_feedback(RotateDegrees.Feedback(current_yaw=current_yaw_deg, status=status_msg))
            
            # 3. 終了判定
            if abs(yaw_error) < yaw_tolerance:
                self.get_logger().info('Target Rotation Reached!')
                break
                
            # 4. 中断チェック
            if goal_handle.is_cancel_requested:
                self.stop_robot()
                goal_handle.canceled()
                return RotateDegrees.Result(success=False)
            
            # 5. 速度計算 (P制御)
            twist = Twist()
            # 最小速度を設けて確実に動くようにする (0.1rad/s)
            min_w = 0.1
            w = kp_angular * yaw_error
            
            if abs(w) > max_angular_speed:
                w = max_angular_speed if w > 0 else -max_angular_speed
            elif abs(w) < min_w:
                w = min_w if w > 0 else -min_w
                
            twist.angular.z = w
            self.cmd_vel_pub.publish(twist)
            
            # ターミナルデバッグ用
            if count % 10 == 0:
                self.get_logger().info(f"Target: {math.degrees(target_yaw):.1f}, Current: {current_yaw_deg:.1f}, ERR: {math.degrees(yaw_error):.1f}rad")
            
            count += 1
            rate.sleep()
            
        self.stop_robot()
        goal_handle.succeed()
        return RotateDegrees.Result(success=True)

    def stop_robot(self):
        self.cmd_vel_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = RotateDegreesNode()
    
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
