import time
import rclpy
import grpc
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import SaySomething

import sys
import os
# Add current directory to path so that the gRPC imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import face_control_pb2
import face_control_pb2_grpc

class SaySomethingNode(Node):
    def __init__(self):
        super().__init__('say_something_node')
        self._action_server = ActionServer(
            self, SaySomething, 'say_something', self.execute_callback)
        self.get_logger().info('SaySomething Node initialized')

    def execute_callback(self, goal_handle):
        message = goal_handle.request.message
        self.get_logger().info(f'Executing SaySomething: {message}')
        
        # 50052番ポートのPythonControlServiceへgRPCでSpeak指令を送信
        target = 'localhost:50052'
        try:
            with grpc.insecure_channel(target) as channel:
                stub = face_control_pb2_grpc.PythonControlServiceStub(channel)
                request = face_control_pb2.SpeakRequest(text=message)
                stub.Speak(request)
            self.get_logger().info(f'Successfully sent Speak request to {target}')
        except Exception as e:
            self.get_logger().error(f'Failed to send Speak request: {e}')

        # テキストの長さから大体の発話時間（秒）を推測して待機する（1文字約0.2秒、最小1.5秒）
        # ※タグ部分（[happy]など）は文字数カウントから除外
        clean_text = message
        while '[' in clean_text and ']' in clean_text:
            start = clean_text.find('[')
            end = clean_text.find(']')
            if start < end:
                clean_text = clean_text[:start] + clean_text[end+1:]
            else:
                break
        
        char_count = len(clean_text)
        duration = max(1.5, char_count * 0.25 + 0.5)
        self.get_logger().info(f'Estimated speaking duration: {duration:.2f}s')

        # 待機しつつフィードバックを返す
        steps = 10
        sleep_step = duration / steps
        for i in range(1, steps + 1):
            goal_handle.publish_feedback(SaySomething.Feedback(progress=i * (100.0 / steps)))
            time.sleep(sleep_step)
            
        goal_handle.succeed()
        return SaySomething.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = SaySomethingNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
