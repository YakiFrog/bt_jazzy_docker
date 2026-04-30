# ROS 2 Jazzy Behavior Tree & Logic Studio

このリポジトリは、ROS 2 Jazzy 環境で **Behavior Tree (C++)** と **ロボット技能ロジック (Python)** を高度に統合し、爆速で開発するためのスタジオ環境です。

---

## 🛠️ コアコンポーネント

| コンポーネント | 役割 | 言語 |
| :--- | :--- | :--- |
| **[bt_core](src/bt_core/)** | 「知能」：ツリーの実行エンジン。Groot2 で設計した XML を読み込みます。 | C++ |
| **[bt_logic](src/bt_logic/)** | 「技能」：各アクションや判定の具体的な制御ロジック（ROS 2 ノード群）。 | Python |
| **[bt_msgs](src/bt_msgs/)** | 通信インターフェース：Action と Service の定義。 | ROS 2 Interfaces |
| **[bt_node_manager.py](bt_node_manager.py)** | **管理スタジオ (GUI)**：ノードの生成、削除、単体テストを完結させます。 | Python (PySide6) |

---

## 🚀 開発の黄金サイクル

この環境では、以下の 3 ステップでロボットに新しいスキルを追加できます。

### 1. 技能の生成とテスト
`node_manager` コマンドで GUI を起動し、新しいアクション（Action）や判定（Condition）を作成します。
作成後、**「Test」タブ** を使って、ツリーを組む前にそのノードが単体で正しく動くか確認できます。

### 2. ツリーの設計
[Groot2](https://www.behaviortree.dev/groot/) を開き、`src/bt_core/tree/nodes_library.xml` を読み込んでツリーを設計します。作成したノードは自動的にパレットに追加されています。

### 3. ビルドと実行
ビルドして、知能と技能をそれぞれ起動します。
```bash
build       # 全パッケージのビルド
run_logic   # 技能サーバー（Python ノード群）の起動
run_bt      # 知能（BT Core）の起動
```

---

## 📖 詳細ドキュメント

より詳しい使い方は、以下のガイドを参照してください。

*   **[BT Node Manager の使い方](docs/node_manager.md)**: GUI を使ったスキルの作り方とテスト方法。
*   **[ロジックの実装ガイド](docs/logic_implementation.md)**: 生成された Python ファイルのどこにコードを書くべきか。
*   **[アーキテクチャ詳細](docs/architecture.md)**: 知能(C++)と技能(Python)がどのように通信しているか。

---

## 🖥️ 便利なエイリアス一覧
コンテナ内では以下の短縮コマンドが使えます。

- `build`: パッケージ全体のビルド (`colcon build`)
- `src`: 環境変数の反映 (`source install/setup.bash`)
- `node_manager`: **BT Node Manager (GUI)** の起動
- `run_logic`: 全アクション/判定ノードの起動
- `run_bt`: Behavior Tree 本体の起動
