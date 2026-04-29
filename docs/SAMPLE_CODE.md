# サンプルコードの解説 (C++ BT + Python Logic)

本プロジェクトでは、Behavior Tree 本体を **C++** で記述し、具体的なロボットのロジック（重い処理や Action Server）を **Python** で記述する、Nav2 と同様の実践的な構成を採用しています。

## 構成の全体像

1. **`bt_msgs`**: 通信用のインターフェース（Action）を定義。
2. **`bt_python_logic`**: Python で書かれたロジック。Action Server として動作。
3. **`bt_example`**: C++ で書かれた Behavior Tree エンジン。Python 側を Action Client として呼び出す。

---

## 1. Python 側のロジック (`action_server.py`)

ロボットの具体的な動きや時間のかかる処理を担当します。

```python
# Action Server の核となるコールバック
def execute_callback(self, goal_handle):
    # BT から届いたメッセージを取得
    message = goal_handle.request.message
    
    # 処理の進捗をフィードバックとして送信 (1%... 100%)
    for i in range(1, 6):
        feedback_msg.progress = i * 20.0
        goal_handle.publish_feedback(feedback_msg)
        time.sleep(0.5)

    # 成功を報告
    goal_handle.succeed()
    return result
```

## 2. C++ 側の Behavior Tree (`main.cpp`)

ツリーの構築と、Python Action Server の呼び出しを担当します。`RosActionNode` という便利なクラスを継承しています。

```cpp
// Python 側の Action を呼び出すための BT ノード定義
class SaySomethingAction : public RosActionNode<bt_msgs::action::SaySomething>
{
    // Goal（リクエスト）の作成
    bool setGoal(Goal& goal) override {
        goal.message = "Hello from BT!";
        return true;
    }

    // Feedback（途中経過）の受信
    NodeStatus onFeedback(const std::shared_ptr<const Feedback> f) override {
        std::cout << "進捗: " << f->progress << "%" << std::endl;
        return NodeStatus::RUNNING;
    }

    // Result（最終結果）の受信
    NodeStatus onResultReceived(const WrappedResult& wr) override {
        return NodeStatus::SUCCESS;
    }
};
```

## 3. 設計図 (`main.cpp` 内の XML 定義)

```xml
<Sequence>
    <SaySomethingAction message="最初の処理を Python で実行"/>
    <SaySomethingAction message="二番目の処理を Python で実行"/>
</Sequence>
```
C++ で作成した `SaySomethingAction` が XML 上でタグとして使われ、直感的にロボットの挙動を組み立てられます。

---

## なぜこの構成にするのか？

- **可視化**: BehaviorTree.CPP v4 を使うことで、Groot2 による強力なデバッグ・監視が可能になります。
- **柔軟性**: ロジック部分を Python で書くことで、開発スピードが向上し、ライブラリの利用も容易になります。
- **標準的**: これは ROS 2 のナビゲーションスタック (Nav2) で採用されている世界標準の設計思想です。
