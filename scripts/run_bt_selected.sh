#!/bin/bash

# ROS 2 環境の読み込み
if [ -f "/ros2_ws/install/setup.bash" ]; then
    source "/ros2_ws/install/setup.bash"
fi

TREES_DIR="/ros2_ws/trees"

echo "------------------------------------------------"
    echo "  Behavior Tree XML Selector"
echo "------------------------------------------------"

# XMLファイルのリストを取得
cd "$TREES_DIR" || exit
trees=($(ls *.xml 2>/dev/null))

if [ ${#trees[@]} -eq 0 ]; then
    echo "エラー: $TREES_DIR にツリーファイル (.xml) が見つかりません。"
    exit 1
fi

echo "実行するツリーを選択してください:"
for i in "${!trees[@]}"; do
    echo "  [$i] ${trees[$i]}"
done

read -p "選択 (番号を入力, 未入力で 0番): " choice
choice=${choice:-0} # デフォルトは0

if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -ge "${#trees[@]}" ]; then
    echo "エラー: 無効な選択です。"
    exit 1
fi

SELECTED_TREE="${trees[$choice]}"
SELECTED_PATH="$TREES_DIR/$SELECTED_TREE"

echo "------------------------------------------------"
echo "次のツリーを実行中: $SELECTED_TREE"
echo "------------------------------------------------"

ros2 run bt_core bt_node --ros-args -p tree_xml:="$SELECTED_PATH"
