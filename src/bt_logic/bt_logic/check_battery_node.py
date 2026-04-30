import rclpy
from rclpy.node import Node
from bt_msgs.srv import CheckBattery

class CheckBatteryNode(Node):
    def __init__(self):
        super().__init__('check_battery_node')
        self.srv = self.create_service(CheckBattery, 'check_battery', self.handle_service)
        self.get_logger().info('CheckBattery Condition Node initialized')

    def handle_service(self, request, response):
        tekito = request.tekito
        self.get_logger().info(f'Checking CheckBattery: tekito={tekito}')
        
        # --- [判定ロジックをここに記述してください] ---
        # result = True (SUCCESS) or False (FAILURE)
        response.result = True
        # --------------------------------------------
        
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CheckBatteryNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
