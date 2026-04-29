#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h> // Added for Groot2
#include <thread>
#include <chrono>

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
        
        // Add a small delay so we can see the execution in Groot2
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        
        return NodeStatus::SUCCESS;
    }
};

int main()
{
    BehaviorTreeFactory factory;
    factory.registerNodeType<SayHello>("SayHello");

    // Load from file for Groot2 visualization
    auto tree = factory.createTreeFromFile("/ros2_ws/src/bt_example/tree/my_tree.xml");

    // Create the Groot2 Publisher
    // This will allow Groot2 to connect to this process
    Groot2Publisher publisher(tree);

    std::cout << "--- Groot2 Real-time Monitoring Enabled ---" << std::endl;
    std::cout << "1. Open Groot2" << std::endl;
    std::cout << "2. Go to 'Monitor' tab" << std::endl;
    std::cout << "3. Click 'Connect' (IP: 127.0.0.1, Port: 1667)" << std::endl;
    std::cout << "------------------------------------------" << std::endl;

    // Loop forever so we can monitor it
    while (true)
    {
        std::cout << "\nTicking tree..." << std::endl;
        tree.tickWhileRunning();
        
        std::this_thread::sleep_for(std::chrono::seconds(2));
    }

    return 0;
}
