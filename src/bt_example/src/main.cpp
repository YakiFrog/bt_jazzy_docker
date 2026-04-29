#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <bt_msgs/action/say_something.hpp>
#include <bt_msgs/action/move_to_target.hpp>
#include <bt_msgs/action/pick_up_item.hpp>
#include <rclcpp/rclcpp.hpp>
#include <bt_msgs/action/clean_room.hpp>

using namespace BT;
class CleanRoomAction : public RosActionNode<bt_msgs::action::CleanRoom>
{
public:
    CleanRoomAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::CleanRoom>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<std::string>("whichroom") });
    }

    bool setGoal(Goal& goal) override {
        getInput("whichroom", goal.whichroom);
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }
};


class PickUpItemAction : public RosActionNode<bt_msgs::action::PickUpItem>
{
public:
    PickUpItemAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::PickUpItem>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<std::string>("item") });
    }

    bool setGoal(Goal& goal) override {
        getInput("item", goal.item);
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }
};


/**
 * 挨拶アクションノード
 */
class SaySomethingAction : public RosActionNode<bt_msgs::action::SaySomething>
{
public:
    SaySomethingAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::SaySomething>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<std::string>("message") });
    }

    bool setGoal(Goal& goal) override {
        getInput("message", goal.message);
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }
};

/**
 * 移動アクションノード (新規追加)
 */
class MoveToTargetAction : public RosActionNode<bt_msgs::action::MoveToTarget>
{
public:
    MoveToTargetAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::MoveToTarget>(name, conf, params) {}

    // ポートの定義: x と y の座標を受け取れるようにします
    static PortsList providedPorts() {
        return providedBasicPorts({ 
            InputPort<float>("x", 0.0, "目標の X 座標"),
            InputPort<float>("y", 0.0, "目標の Y 座標") 
        });
    }

    // ゴールの設定: ポートから読み取った値を Action の Goal に詰め込みます
    bool setGoal(Goal& goal) override {
        if (!getInput("x", goal.x) || !getInput("y", goal.y)) {
            return false;
        }
        return true;
    }

    // 結果の受信
    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }

    // フィードバックの受信: 残り距離をコンソールに表示
    virtual NodeStatus onFeedback(const std::shared_ptr<const bt_msgs::action::MoveToTarget::Feedback> feedback) override {
        std::cout << "[BT] 目標までの残り距離: " << feedback->distance << "m" << std::endl;
        return NodeStatus::RUNNING;
    }
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("bt_node_client");

    BehaviorTreeFactory factory;
    params.default_port_value = "cleanroom";
    factory.registerNodeType<CleanRoomAction>("CleanRoom", params);

    RosNodeParams params;
    params.nh = node;

    params.default_port_value = "pickupitem";
    factory.registerNodeType<PickUpItemAction>("PickUpItem", params);

    // ノードの登録
    params.default_port_value = "say_something";
    factory.registerNodeType<SaySomethingAction>("SaySomething", params);

    params.default_port_value = "move_to_target";
    factory.registerNodeType<MoveToTargetAction>("MoveToTarget", params);

    // XML ファイルからツリーを読み込む
    // コンテナ内の絶対パスを指定します
    auto tree = factory.createTreeFromFile("/ros2_ws/src/bt_example/tree/my_tree.xml");
    
    Groot2Publisher publisher(tree);

    std::cout << "--- BT Mission Started ---" << std::endl;

    while (rclcpp::ok()) {
        tree.tickWhileRunning();
        rclcpp::spin_some(node);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    rclcpp::shutdown();
    return 0;
}
