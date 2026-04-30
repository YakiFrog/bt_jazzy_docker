#!/usr/bin/env python3
import os
import sys
import re
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QScrollArea, QFrame, QMessageBox, QCheckBox, QTabWidget, QListWidget)
from PySide6.QtCore import Qt

def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def add_to_file_after_marker(file_path, content, marker):
    if not os.path.exists(file_path): return
    with open(file_path, 'r') as f: lines = f.readlines()
    if content.strip() in "".join(lines): return
    with open(file_path, 'w') as f:
        for line in lines:
            f.write(line)
            if marker in line: f.write(content)

def remove_from_file_by_pattern(file_path, pattern):
    if not os.path.exists(file_path): return
    with open(file_path, 'r') as f: lines = f.readlines()
    with open(file_path, 'w') as f:
        for line in lines:
            if re.search(pattern, line): continue
            f.write(line)

def update_tree_path_in_cpp(file_path, new_xml_name):
    if not os.path.exists(file_path): return
    with open(file_path, 'r') as f: content = f.read()
    new_path = f'/ros2_ws/src/bt_core/tree/{new_xml_name}'
    updated_content = re.sub(r'createTreeFromFile\(".+?"\)', f'createTreeFromFile("{new_path}")', content)
    with open(file_path, 'w') as f: f.write(updated_content)

class ActionManagerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BT Action Manager")
        self.setMinimumSize(650, 950)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #333333; font-family: 'Noto Sans CJK JP', sans-serif; }
            QTabWidget::pane { border: 1px solid #cccccc; }
            QPushButton#GenerateBtn { background-color: #28a745; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
            QPushButton#RemoveBtn { background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cccccc; border-radius: 4px; }
            QFrame#HelpBox { background-color: #fff9db; border: 1px solid #ffec99; border-radius: 8px; }
            QListWidget { border: 1px solid #cccccc; border-radius: 4px; }
        """)

        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tab_widget(), "作成 (Create)")
        self.tabs.addTab(self.manage_tab_widget(), "管理・削除 (Manage)")
        main_layout.addWidget(self.tabs)

    def create_tab_widget(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        help_box = QFrame(); help_box.setObjectName("HelpBox")
        h_layout = QVBoxLayout(help_box)
        h_layout.addWidget(QLabel("<b>💡 アクション作成</b><br>PascalCaseで名前を入力し、必要なポートを追加してください。"))
        layout.addWidget(help_box)
        layout.addSpacing(15)

        layout.addWidget(QLabel("<b>Tree XML Filename:</b>"))
        self.tree_name_input = QLineEdit("my_tree.xml")
        layout.addWidget(self.tree_name_input)
        
        btn_new_tree = QPushButton("空のツリーを新規作成・設定")
        btn_new_tree.clicked.connect(self.create_empty_tree)
        layout.addWidget(btn_new_tree)
        layout.addSpacing(10); layout.addWidget(QLabel("<hr>"))

        layout.addWidget(QLabel("<b>New Action Name:</b>"))
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("例: CleanRoom")
        layout.addWidget(self.name_input)

        layout.addSpacing(15); layout.addWidget(QLabel("<b>Arguments (Input Ports):</b>"))
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.fields_container = QWidget(); self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setAlignment(Qt.AlignTop); self.scroll.setWidget(self.fields_container)
        layout.addWidget(self.scroll)

        self.field_rows = []
        self.addFieldRow()
        
        add_btn = QPushButton("+ Port を追加")
        add_btn.clicked.connect(self.addFieldRow)
        layout.addWidget(add_btn)

        layout.addSpacing(15)
        self.palette_only_cb = QCheckBox("Palette更新のみ（コード生成スキップ）")
        layout.addWidget(self.palette_only_cb)

        self.gen_btn = QPushButton("アクションを生成・登録する")
        self.gen_btn.setObjectName("GenerateBtn")
        self.gen_btn.clicked.connect(self.generate)
        layout.addWidget(self.gen_btn)

        return tab

    def manage_tab_widget(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("<b>📦 登録済みアクション一覧</b>"))
        self.action_list = QListWidget()
        layout.addWidget(self.action_list)
        
        refresh_btn = QPushButton("リストを更新")
        refresh_btn.clicked.connect(self.refresh_action_list)
        layout.addWidget(refresh_btn)

        layout.addSpacing(20)
        remove_btn = QPushButton("選択したアクションを完全に削除")
        remove_btn.setObjectName("RemoveBtn")
        remove_btn.clicked.connect(self.remove_action)
        layout.addWidget(remove_btn)
        
        self.refresh_action_list()
        return tab

    def addFieldRow(self):
        row = QWidget(); r_layout = QHBoxLayout(row)
        name_in = QLineEdit(); name_in.setPlaceholderText("port_name")
        type_in = QComboBox(); type_in.addItems(["float32", "int32", "string", "bool"])
        del_btn = QPushButton("×"); del_btn.setFixedWidth(30); del_btn.clicked.connect(lambda: self.removeFieldRow(row))
        r_layout.addWidget(name_in); r_layout.addWidget(type_in); r_layout.addWidget(del_btn)
        self.fields_layout.addWidget(row); self.field_rows.append((row, name_in, type_in))

    def removeFieldRow(self, row):
        for i, (w, n, t) in enumerate(self.field_rows):
            if w == row: self.field_rows.pop(i); row.deleteLater(); break

    def refresh_action_list(self):
        self.action_list.clear()
        action_dir = "src/bt_msgs/action"
        if os.path.exists(action_dir):
            for f in os.listdir(action_dir):
                if f.endswith(".action"): self.action_list.addItem(f.replace(".action", ""))

    def generate(self):
        name = self.name_input.text().strip()
        if not name: return QMessageBox.critical(self, "Error", "Name is required")
        fields = [f"{n.text().strip()}:{t.currentText()}" for w, n, t in self.field_rows if n.text().strip()]
        try:
            if self.palette_only_cb.isChecked(): self.update_palette_only(name, fields)
            else: self.create_action_files(name, fields)
            QMessageBox.information(self, "Success", f"Action '{name}' generated.")
            self.refresh_action_list()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def create_empty_tree(self):
        name = self.tree_name_input.text().strip()
        if not name.endswith(".xml"): name += ".xml"
        if QMessageBox.question(self, "Confirm", f"Overwrite {name}?") == QMessageBox.Yes:
            tree_path = f"src/bt_core/tree/{name}"
            os.makedirs(os.path.dirname(tree_path), exist_ok=True)
            with open(tree_path, 'w') as f:
                f.write(f'<root BTCPP_format="4">\n  <BehaviorTree ID="MainTree">\n    <Sequence>\n      <AlwaysSuccess name="placeholder"/>\n    </Sequence>\n  </BehaviorTree>\n</root>')
            update_tree_path_in_cpp("src/bt_core/src/main.cpp", name)
            QMessageBox.information(self, "Success", "Empty tree created.")

    def update_palette_only(self, name, fields):
        path = "src/bt_core/tree/nodes_library.xml"
        cpp_t = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        ports = "".join([f'            <input_port name="{f.split(":")[0]}" type="{cpp_t[f.split(":")[1]]}"/>\n' for f in fields])
        node_xml = f'        <Action ID="{name}">\n{ports}        </Action>\n'
        add_to_file_after_marker(path, node_xml, "<TreeNodesModel>")

    def create_action_files(self, name, fields):
        snake = camel_to_snake(name); node_name = f"{snake}_node"
        # 1. Action file
        os.makedirs("src/bt_msgs/action", exist_ok=True)
        with open(f"src/bt_msgs/action/{name}.action", 'w') as f:
            f.write("# Request\n" + "".join([f"{f.split(':')[1]} {f.split(':')[0]}\n" for f in fields]) + "---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")
        # 2. CMake
        add_to_file_after_marker("src/bt_msgs/CMakeLists.txt", f'  "action/{name}.action"\n', "rosidl_generate_interfaces(${PROJECT_NAME}")
        # 3. Python Node
        os.makedirs("src/bt_python_logic/bt_python_logic", exist_ok=True)
        args = "\n        ".join([f"{f.split(':')[0]} = goal_handle.request.{f.split(':')[0]}" for f in fields])
        with open(f"src/bt_python_logic/bt_python_logic/{node_name}.py", 'w') as f:
            f.write(f"import time\nimport rclpy\nfrom rclpy.action import ActionServer\nfrom rclpy.node import Node\nfrom bt_msgs.action import {name}\n\nclass {name}Node(Node):\n    def __init__(self):\n        super().__init__('{node_name}')\n        self._action_server = ActionServer(self, {name}, '{snake}', self.execute_callback)\n        self.get_logger().info('{name} Node initialized')\n\n    def execute_callback(self, goal_handle):\n        self.get_logger().info('Executing {name}...')\n        {args}\n        goal_handle.succeed()\n        return {name}.Result(success=True)\n\ndef main(args=None):\n    rclpy.init(args=args); node = {name}Node(); rclpy.spin(node); rclpy.shutdown()\n\nif __name__ == '__main__': main()")
        # 4. setup.py
        add_to_file_after_marker("src/bt_python_logic/setup.py", f"            '{node_name} = bt_python_logic.{node_name}:main',\n", "[CONSOLE_SCRIPTS_MARKER]")
        # 5. Launch
        add_to_file_after_marker("src/bt_python_logic/launch/action_logic.launch.py", f"        Node(package='bt_python_logic', executable='{node_name}', name='{node_name}', output='screen'),\n", "[ACTION_NODES_MARKER]")
        # 6. C++
        add_to_file_after_marker("src/bt_core/src/main.cpp", f'#include <bt_msgs/action/{snake}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
        cpp_t = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        ports = ", ".join([f'InputPort<{cpp_t[f.split(":")[1]]}>("{f.split(":")[0]}")' for f in fields])
        sets = "\n        ".join([f'getInput("{f.split(":")[0]}", goal.{f.split(":")[0]});' for f in fields])
        class_code = f"class {name}Action : public RosActionNode<bt_msgs::action::{name}>\n{{\npublic:\n    {name}Action(const std::string& name, const NodeConfig& conf, const RosNodeParams& params) : RosActionNode<bt_msgs::action::{name}>(name, conf, params) {{}}\n    static PortsList providedPorts() {{ return providedBasicPorts({{ {ports} }}); }}\n    bool setGoal(Goal& goal) override {{ {sets}\n        return true; }}\n    NodeStatus onResultReceived(const WrappedResult& wr) override {{ return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE; }}\n}};\n\n"
        add_to_file_after_marker("src/bt_core/src/main.cpp", class_code, "using namespace BT;")
        add_to_file_after_marker("src/bt_core/src/main.cpp", f'    params.default_port_value = "{snake}";\n    factory.registerNodeType<{name}Action>("{name}", params);\n', "[ACTION_REGISTRATION_MARKER]")
        # 7. Palette
        self.update_palette_only(name, fields)

    def remove_action(self):
        item = self.action_list.currentItem()
        if not item: return QMessageBox.warning(self, "Warning", "Select an action first")
        name = item.text(); snake = camel_to_snake(name)
        if QMessageBox.question(self, "Confirm", f"Delete {name} completely?") != QMessageBox.Yes: return
        
        try:
            # Delete files
            paths = [f"src/bt_msgs/action/{name}.action", f"src/bt_python_logic/bt_python_logic/{snake}_node.py"]
            for p in paths:
                if os.path.exists(p): os.remove(p)
            
            # Remove from config files
            remove_from_file_by_pattern("src/bt_msgs/CMakeLists.txt", f'"{name}.action"')
            remove_from_file_by_pattern("src/bt_python_logic/setup.py", f"'{snake}_node")
            remove_from_file_by_pattern("src/bt_python_logic/launch/action_logic.launch.py", f"executable='{snake}_node'")
            
            # C++ cleanup (Removes class, include, and registration)
            cpp_path = "src/bt_core/src/main.cpp"
            if os.path.exists(cpp_path):
                with open(cpp_path, 'r') as f: content = f.read()
                content = re.sub(f'#include <bt_msgs/action/{snake}.hpp>\n', '', content)
                content = re.sub(rf'class {name}Action : public RosActionNode<bt_msgs::action::{name}>.*?\n}};\n\n', '', content, flags=re.DOTALL)
                content = re.sub(rf'params\.default_port_value = "{snake}";\n    factory\.registerNodeType<{name}Action>\("{name}", params\);\n', '', content)
                with open(cpp_path, 'w') as f: f.write(content)
            
            # Palette cleanup
            pal_path = "src/bt_core/tree/nodes_library.xml"
            if os.path.exists(pal_path):
                with open(pal_path, 'r') as f: content = f.read()
                content = re.sub(rf'        <Action ID="{name}">.*?\n        </Action>\n', '', content, flags=re.DOTALL)
                with open(pal_path, 'w') as f: f.write(content)

            QMessageBox.information(self, "Success", f"Action '{name}' removed.")
            self.refresh_action_list()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ActionManagerGUI()
    ex.show()
    sys.exit(app.exec())
