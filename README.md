# ROS 2 Jazzy Behavior Tree & Logic Studio

このリポジトリは、ROS 2 Jazzy 環境で **Behavior Tree (C++)** と **ロボット技能ロジック (Python)** を高度に統合し、爆速で開発するためのスタジオ環境です。

---

## 🛠️ コアコンポーネント

| コンポーネント | 役割 | 言語 |
| :--- | :--- | :--- |
| **[trees/](trees/)** | **知能の設計図**：Groot2 で設計した XML ファイル（ミッション）をここに集約します。 | XML |
| **[bt_core](src/bt_core/)** | **知能の実行部**：ツリーの実行エンジン。XML を読み込んで各スキルを動かします。 | C++ |
| **[bt_logic](src/bt_logic/)** | **技能の実装部**：各アクションや判定の具体的な制御ロジック（ROS 2 ノード群）。 | Python |
| **[bt_msgs](src/bt_msgs/)** | **通信の定義**：Action と Service の型定義。 | ROS 2 Interfaces |
| **[bt_node_manager.py](bt_node_manager.py)** | **管理スタジオ (GUI)**：ノードの生成、削除、単体テストを完結させます。 | Python (PySide6) |

---

## 🚀 開発の黄金サイクル

### 1. スキルの生成とテスト
`node_manager` コマンドで GUI を起動し、新しいアクション（Action）や判定（Condition）を作成。
**「Test」タブ** を使い、ノードが単体で正しく動くか（内部ログや戻り値）を確認します。

### 2. ミッションの設計 (Groot2)
Groot2 を開き、`trees/nodes_library.xml` を読み込んでツリーを設計し、`trees/` 内に保存します。

### 3. ビルドと実行
```bash
build       # 全パッケージのビルド
run_logic   # 技能サーバー（Python ノード群）の起動
run_bt      # 知能の起動。番号で XML を選択できます 🆕
```

---

## 📖 詳細ドキュメント

*   **[環境構築ガイド](docs/setup.md)**: 最初に読んでください。Docker のビルドや GUI 設定について。 🆕
*   **[BT Node Manager の使い方](docs/node_manager.md)**: GUI を使ったスキルの作り方とテスト方法。
*   **[ロジックの実装ガイド](docs/logic_implementation.md)**: Python ロジックの書き方と実践的な判定例。
*   **[トラブルシューティング](docs/troubleshooting.md)**: よくあるエラー（XML の引数漏れなど）の解決策。 🆕
*   **[アーキテクチャ詳細](docs/architecture.md)**: システム全体の通信構造について。

---

## 🖥️ 便利なエイリアス
- `node_manager`: BT Node Manager (GUI) の起動
- `run_logic`: 全アクション/判定ノードの起動
- `run_bt`: インタラクティブなツリー実行（番号選択式）
- `build`: `colcon build` の実行
- `src`: `source install/setup.bash` の実行
