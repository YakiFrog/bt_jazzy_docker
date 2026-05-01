# ロジック実装ガイド (Python)

## Condition ノードの実践的なパターン

判定ノードは単に `True/False` を返すだけでなく、**「ツリーからの引数（基準）」と「ロボットの状態」を比較する** のが基本です。

### バッテリーチェックの例
```python
def handle_service(self, request, response):
    # 1. 内部状態の取得（例：シミュレーションやセンサー値）
    self.battery_level -= 1.0 
    
    # 2. ツリーからの引数（しきい値）の取得
    # ノード作成時に設定したポート名（例：threshold）でアクセスします
    threshold = request.threshold
    
    # 3. 判定
    response.result = (self.battery_level > threshold)
    
    self.get_logger().info(f"Battery: {self.battery_level}% (Goal: >{threshold}%)")
    return response
```

## Action ノードの実装ヒント

Action ノードでは、`goal_handle.publish_feedback()` を使うことで、実行中の進捗を BT エンジンや GUI に伝えることができます。

```python
def execute_callback(self, goal_handle):
    # 引数の取得
    target = goal_handle.request.target_name
    
    # 進捗の報告
    goal_handle.publish_feedback(MyAction.Feedback(status="Processing..."))
    
    # 完了
    goal_handle.succeed()
    return MyAction.Result(success=True)
```

---

## 注意点
*   Python ファイルを書き換えた後は、`run_logic` を再起動する必要があります。
*   `colcon build` 時の `--symlink-install` により、Python コードの変更はビルドなしで反映されます。
