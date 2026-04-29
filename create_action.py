#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import messagebox, ttk

def add_to_file_before_marker(file_path, content, marker):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
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
        self.root.title("BT Action Scaffolder v2")
        self.root.geometry("600x700")
        self.root.configure(bg="#f5f5f5")

        # タイトルと説明
        header = tk.Frame(root, bg="#2c3e50", height=100)
        header.pack(fill=tk.X)
        tk.Label(header, text="Behavior Tree Action Scaffolder", bg="#2c3e50", fg="white", font=('Arial', 16, 'bold')).pack(pady=10)
        
        info_text = "【自動化の範囲】\n1. .action作成  2. CMake登録  3. Pythonサーバー雛形  4. C++ノード実装・登録"
        tk.Label(header, text=info_text, bg="#2c3e50", fg="#bdc3c7", font=('Arial', 9)).pack(pady=5)

        main_frame = tk.Frame(root, bg="#f5f5f5", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # アクション名
        tk.Label(main_frame, text="Action Name:", bg="#f5f5f5", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.name_entry = tk.Entry(main_frame, font=('Arial', 12), width=40)
        self.name_entry.pack(pady=10)
        self.name_entry.insert(0, "MyNewTask")

        # フィールド一覧
        tk.Label(main_frame, text="Arguments (Ports):", bg="#f5f5f5", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
        
        # スクロール可能なフィールドエリア
        self.canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f5f5f5")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.field_rows = []
        self.add_field_row()

        btn_frame = tk.Frame(root, bg="#f5f5f5", pady=20)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="+ Add Port", command=self.add_field_row, bg="#3498db", fg="white", font=('Arial', 10)).pack(side=tk.LEFT, padx=50)
        tk.Button(btn_frame, text="GENERATE", command=self.generate, bg="#27ae60", fg="white", font=('Arial', 12, 'bold'), width=15).pack(side=tk.RIGHT, padx=50)

        # 下部の注意書き
        footer = tk.Label(root, text="※ 生成後は 'build' を実行し、Python側のcallbackを実装してください", bg="#f5f5f5", fg="#7f8c8d", font=('Arial', 8, 'italic'))
        footer.pack(side=tk.BOTTOM, pady=10)

    def add_field_row(self):
        row = tk.Frame(self.scrollable_frame, bg="#f5f5f5")
        row.pack(pady=5, fill=tk.X)
        
        tk.Label(row, text="Name:", bg="#f5f5f5").pack(side=tk.LEFT)
        name_ent = tk.Entry(row, width=15)
        name_ent.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row, text="Type:", bg="#f5f5f5").pack(side=tk.LEFT, padx=(10,0))
        type_var = tk.StringVar(value="float32")
        type_opt = ttk.Combobox(row, textvariable=type_var, values=["float32", "int32", "string", "bool"], width=10)
        type_opt.pack(side=tk.LEFT, padx=5)
        
        self.field_rows.append((name_ent, type_opt))

    def generate(self):
        name = self.name_entry.get().strip()
        if not name or name == "MyNewTask":
            messagebox.showerror("Error", "有効なアクション名を入力してください")
            return

        fields = []
        for n_ent, t_opt in self.field_rows:
            f_name = n_ent.get().strip()
            if f_name:
                fields.append(f"{f_name}:{t_opt.get()}")

        try:
            self.create_action_files(name, fields)
            messagebox.showinfo("Success", f"アクション '{name}' の全ファイルを更新しました！\n\n1. コンテナ内で 'build' を実行\n2. Python側のコールバックを実装\n3. XMLで使用")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_action_files(self, name, fields):
        # ロジックは同じ（省略せず実装を維持）
        os.makedirs("src/bt_msgs/action", exist_ok=True)
        with open(f"src/bt_msgs/action/{name}.action", 'w') as f:
            f.write("# Request\n")
            for fld in fields:
                f.write(f"{fld.replace(':', ' ')}\n")
            f.write("---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")

        add_to_file_before_marker("src/bt_msgs/CMakeLists.txt", f'  "action/{name}.action"\n', '  DEPENDENCIES action_msgs')

        py_path = "src/bt_python_logic/bt_python_logic/action_server.py"
        add_to_file_before_marker(py_path, f", {name}", "from bt_msgs.action import")
        add_to_file_before_marker(py_path, f"        self._{name.lower()}_server = ActionServer(self, {name}, '{name.lower()}', self.{name.lower()}_callback)\n", "self.get_logger().info('Python ロジックサーバー")
        cb_content = f"""    def {name.lower()}_callback(self, goal_handle):
        self.get_logger().info('{name} 実行開始')
        # TODO: 具体的な処理を書く
        goal_handle.succeed()
        return {name}.Result(success=True)

"""
        add_to_file_before_marker(py_path, cb_content, "def main(args=None):")

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
