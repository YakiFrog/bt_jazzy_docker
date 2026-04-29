import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import SaySomething

class SaySomethingActionServer(Node):
    """
    Python で記述されたロジック側（アクションサーバー）
    具体的なロボットの処理や時間のかかる計算はここで行います。
    """
    def __init__(self):
        super().__init__('say_something_action_server')
        # アクションサーバーの初期化
        # サービス名: 'say_something'
        self._action_server = ActionServer(
            self,
            SaySomething,
            'say_something',
            self.execute_callback)
        self.get_logger().info('Python ロジック（Action Server）が起動しました。')

    def execute_callback(self, goal_handle):
        """
        BT ノードからリクエスト（Goal）が届いた時に呼ばれるメインロジック
        """
        message = goal_handle.request.message
        self.get_logger().info(f'リクエストを受信: "{message}"')
        
        feedback_msg = SaySomething.Feedback()
        
        # ここに具体的なロジック（例: ロボットを動かす、計算するなど）を記述します
        # 今回はループを回して進捗を報告するサンプルです
        for i in range(1, 6):
            # 進捗率（Feedback）を設定
            feedback_msg.progress = i * 20.0
            self.get_logger().info(f'ロジック実行中... 進捗: {feedback_msg.progress}%')
            
            # BT 側に途中経過を送信
            goal_handle.publish_feedback(feedback_msg)
            
            # 処理時間のシミュレート
            time.sleep(0.5)

        # 全ての処理が正常に完了したことを報告
        goal_handle.succeed()
        self.get_logger().info('ロジック完了。')

        # 最終的な実行結果（Result）を返す
        result = SaySomething.Result()
        result.success = True
        return result

def main(args=None):
    rclpy.init(args=args)
    # ノードを生成して実行
    action_server = SaySomethingActionServer()
    try:
        rclpy.spin(action_server)
    except KeyboardInterrupt:
        pass
    action_server.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
