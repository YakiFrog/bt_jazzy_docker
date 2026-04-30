#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <bt_msgs/action/say_something.hpp>
#include <bt_msgs/action/move_to_target.hpp>
#include <bt_msgs/action/pick_up_item.hpp>
#include <bt_msgs/action/clean_room.hpp>
#include <bt_msgs/action/tekito_action.hpp>
#include <rclcpp/rclcpp.hpp>

using namespace BT;

// =============================================================================
// アクションノードの定義
// =============================================================================

class TekitoActionAction : public RosActionNode<bt_msgs::action::TekitoAction>
{
public:
    TekitoActionAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::TekitoAction>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<int>("tekitodane") });
    }

    bool setGoal(Goal& goal) override {
        getInput("tekitodane", goal.tekitodane);
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }
};

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

class MoveToTargetAction : public RosActionNode<bt_msgs::action::MoveToTarget>
{
public:
    MoveToTargetAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::MoveToTarget>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ 
            InputPort<float>("x", 0.0, "目標の X 座標"),
            InputPort<float>("y", 0.0, "目標の Y 座標") 
        });
    }

    bool setGoal(Goal& goal) override {
        if (!getInput("x", goal.x) || !getInput("y", goal.y)) return false;
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }

    virtual NodeStatus onFeedback(const std::shared_ptr<const bt_msgs::action::MoveToTarget::Feedback> feedback) override {
        std::cout << "[BT] 目標までの残り距離: " << feedback->distance << "m" << std::endl;
        return NodeStatus::RUNNING;
    }
};

// =============================================================================
// メイン関数
// =============================================================================

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("bt_node_client");

    // パラメータの宣言 (読み込むXMLファイルを引数で変えられるようにする)
    node->declare_parameter("tree_xml", "/ros2_ws/src/bt_example/tree/my_tree.xml");
    std::string tree_xml_path = node->get_parameter("tree_xml").as_string();

    BehaviorTreeFactory factory;
    RosNodeParams params;
    params.nh = node;

    // --- [ACTION_REGISTRATION_MARKER] ---

    params.default_port_value = "tekito_action";
    factory.registerNodeType<TekitoActionAction>("TekitoAction", params);

    params.default_port_value = "clean_room";
    factory.registerNodeType<CleanRoomAction>("CleanRoom", params);

    params.default_port_value = "pickupitem";
    factory.registerNodeType<PickUpItemAction>("PickUpItem", params);

    params.default_port_value = "say_something";
    factory.registerNodeType<SaySomethingAction>("SaySomething", params);

    params.default_port_value = "move_to_target";
    factory.registerNodeType<MoveToTargetAction>("MoveToTarget", params);

    // XML ファイルからツリーを読み込む
    std::cout << "Loading Tree from: " << tree_xml_path << std::endl;
    auto tree = factory.createTreeFromFile(tree_xml_path);
    
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
