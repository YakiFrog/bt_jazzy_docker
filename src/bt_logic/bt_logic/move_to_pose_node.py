import time
import math
import rclpy
from rclpy.action import ActionServer, ActionClient
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from bt_msgs.action import MoveToPose
from nav_msgs.msg import Odometry
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped

class MoveToPoseNode(Node):
    def __init__(self):
        super().__init__('move_to_pose_node')
        self._action_server = ActionServer(
            self, MoveToPose, 'move_to_pose', 
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup())
            
        # Nav2のアクションクライアントを作成
        self._nav2_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=ReentrantCallbackGroup())
            
        self.get_logger().info('MoveToPose Node initialized, waiting for Nav2 navigate_to_pose action server...')

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing MoveToPose...')
        
        x = goal_handle.request.x
        y = goal_handle.request.y
        yaw = goal_handle.request.yaw
        
        self.get_logger().info(f'Received goal coordinate: X={x:.2f}, Y={y:.2f}, Yaw={yaw:.2f}')
        
        # Nav2アクションサーバーの存在チェック (タイムアウト5秒)
        if not self._nav2_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Nav2 navigate_to_pose action server not available!')
            goal_handle.abort()
            return MoveToPose.Result(success=False)
            
        # Nav2の目標作成
        nav2_goal = NavigateToPose.Goal()
        nav2_goal.pose.header.frame_id = 'map'
        nav2_goal.pose.header.stamp = self.get_clock().now().to_msg()
        
        nav2_goal.pose.pose.position.x = float(x)
        nav2_goal.pose.pose.position.y = float(y)
        nav2_goal.pose.pose.position.z = 0.0
        
        # Yawからクォータニオンを計算
        nav2_goal.pose.pose.orientation.x = 0.0
        nav2_goal.pose.pose.orientation.y = 0.0
        nav2_goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        nav2_goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        self.get_logger().info('Sending goal to Nav2...')
        
        # 進行状況のフィードバック受信用クロージャ
        def nav2_feedback_callback(feedback_msg):
            distance = feedback_msg.feedback.distance_remaining
            self.get_logger().info(f'Nav2 Feedback: Remaining Distance = {distance:.2f}m', throttle_duration_sec=1.0)
            goal_handle.publish_feedback(MoveToPose.Feedback(distance=distance))
            
        # アクション送信
        send_goal_future = self._nav2_client.send_goal_async(
            nav2_goal,
            feedback_callback=nav2_feedback_callback)
            
        # ゴール受付完了を待機
        await send_goal_future
        nav2_goal_handle = send_goal_future.result()
        
        if not nav2_goal_handle.accepted:
            self.get_logger().error('Goal rejected by Nav2!')
            goal_handle.abort()
            return MoveToPose.Result(success=False)
            
        self.get_logger().info('Goal accepted by Nav2, waiting for result...')
        
        # 結果の待機
        get_result_future = nav2_goal_handle.get_result_async()
        await get_result_future
        
        nav2_status = get_result_future.result().status
        # STATUS_SUCCEEDED = 4
        if nav2_status == 4:
            self.get_logger().info('Nav2 navigation completed successfully!')
            goal_handle.succeed()
            return MoveToPose.Result(success=True)
        else:
            self.get_logger().warn(f'Nav2 navigation failed or was canceled (Status code: {nav2_status})')
            goal_handle.abort()
            return MoveToPose.Result(success=False)

def main(args=None):
    rclpy.init(args=args)
    node = MoveToPoseNode()
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
