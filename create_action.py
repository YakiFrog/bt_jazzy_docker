#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import messagebox, ttk

def add_to_file_before_marker(file_path, content, marker):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # すでに存在するかチェック
    if content.strip() in "".join(lines):
        return

    with open(file_path, 'w') as f:
        for line in lines:
            if marker in line:
                f.write(content)
            f.write(line)

class ActionCreatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ROS 2 / BT Action Scaffolder")
        self.root.geometry("500x500")

        # アクション名
        tk.Label(root, text="Action Name (e.g. MoveRobot):", font=('Arial', 10, 'bold')).pack(pady=5)
        self.name_entry = tk.Entry(root, font=('Arial', 12), width=30)
        self.name_entry.pack(pady=5)

        # フィールド一覧
        tk.Label(root, text="Fields (Arguments):", font=('Arial', 10, 'bold')).pack(pady=10)
        
        self.fields_frame = tk.Frame(root)
        self.fields_frame.pack()
        
        self.field_rows = []
        self.add_field_row()

        tk.Button(root, text="+ Add Field", command=self.add_field_row, bg="#e1e1e1").pack(pady=5)

        # 作成ボタン
        tk.Button(root, text="GENERATE ACTION", command=self.generate, bg="#4CAF50", fg="white", font=('Arial', 12, 'bold'), height=2, width=20).pack(pady=30)

    def add_field_row(self):
        row = tk.Frame(self.fields_frame)
        row.pack(pady=2)
        
        name_ent = tk.Entry(row, width=15)
        name_ent.insert(0, "field_name")
        name_ent.pack(side=tk.LEFT, padx=5)
        
        type_var = tk.StringVar(value="float32")
        type_opt = ttk.Combobox(row, textvariable=type_var, values=["float32", "int32", "string", "bool"], width=10)
        type_opt.pack(side=tk.LEFT, padx=5)
        
        self.field_rows.append((name_ent, type_opt))

    def generate(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Action Name is required!")
            return

        fields = []
        for n_ent, t_opt in self.field_rows:
            f_name = n_ent.get().strip()
            if f_name and f_name != "field_name":
                fields.append(f"{f_name}:{t_opt.get()}")

        try:
            self.create_action_files(name, fields)
            messagebox.showinfo("Success", f"Action '{name}' has been created successfully!\n\nPlease rebuild with 'build' command.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_action_files(self, name, fields):
        # --- 1. .action ---
        os.makedirs("src/bt_msgs/action", exist_ok=True)
        with open(f"src/bt_msgs/action/{name}.action", 'w') as f:
            f.write("# Request\n")
            for fld in fields:
                f.write(f"{fld.replace(':', ' ')}\n")
            f.write("---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")

        # --- 2. CMakeLists.txt ---
        add_to_file_before_marker("src/bt_msgs/CMakeLists.txt", f'  "action/{name}.action"\n', '  DEPENDENCIES action_msgs')

        # --- 3. Python Server ---
        py_path = "src/bt_python_logic/bt_python_logic/action_server.py"
        add_to_file_before_marker(py_path, f", {name}", "from bt_msgs.action import")
        add_to_file_before_marker(py_path, f"        self._{name.lower()}_server = ActionServer(self, {name}, '{name.lower()}', self.{name.lower()}_callback)\n", "self.get_logger().info('Python ロジックサーバー")
        
        cb_content = f"""    def {name.lower()}_callback(self, goal_handle):
        self.get_logger().info('{name} 実行開始')
        # TODO: ロジックをここに書く
        goal_handle.succeed()
        return {name}.Result(success=True)

"""
        add_to_file_before_marker(py_path, cb_content, "def main(args=None):")

        # --- 4. C++ BT Node ---
        cpp_path = "src/bt_example/src/main.cpp"
        add_to_file_before_marker(cpp_path, f'#include <bt_msgs/action/{name.lower()}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
        
        ports = ", ".join([f'InputPort<{f.split(":")[1].replace("32","")}>("{f.split(":")[0]}")' for f in fields])
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
        add_to_file_before_marker(cpp_path, class_content, "int main(int argc")
        add_to_file_before_marker(cpp_path, f'    params.default_port_value = "{name.lower()}";\n    factory.registerNodeType<{name}Action>("{name}", params);\n\n', "auto tree =")

if __name__ == "__main__":
    root = tk.Tk()
    app = ActionCreatorGUI(root)
    root.mainloop()
