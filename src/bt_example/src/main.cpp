#include <iostream>
#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <bt_msgs/action/say_something.hpp>
#include <rclcpp/rclcpp.hpp>

using namespace BT;

/**
 * ROS 2 Action を呼び出す Behavior Tree 用のカスタムノード
 * RosActionNode<アクション型> を継承することで、Action 通信の複雑な処理をライブラリが肩代わりしてくれます。
 */
class SaySomethingAction : public RosActionNode<bt_msgs::action::SaySomething>
{
public:
    SaySomethingAction(const std::string& name,
                       const NodeConfig& conf,
                       const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::SaySomething>(name, conf, params)
    {}

    // このノードで使用するポート（引数）の定義
    static PortsList providedPorts()
    {
        // providedBasicPorts を呼ぶことで、ROS 2 関連の基本ポート（action_name等）も自動的に追加されます
        return providedBasicPorts({ InputPort<std::string>("message", "送信するメッセージ内容") });
    }

    // アクションサーバーへ送る「ゴール（目標）」を設定する関数
    bool setGoal(RosActionNode::Goal& goal) override
    {
        std::string msg;
        // XML 側で指定された "message" ポートの値を取得
        if (!getInput<std::string>("message", msg))
        {
            return false; // メッセージがない場合はエラー
        }
        goal.message = msg;
        return true; // ゴールを送信
    }

    // アクションの実行が完了し、結果（Result）が返ってきた時の処理
    NodeStatus onResultReceived(const RosActionNode::WrappedResult& wr) override
    {
        if (wr.result->success)
        {
            std::cout << "[BT Node] アクション成功!" << std::endl;
            return NodeStatus::SUCCESS; // ツリーに「成功」を返す
        }
        return NodeStatus::FAILURE; // ツリーに「失敗」を返す
    }

    // アクションの実行中、Python 側からフィードバック（途中経過）が届いた時の処理
    virtual NodeStatus onFeedback(const std::shared_ptr<const bt_msgs::action::SaySomething::Feedback> feedback) override
    {
        std::cout << "[BT Node] Python ロジックからの進捗報告: " << feedback->progress << "%" << std::endl;
        return NodeStatus::RUNNING; // 実行中なので RUNNING を返す
    }
};

int main(int argc, char** argv)
{
    // ROS 2 の初期化
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("bt_node_client");

    BehaviorTreeFactory factory;

    // ROS 2 連携用のパラメータ設定
    RosNodeParams params;
    params.nh = node;
    params.default_port_value = "say_something"; // 通信する Action 名のデフォルト値
    
    // カスタムノードを工場 (Factory) に登録
    factory.registerNodeType<SaySomethingAction>("SaySomethingAction", params);

    // Behavior Tree の定義 (XML 形式)
    const std::string xml_text = R"(
    <root BTCPP_format="4">
        <BehaviorTree ID="MainTree">
            <Sequence>
                <SaySomethingAction message="C++ の BT から Python ロジックを呼び出しています！"/>
                <SaySomethingAction message="すべて ROS 2 Action 経由で動いています。"/>
            </Sequence>
        </BehaviorTree>
    </root>
    )";

    // ツリーの作成
    auto tree = factory.createTreeFromText(xml_text);
    
    // Groot2 でリアルタイム監視するためのパブリッシャー
    Groot2Publisher publisher(tree);

    std::cout << "--- BT Node (Action Client) 起動完了 ---" << std::endl;

    // 実行ループ
    while (rclcpp::ok())
    {
        // ツリーを 1 ステップ進める (内部で Action の状態管理を行ってくれます)
        tree.tickWhileRunning();
        
        // ROS 2 の通信イベントを処理
        rclcpp::spin_some(node);
        
        // CPU 負荷を抑えるための待機
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    rclcpp::shutdown();
    return 0;
}
