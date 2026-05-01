# 環境構築ガイド (Setup Guide)

このプロジェクトは Docker を使用しているため、ホスト OS に依存せず開発環境を構築できます。

## 1. 準備 (Prerequisites)

ホストマシンに以下のツールがインストールされている必要があります。

*   **Docker**: [公式のインストール手順](https://docs.docker.com/get-docker/)に従ってください。
*   **NVIDIA Container Toolkit** (GPU を使用する場合): NVIDIA 製 GPU を搭載している場合は必須です。
*   **X11 Server**: コンテナから GUI (Groot2 や Node Manager) を表示するために必要です。
    *   Linux: 標準でインストールされています。
    *   Windows: VcXsrv や GWSL などが必要です。

## 2. ビルドと起動

リポジトリのルートディレクトリで以下の手順を実行します。

### ステップ 1: セットアップスクリプトの実行
ワークスペースの初期化とパーミッション設定を行います。
```bash
./setup_workspace.sh
```

### ステップ 2: コンテナの起動
`bt_start`（または `docker-compose up -d`）を実行してコンテナを起動します。
```bash
# ホスト側のエイリアスを設定している場合
bt_start
```

### ステップ 3: コンテナ内に入る
```bash
bt_enter
```

## 3. GUI の表示設定

コンテナからホストのディスプレイに画面を出すため、ホスト側で以下のコマンドを実行して X11 接続を許可しておく必要があります。
```bash
xhost +local:docker
```
※ `bt_start` スクリプト内で自動実行されるように設定されている場合もあります。

## 4. 初回ビルド

コンテナ内に入ったら、まず ROS 2 パッケージをビルドします。
```bash
build
src
```

---

## トラブルシューティング

### Q. `node_manager` や `Groot2` が開かない
*   ホスト側で `xhost +local:docker` を実行しましたか？
*   `DISPLAY` 環境変数が正しく設定されているか確認してください。

### Q. ビルドエラーが出る
*   `rm -rf build/ install/ log/` を実行して、クリーンビルドを試してください。
