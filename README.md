# BehaviorTree.CPP v4 for ROS 2 Jazzy (Docker 開発環境)

このリポジトリは、**ROS 2 Jazzy** 上で **BehaviorTree.CPP v4** を使用するための Docker 開発環境を提供します。

## 特徴
- **ROS 2 Jazzy 対応**: 公式の `ros:jazzy-ros-base` イメージをベースに構築。
- **BehaviorTree.CPP v4 標準搭載**: Jazzy 対応の最新版 (v4.9.0) がプリインストール済み。
- **永続的なワークスペース**: ビルド成果物 (`build`, `install`, `log`) はホスト側に保存されるため、コンテナを消しても再ビルドは不要。
- **サンプルパッケージ同梱**: すぐに動作確認ができる `bt_example` パッケージが含まれています。

## 動作要件
- Docker
- Docker Compose

## クイックスタート

### 1. 初回セットアップ & ビルド
以下のスクリプトを実行して、Docker イメージの作成と ROS 2 ワークスペースのビルドを行います。
```bash
chmod +x setup_workspace.sh
./setup_workspace.sh
```

### 2. 開発環境の起動
コンテナ内に入るには、以下のコマンドを実行します。
```bash
docker compose run --rm bt_dev
```

### 3. サンプルの実行
コンテナ内で、サンプルノードを起動して動作を確認します。
```bash
ros2 run bt_example bt_node
```

## ディレクトリ構成
- `src/`: ROS 2 のソースコード（自分のパッケージはここに追加します）
- `Dockerfile`: コンテナの定義ファイル
- `docker-compose.yml`: コンテナの起動設定・マウント設定
- `setup_workspace.sh`: ビルド用のユーティリティスクリプト
- `build/`, `install/`, `log/`: ビルド成果物（ホスト側に生成されます）

## なぜ Docker 内でビルドするのか？
コンテナ内でビルドを行うことで、どの PC を使っても**「全く同じコンパイラ、全く同じライブラリのバージョン」**で開発を行うことができます。これにより、OS の差異による「自分の環境では動くのに他の人の環境では動かない」といったトラブルを防ぎ、ホスト OS をクリーンに保つことができます。
