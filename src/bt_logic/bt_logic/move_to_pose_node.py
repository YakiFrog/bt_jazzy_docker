import time
import math
import rclpy
from rclpy.action import ActionServer, ActionClient, CancelResponse, GoalResponse
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
        self._current_nav2_handle = None  # 現在実行中のNav2ゴールハンドル

        self._action_server = ActionServer(
            self, MoveToPose, 'move_to_pose',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup())

        # Nav2のアクションクライアントを作成
        self._nav2_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=ReentrantCallbackGroup())

        self.get_logger().info('MoveToPose Node initialized, waiting for Nav2 navigate_to_pose action server...')

    def goal_callback(self, goal_request):
        """新しいゴールが来たら前のNav2ゴールをキャンセルしてから受け入れる"""
        self.get_logger().info('New MoveToPose goal received. Preempting previous goal if any...')
        if self._current_nav2_handle is not None:
            try:
                self._current_nav2_handle.cancel_goal()
                self.get_logger().info('Previous Nav2 goal cancel requested.')
            except Exception as e:
                self.get_logger().warn(f'Could not cancel previous Nav2 goal: {e}')
            self._current_nav2_handle = None
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """BTクライアントからのキャンセル要求を受け入れる"""
        self.get_logger().info('MoveToPose cancel requested by BT client.')
        if self._current_nav2_handle is not None:
            try:
                self._current_nav2_handle.cancel_goal()
            except Exception as e:
                self.get_logger().warn(f'Could not cancel Nav2 goal: {e}')
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing MoveToPose...')

        x = goal_handle.request.x
        y = goal_handle.request.y
        degrees = goal_handle.request.degrees
        yaw = math.radians(degrees)  # 度 → ラジアン変換

        self.get_logger().info(f'Received goal coordinate: X={x:.2f}, Y={y:.2f}, Degrees={degrees:.1f}deg ({yaw:.3f}rad)')

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

        # 現在のNav2ゴールハンドルを保存（キャンセル用）
        self._current_nav2_handle = nav2_goal_handle
        self.get_logger().info('Goal accepted by Nav2, waiting for result...')

        # 結果の待機
        get_result_future = nav2_goal_handle.get_result_async()
        await get_result_future

        self._current_nav2_handle = None
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

