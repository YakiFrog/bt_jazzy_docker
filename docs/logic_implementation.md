# ロジック実装ガイド (Python)

`node_manager` で生成された各ノードのロジックは、`src/bt_logic/bt_logic/` ディレクトリ内にあります。

## Action ノードの実装 (`*_node.py`)

Action ノードは `execute_callback` 内で処理を行います。

```python
def execute_callback(self, goal_handle):
    # 1. 引数の取得
    target_x = goal_handle.request.x
    
    # 2. 実際のロボット制御（例：ループで少しずつ動かす）
    for i in range(10):
        # 中断チェック
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
            return MoveToTarget.Result(success=False)
            
        # フィードバックの送信
        goal_handle.publish_feedback(MoveToTarget.Feedback(progress=i*10))
        time.sleep(0.5)

    # 3. 完了報告
    goal_handle.succeed()
    return MoveToTarget.Result(success=True)
```

## Condition ノードの実装 (`*_node.py`)

Condition ノードは `handle_service` 内で即座に結果を返します。

```python
def handle_service(self, request, response):
    # 1. 引数の取得
    threshold = request.threshold
    
    # 2. 判定ロジック
    # SUCCESS (True) か FAILURE (False) かを返す
    current_battery = 25.0
    response.result = (current_battery > threshold)
    
    return response
```

---

## ヒント：実機やシミュレータとの連携
この Python ノードは通常の ROS 2 ノードです。
`self.create_subscription` でセンサデータを購読したり、`self.create_publisher` でモータへの指令値を送ったりして、実際のロボットを制御してください。
