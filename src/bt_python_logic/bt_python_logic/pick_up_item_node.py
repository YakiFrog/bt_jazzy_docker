import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import PickUpItem

class PickUpItemNode(Node):
    def __init__(self):
        super().__init__('pick_up_item_node')
        self._action_server = ActionServer(
            self, PickUpItem, 'pickupitem', self.execute_callback)
        self.get_logger().info('PickUpItem Node initialized')

    def execute_callback(self, goal_handle):
        item = goal_handle.request.item
        self.get_logger().info(f'Picking up item: {item}')
        
        # --- [具体的なピッキングロジックをここに実装してください] ---
        # 例: アームの制御ノードに目標姿勢を送る、グリッパーを閉じるなど
        
        time.sleep(1.0)
        
        # ------------------------------------------------------------
        
        goal_handle.succeed()
        return PickUpItem.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = PickUpItemNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
