# 新しい振る舞い（Action）の開発フロー

このドキュメントでは、新しいロボットの動作を追加する際の手順と、設計思想について解説します。

---

## 1. 設計思想：なぜ Action なのか？

Behavior Tree (BT) において、各ノードはロボットの **「状態 (State)」** を表します。ROS 2 の Action 通信を使う理由は、BT の要求する以下の特性を満たすためです。

- **非同期性**: 動作中に BT をブロックせず、「実行中 (RUNNING)」という状態を維持できる。
- **中断可能性 (Preemption)**: より優先度の高いイベントが発生した際、実行中の動作を安全にキャンセルできる。
- **フィードバック**: 動作の進捗を確認し、それに応じた判断ができる。

---

## 2. 開発ステップ（具体例：MoveToTarget アクション）

### ステップ 1：通信（Action）の定義
`src/bt_msgs/action/` に新しい `.action` ファイルを作成し、`CMakeLists.txt` に追記します。

```text
# MoveToTarget.action
float32 x
float32 y
---
bool success
---
float32 distance
```

### ステップ 2：ロジック（Python）の実装
`src/bt_python_logic` 内で、実際の動き（計算やモーター制御）を担当するサーバーを実装します。

```python
def move_to_target_callback(self, goal_handle):
    target_x = goal_handle.request.x
    target_y = goal_handle.request.y
    
    # ループ内で進捗（残り距離）を計算して送信
    while dist > 0.1:
        feedback_msg.distance = current_dist
        goal_handle.publish_feedback(feedback_msg)
        time.sleep(0.5)

    goal_handle.succeed()
    return MoveToTarget.Result(success=True)
```

### ステップ 3：BT ノード（C++）の実装
`src/bt_example/src/main.cpp` に、Python 側を呼び出すためのノードを作成します。

```cpp
class MoveToTargetAction : public RosActionNode<bt_msgs::action::MoveToTarget>
{
    // XMLから目標座標(x, y)を受け取るポート定義
    static PortsList providedPorts() {
        return providedBasicPorts({ InputPort<float>("x"), InputPort<float>("y") });
    }

    // Pythonサーバーへ送るゴールの設定
    bool setGoal(Goal& goal) override {
        getInput("x", goal.x);
        getInput("y", goal.y);
        return true;
    }
};
```

### ステップ 4：工場の登録と XML での使用
```cpp
// main関数内での登録
factory.registerNodeType<MoveToTargetAction>("MoveToTarget", params);
```

```xml
<!-- XML上での使用例 -->
<Sequence>
    <MoveToTarget x="5.0" y="5.0"/>
    <SaySomething message="到着しました"/>
</Sequence>
```

---

## 3. 開発のコツ

- **ノードはシンプルに**: 一つのノードに複雑な条件分岐を詰め込まず、「前進する」「挨拶する」といった単純なアクションに分割してください。
- **再利用性を考える**: 汎用的なアクションを作っておけば、XML を書き換えるだけで様々なミッションに対応できるようになります。
- **Groot2 で監視する**: 実行中は常に Groot2 で接続し、視覚的にデバッグを行ってください。
