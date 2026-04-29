#include <iostream>
#include <behaviortree_cpp/bt_factory.h>

using namespace BT;

// Custom Action
class SayHello : public SyncActionNode
{
public:
    SayHello(const std::string& name, const NodeConfig& config)
        : SyncActionNode(name, config)
    {}

    static PortsList providedPorts()
    {
        return { InputPort<std::string>("message") };
    }

    NodeStatus tick() override
    {
        std::string msg;
        if (!getInput<std::string>("message", msg))
        {
            throw RuntimeError("missing required input [message]");
        }
        std::cout << "Robot says: " << msg << std::endl;
        return NodeStatus::SUCCESS;
    }
};

int main()
{
    BehaviorTreeFactory factory;

    // Register custom action
    factory.registerNodeType<SayHello>("SayHello");

    // Define the tree structure in XML
    const std::string xml_text = R"(
     <root BTCPP_format="4">
         <BehaviorTree ID="MainTree">
            <Sequence name="root_sequence">
                <SayHello message="Hello BehaviorTree.CPP v4!"/>
                <SayHello message="This is running in ROS 2 Jazzy."/>
            </Sequence>
         </BehaviorTree>
     </root>
    )";

    // Create the tree
    auto tree = factory.createTreeFromText(xml_text);

    // Execute the tree from text (already done)
    std::cout << "--- Executing tree from text ---" << std::endl;
    tree.tickWhileRunning();

    // Demonstrate loading from file
    std::cout << "\n--- Executing tree from file ---" << std::endl;
    // Note: In a real ROS 2 app, you'd use ament_index_cpp to find the file path
    auto tree_from_file = factory.createTreeFromFile("/ros2_ws/src/bt_example/tree/my_tree.xml");
    tree_from_file.tickWhileRunning();

    return 0;
}
