import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from bt_msgs.action import RotateDegrees
import math
import transforms3d

class RotateDegreesNode(Node):
    def __init__(self):
        super().__init__('rotate_degrees_node')
        
        # パラメータの取得
        self.declare_parameter('odom_topic', '/odom/filtered')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('max_angular_speed', 0.6)
        self.declare_parameter('kp_angular', 0.8)
        self.declare_parameter('yaw_tolerance', 0.05)
        
        self.odom_topic = self.get_parameter('odom_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        
        # サブスクライバとパブリッシャ
        self.odom_sub = self.create_subscription(Odometry, self.odom_topic, self.odom_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        
        self.current_yaw = 0.0
        self._action_server = ActionServer(self, RotateDegrees, 'rotate_degrees', self.execute_callback)
        
        self.get_logger().info('RotateDegrees Node initialized')

    def odom_callback(self, msg):
        # クォータニオンをオイラー角に変換
        q = msg.pose.pose.orientation
        _, _, yaw = transforms3d.euler.quat2euler([q.w, q.x, q.y, q.z])
        self.current_yaw = yaw

    def normalize_angle(self, angle):
        """角度を -pi から pi の範囲に正規化"""
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def execute_callback(self, goal_handle):
        self.get_logger().info(f'Executing RotateDegrees: {goal_handle.request.degrees} degrees')
        
        # 目標角度をラジアンに変換 (相対)
        target_offset_rad = math.radians(goal_handle.request.degrees)
        start_yaw = self.current_yaw
        target_yaw = self.normalize_angle(start_yaw + target_offset_rad)
        
        # パラメータの再取得
        max_angular_speed = self.get_parameter('max_angular_speed').value
        kp_angular = self.get_parameter('kp_angular').value
        yaw_tolerance = self.get_parameter('yaw_tolerance').value
        
        rate = self.create_rate(10)
        count = 0
        
        while rclpy.ok():
            # 1. 現在の誤差を計算 (最短経路)
            yaw_error = self.normalize_angle(target_yaw - self.current_yaw)
            
            # 2. フィードバック
            current_yaw_deg = math.degrees(self.current_yaw)
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
            # 最小速度を設けて確実に動くようにする (0.15rad/s)
            min_w = 0.15
            w = kp_angular * yaw_error
            
            if abs(w) > max_angular_speed:
                w = max_angular_speed if w > 0 else -max_angular_speed
            elif abs(w) < min_w:
                w = min_w if w > 0 else -min_w
                
            twist.angular.z = w
            self.cmd_vel_pub.publish(twist)
            
            if count % 10 == 0:
                self.get_logger().info(f"Target: {math.degrees(target_yaw):.1f}, Current: {current_yaw_deg:.1f}, ERR: {math.degrees(yaw_error):.1f}")
            
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
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()
