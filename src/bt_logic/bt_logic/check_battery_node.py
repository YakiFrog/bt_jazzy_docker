import rclpy
from rclpy.node import Node
from bt_msgs.srv import CheckBattery

class CheckBatteryNode(Node):
    def __init__(self):
        super().__init__('check_battery_node')
        self.srv = self.create_service(CheckBattery, 'check_battery', self.handle_service)
        self.battery_level = 100.0  # 初期値 100%
        self.get_logger().info('CheckBattery Condition Node initialized (Simulated 100%)')

    def handle_service(self, request, response):
        # サービスが呼ばれるたびに 5% ずつ減らしてみる
        self.battery_level -= 5.0
        if self.battery_level < 0: self.battery_level = 0.0

        # request.tekito % 以下なら失敗 (False)
        threshold = request.tekito
        is_ok = self.battery_level > threshold
        
        self.get_logger().info(f'Battery Level: {self.battery_level}% (Threshold: {threshold}%) -> Result: {is_ok}')
        
        response.result = is_ok
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CheckBatteryNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
