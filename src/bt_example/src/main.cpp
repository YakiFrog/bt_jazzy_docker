#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <bt_msgs/action/say_something.hpp>
#include <rclcpp/rclcpp.hpp>

using namespace BT;

// Define the BT Node that calls the ROS 2 Action
class SaySomethingAction : public RosActionNode<bt_msgs::action::SaySomething>
{
public:
    SaySomethingAction(const std::string& name,
                       const NodeConfig& conf,
                       const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::SaySomething>(name, conf, params)
    {}

    // Define the input ports
    static PortsList providedPorts()
    {
        return providedBasicPorts({ InputPort<std::string>("message") });
    }

    // This function is called to create the goal message
    bool setGoal(RosActionNode::Goal& goal) override
    {
        std::string msg;
        if (!getInput<std::string>("message", msg))
        {
            return false;
        }
        goal.message = msg;
        return true;
    }

    // This function is called when the result is received
    NodeStatus onResultReceived(const RosActionNode::WrappedResult& wr) override
    {
        if (wr.result->success)
        {
            std::cout << "[BT Node] Action succeeded!" << std::endl;
            return NodeStatus::SUCCESS;
        }
        return NodeStatus::FAILURE;
    }

    // This function is called when feedback is received
    virtual NodeStatus onFeedback(const std::shared_ptr<const bt_msgs::action::SaySomething::Feedback> feedback) override
    {
        std::cout << "[BT Node] Progress from Python Logic: " << feedback->progress << "%" << std::endl;
        return NodeStatus::RUNNING;
    }
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("bt_node_client");

    BehaviorTreeFactory factory;

    // Register the ROS Action Node
    RosNodeParams params;
    params.nh = node;
    params.default_port_value = "say_something"; // The action name
    
    factory.registerNodeType<SaySomethingAction>("SaySomethingAction", params);

    // Tree definition
    const std::string xml_text = R"(
    <root BTCPP_format="4">
        <BehaviorTree ID="MainTree">
            <Sequence>
                <SaySomethingAction message="Calling Python logic from C++ BT!"/>
                <SaySomethingAction message="Everything is working through ROS 2 Actions."/>
            </Sequence>
        </BehaviorTree>
    </root>
    )";

    auto tree = factory.createTreeFromText(xml_text);
    Groot2Publisher publisher(tree);

    std::cout << "--- BT Node (Action Client) Started ---" << std::endl;

    while (rclcpp::ok())
    {
        tree.tickWhileRunning();
        rclcpp::spin_some(node);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    rclcpp::shutdown();
    return 0;
}
