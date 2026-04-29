#!/usr/bin/env python3
import os
import sys
import argparse

def add_to_file_before_marker(file_path, content, marker):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    with open(file_path, 'w') as f:
        for line in lines:
            if marker in line:
                f.write(content)
            f.write(line)

def create_action(name, fields):
    # 1. Action ファイルの作成
    action_path = f"src/bt_msgs/action/{name}.action"
    with open(action_path, 'w') as f:
        f.write("# Request\n")
        for field in fields:
            f.write(f"{field.replace(':', ' ')}\n")
        f.write("---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")
    print(f"Created {action_path}")

    # 2. bt_msgs/CMakeLists.txt への追加
    cmake_path = "src/bt_msgs/CMakeLists.txt"
    add_to_file_before_marker(cmake_path, f'  "action/{name}.action"\n', '  DEPENDENCIES action_msgs')
    print(f"Updated {cmake_path}")

    # 3. Python ロジックの雛形追加
    python_path = "src/bt_python_logic/bt_python_logic/action_server.py"
    # Import 追加
    add_to_file_before_marker(python_path, f", {name}", "from bt_msgs.action import")
    
    # サーバー初期化追加
    init_marker = "self.get_logger().info('Python ロジックサーバー"
    init_content = f"        self._{name.lower()}_server = ActionServer(self, {name}, '{name.lower()}', self.{name.lower()}_callback)\n"
    add_to_file_before_marker(python_path, init_content, init_marker)

    # コールバック関数追加
    cb_marker = "def main(args=None):"
    cb_content = f"""    def {name.lower()}_callback(self, goal_handle):
        self.get_logger().info('{name} 実行開始')
        # TODO: ここにロジックを書く
        goal_handle.succeed()
        return {name}.Result(success=True)

"""
    add_to_file_before_marker(python_path, cb_content, cb_marker)
    print(f"Updated {python_path}")

    # 4. C++ BT ノードの追加
    cpp_path = "src/bt_example/src/main.cpp"
    # Include 追加
    add_to_file_before_marker(cpp_path, f'#include <bt_msgs/action/{name.lower()}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
    
    # クラス定義追加
    class_marker = "int main(int argc"
    ports = ", ".join([f'InputPort<{f.split(":")[1]}>("{f.split(":")[0]}")' for f in fields])
    goal_sets = "\n        ".join([f'getInput("{f.split(":")[0]}", goal.{f.split(":")[0]});' for f in fields])
    
    class_content = f"""class {name}Action : public RosActionNode<bt_msgs::action::{name}>
{{
public:
    {name}Action(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
      : RosActionNode<bt_msgs::action::{name}>(name, conf, params) {{}}

    static PortsList providedPorts() {{
        return providedBasicPorts({{ {ports} }});
    }}

    bool setGoal(Goal& goal) override {{
        {goal_sets}
        return true;
    }}

    NodeStatus onResultReceived(const WrappedResult& wr) override {{
        return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
    }}
}};

"""
    add_to_file_before_marker(cpp_path, class_content, class_marker)

    # Factory登録追加
    reg_marker = "auto tree ="
    reg_content = f'    params.default_port_value = "{name.lower()}";\n    factory.registerNodeType<{name}Action>("{name}", params);\n\n'
    add_to_file_before_marker(cpp_path, reg_content, reg_marker)
    print(f"Updated {cpp_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Action name (e.g. CleanRoom)")
    parser.add_argument("fields", nargs="*", help="Fields like name:type (e.g. speed:float32)")
    args = parser.parse_args()
    
    create_action(args.name, args.fields)
    print("\n[完了] ワークスペースを build して src すれば、新しいノードが使えます！")
