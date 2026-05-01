# BT Node Manager ユーザーガイド

`bt_node_manager.py` は、Behavior Tree のスキル開発を GUI で支援する統合ツールです。

## 設定 (Global Config)

画面最上部の **「Trees Directory」** で、ツリーファイルの保存場所を指定します。
*   デフォルト: `/ros2_ws/trees`
*   この設定は、新規ツリーの作成や、Groot2 用のパレット (`nodes_library.xml`) の更新先に反映されます。

## 主な機能

### 1. ノード作成 (Create)
*   **Action (動作)**: 非同期。移動や掃除など「時間のかかる処理」に。
*   **Condition (判定)**: 同期。バッテリーやセンサー値の「状態チェック」に。

### 2. 管理 (Manage)
*   登録されているノードの確認と、不要なノードの「完全削除」が行えます。ソースコード、CMake、XML パレットから関連記述を自動で消去します。

### 3. テスト (Test)
*   作成したノードに直接「引数」を入力して実行できます。
*   **Action**: フィードバック (Feedback) と最終結果 (Result) を確認可能。
*   **Condition**: 判定結果 (True/False) を確認可能。

---

## 開発のコツ
1.  ノードを作ったら、まず `build` して `run_logic` を起動します。
2.  `node_manager` のテストタブで、期待通りの戻り値が返ってくるか確認します。
3.  問題なければ Groot2 でツリーを組み、`run_bt` で動かします。
