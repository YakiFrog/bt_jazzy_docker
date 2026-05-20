#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <bt_msgs/action/say_something.hpp>
#include <bt_msgs/action/move_to_target.hpp>
#include <bt_msgs/action/pick_up_item.hpp>
#include <bt_msgs/action/clean_room.hpp>
#include <bt_msgs/action/tekito_action.hpp>
#include <bt_msgs/action/rotate_degrees.hpp>
#include <rclcpp/rclcpp.hpp>
#include <bt_msgs/action/move_to_pose.hpp>
#include <bt_msgs/action/set_face_expression.hpp>

#include <bt_msgs/srv/condition_check.hpp>
#include <bt_msgs/srv/check_battery.hpp>

using namespace BT;

// =============================================================================
// サービス通信用ベースクラス (判定ノード用)
// =============================================================================
template <class ServiceT>
class RosServiceNode : public BT::ConditionNode {
public:
    RosServiceNode(const std::string& name, const BT::NodeConfig& conf, const RosNodeParams& params)
        : BT::ConditionNode(name, conf), node_(params.nh) {
        // ノード名と同じ名前のサービスを呼ぶ
        client_ = node_->create_client<ServiceT>(name);
    }

    BT::NodeStatus tick() override {
        if (!client_->wait_for_service(std::chrono::milliseconds(500))) {
            return BT::NodeStatus::FAILURE;
        }

        auto request = std::make_shared<typename ServiceT::Request>();
        if (!setRequest(request)) return BT::NodeStatus::FAILURE;

        auto future = client_->async_send_request(request);
        // 判定ノードは即座に結果が欲しいので同期的に待つ
        if (rclcpp::spin_until_future_complete(node_, future, std::chrono::seconds(1)) != rclcpp::FutureReturnCode::SUCCESS) {
            return BT::NodeStatus::FAILURE;
        }

        auto response = future.get();
        return onResponseReceived(response) ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
    }

    virtual bool setRequest(std::shared_ptr<typename ServiceT::Request>& request) = 0;
    virtual bool onResponseReceived(const std::shared_ptr<typename ServiceT::Response>& response) = 0;

protected:
    rclcpp::Node::SharedPtr node_;
    typename rclcpp::Client<ServiceT>::SharedPtr client_;
};

// --- [NODE_CLASS_MARKER] ---
class MoveToPoseAction : public RosActionNode<bt_msgs::action::MoveToPose>
{
public:
    MoveToPoseAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params) : RosActionNode<bt_msgs::action::MoveToPose>(name, conf, params) {}
    static PortsList providedPorts() { return providedBasicPorts({ InputPort<float>("x"), InputPort<float>("y"), InputPort<float>("degrees", 0.0f, "目的地の向き [度] (0=正面向き)") }); }
    bool setGoal(Goal& goal) override { 
        if (!getInput("x", goal.x) || !getInput("y", goal.y)) return false;
        getInput("degrees", goal.degrees); // degrees is optional (default 0)
        return true; 
    }
    NodeStatus onResultReceived(const WrappedResult& wr) override { return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE; }
    NodeStatus onFeedback(const std::shared_ptr<const bt_msgs::action::MoveToPose::Feedback> feedback) override {
        std::cout << "[BT] Nav2 remaining distance: " << feedback->distance << "m" << std::endl;
        return NodeStatus::RUNNING;
    }
};

class SetFaceExpressionAction : public RosActionNode<bt_msgs::action::SetFaceExpression>
{
public:
    SetFaceExpressionAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params) : RosActionNode<bt_msgs::action::SetFaceExpression>(name, conf, params) {}
    static PortsList providedPorts() { return providedBasicPorts({ InputPort<std::string>("expression") }); }
    bool setGoal(Goal& goal) override { getInput("expression", goal.expression);
        return true; }
    NodeStatus onResultReceived(const WrappedResult& wr) override { return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE; }
};


class CheckBatteryCondition : public RosServiceNode<bt_msgs::srv::CheckBattery>
{
public:
    CheckBatteryCondition(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosServiceNode<bt_msgs::srv::CheckBattery>(name, conf, params) {}

    static PortsList providedPorts() {
        return { InputPort<float>("tekito") };
    }

    bool setRequest(std::shared_ptr<bt_msgs::srv::CheckBattery::Request>& request) override {
        getInput("tekito", request->tekito);
        return true;
    }

    bool onResponseReceived(const std::shared_ptr<bt_msgs::srv::CheckBattery::Response>& response) override {
        return response->result;
    }
};

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

class RotateDegreesAction : public RosActionNode<bt_msgs::action::RotateDegrees>
{
public:
    RotateDegreesAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::RotateDegrees>(name, conf, params) {}

    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<float>("degrees", 0.0, "回転させる角度 (度)") });
    }

    bool setGoal(Goal& goal) override {
        if (!getInput("degrees", goal.degrees)) return false;
        return true;
    }

    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }
};

// =============================================================================
// メイン関数
// =============================================================================

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("bt_node_client");

    // DDSディスカバリの同期を待つために、初期化直後にノードを少しスピンする
    // ※マルチマシン・コンテナ間通信ではディスカバリに数秒かかるため長めに設定
    RCLCPP_INFO(node->get_logger(), "Waiting for DDS discovery to sync...");
    for (int i = 0; i < 50; ++i) {
        rclcpp::spin_some(node);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // パラメータの宣言 (読み込むXMLファイルを引数で変えられるようにする)
    node->declare_parameter("tree_xml", "/ros2_ws/trees/my_tree.xml");
    std::string tree_xml_path = node->get_parameter("tree_xml").as_string();

    node->declare_parameter("loop_tree", false);
    bool loop_tree = node->get_parameter("loop_tree").as_bool();

    BehaviorTreeFactory factory;
    RosNodeParams params;
    params.nh = node;

    // --- [ACTION_REGISTRATION_MARKER] ---
    params.default_port_value = "move_to_pose";
    factory.registerNodeType<MoveToPoseAction>("MoveToPose", params);
    params.default_port_value = "set_face_expression";
    factory.registerNodeType<SetFaceExpressionAction>("SetFaceExpression", params);
    params.default_port_value = "check_battery";
    factory.registerNodeType<CheckBatteryCondition>("CheckBattery", params);

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

    params.default_port_value = "rotate_degrees";
    factory.registerNodeType<RotateDegreesAction>("RotateDegrees", params);

    // XML ファイルからツリーを読み込む
    std::cout << "Loading Tree from: " << tree_xml_path << std::endl;
    auto tree = factory.createTreeFromFile(tree_xml_path);
    
    Groot2Publisher publisher(tree);

    if (loop_tree) {
        std::cout << "--- BT Mission Started (Loop Mode) ---" << std::endl;
        while (rclcpp::ok()) {
            tree.tickWhileRunning();
            rclcpp::spin_some(node);
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    } else {
        std::cout << "--- BT Mission Started (Single-Run Mode) ---" << std::endl;
        NodeStatus status = NodeStatus::RUNNING;
        while (rclcpp::ok() && status == NodeStatus::RUNNING) {
            status = tree.tickExactlyOnce();
            rclcpp::spin_some(node);
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        std::cout << "--- BT Mission Finished with status: " << toStr(status) << " ---" << std::endl;
    }

    rclcpp::shutdown();
    return 0;
}
