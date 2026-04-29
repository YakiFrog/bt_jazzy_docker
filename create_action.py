#!/usr/bin/env python3
import os
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt

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

class ActionCreatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BT Action Scaffolder (PySide6)")
        self.setMinimumSize(600, 700)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #333333; font-family: 'Noto Sans CJK JP', 'Meiryo', sans-serif; }
            QLabel { color: #333333; background-color: transparent; }
            QLineEdit { padding: 8px; border: 1px solid #cccccc; border-radius: 4px; background-color: #fcfcfc; color: #000000; }
            QComboBox { padding: 5px; border: 1px solid #cccccc; border-radius: 4px; background-color: #fcfcfc; color: #000000; }
            QPushButton#GenerateBtn { background-color: #28a745; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 10px; }
            QPushButton#AddBtn { background-color: #007bff; color: #ffffff; border-radius: 4px; padding: 5px; }
            QFrame#Header { background-color: #24292e; }
            QScrollArea { border: 1px solid #dddddd; background-color: #ffffff; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # ヘッダー
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(120)
        h_layout = QVBoxLayout(header)
        title = QLabel("BT Action Scaffolder")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        h_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        info = QLabel("【自動化】 .action作成 / CMake / Pythonサーバー / C++ノード実装・登録")
        info.setStyleSheet("color: #959da5; font-size: 12px;")
        h_layout.addWidget(info, alignment=Qt.AlignCenter)
        layout.addWidget(header)

        # メインコンテンツ
        content_frame = QFrame()
        c_layout = QVBoxLayout(content_frame)
        c_layout.setContentsMargins(30, 20, 30, 20)

        # アクション名
        c_layout.addWidget(QLabel("<b>Action Name (クラス名になります):</b>"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: MoveRobot, PickupItem...")
        c_layout.addWidget(self.name_input)

        # フィールドセクション
        c_layout.addSpacing(20)
        c_layout.addWidget(QLabel("<b>Arguments (入力ポート):</b>"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: white; border: 1px solid #ddd; border-radius: 4px;")
        
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.fields_container)
        c_layout.addWidget(self.scroll)

        self.field_rows = []
        self.addFieldRow()

        add_btn = QPushButton("+ Add Port")
        add_btn.setObjectName("AddBtn")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self.addFieldRow)
        c_layout.addWidget(add_btn)

        c_layout.addSpacing(30)
        
        # 生成ボタン
        self.gen_btn = QPushButton("GENERATE ACTION")
        self.gen_btn.setObjectName("GenerateBtn")
        self.gen_btn.setFixedHeight(50)
        self.gen_btn.clicked.connect(self.generate)
        c_layout.addWidget(self.gen_btn)

        footer = QLabel("※ 生成後は 'build' を実行し、Python側のcallbackを実装してください")
        footer.setStyleSheet("color: #6a737d; font-style: italic; font-size: 11px;")
        c_layout.addWidget(footer, alignment=Qt.AlignCenter)

        layout.addWidget(content_frame)
        self.setLayout(layout)

    def addFieldRow(self):
        row = QWidget()
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(0, 0, 0, 0)

        name_in = QLineEdit()
        name_in.setPlaceholderText("port_name")
        type_in = QComboBox()
        type_in.addItems(["float32", "int32", "string", "bool"])
        
        del_btn = QPushButton("×")
        del_btn.setFixedWidth(30)
        del_btn.setStyleSheet("color: red; font-weight: bold; border: none;")
        del_btn.clicked.connect(lambda: self.removeFieldRow(row))

        r_layout.addWidget(name_in)
        r_layout.addWidget(type_in)
        r_layout.addWidget(del_btn)
        
        self.fields_layout.addWidget(row)
        self.field_rows.append((row, name_in, type_in))

    def removeFieldRow(self, row_widget):
        for i, (w, n, t) in enumerate(self.field_rows):
            if w == row_widget:
                self.field_rows.pop(i)
                row_widget.deleteLater()
                break

    def generate(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.critical(self, "Error", "Action Name を入力してください")
            return

        fields = []
        for w, n, t in self.field_rows:
            f_name = n.text().strip()
            if f_name:
                fields.append(f"{f_name}:{t.currentText()}")

        try:
            self.create_action_files(name, fields)
            QMessageBox.information(self, "Success", f"アクション '{name}' の生成が完了しました！\n\n1. コンテナ内で 'build' を実行\n2. Python側のロジックを実装\n3. XMLで使用")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def create_action_files(self, name, fields):
        # 通信定義、CMake、Python、C++ の更新ロジック
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
        # TODO: 具体的なロジックをここに実装
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
    app = QApplication(sys.argv)
    ex = ActionCreatorGUI()
    ex.show()
    sys.exit(app.exec())
