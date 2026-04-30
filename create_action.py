#!/usr/bin/env python3
import os
import sys
import re
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QScrollArea, QFrame, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt

def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def add_to_file_after_marker(file_path, content, marker):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    if content.strip() in "".join(lines):
        return

    with open(file_path, 'w') as f:
        for line in lines:
            f.write(line)
            if marker in line:
                f.write(content)

def update_tree_path_in_cpp(file_path, new_xml_name):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as f:
        content = f.read()
    
    new_path = f'/ros2_ws/src/bt_example/tree/{new_xml_name}'
    updated_content = re.sub(r'createTreeFromFile\(".+?"\)', f'createTreeFromFile("{new_path}")', content)
    
    with open(file_path, 'w') as f:
        f.write(updated_content)

class ActionCreatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BT Action Scaffolder (Independent Nodes)")
        self.setMinimumSize(600, 900)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #333333; font-family: 'Noto Sans CJK JP', 'Meiryo', sans-serif; }
            QLabel { color: #333333; background-color: transparent; }
            QLineEdit { padding: 8px; border: 1px solid #cccccc; border-radius: 4px; background-color: #fcfcfc; color: #000000; }
            QComboBox { padding: 5px; border: 1px solid #cccccc; border-radius: 4px; background-color: #fcfcfc; color: #000000; }
            QPushButton#GenerateBtn { background-color: #28a745; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 10px; }
            QPushButton#AddBtn { background-color: #007bff; color: #ffffff; border-radius: 4px; padding: 5px; }
            QPushButton#NewTreeBtn { background-color: #6c757d; color: #ffffff; border-radius: 4px; padding: 10px; }
            QFrame#Header { background-color: #24292e; }
            QFrame#HelpBox { background-color: #fff9db; border: 1px solid #ffec99; border-radius: 8px; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(80)
        h_layout = QVBoxLayout(header)
        title = QLabel("BT Action Scaffolder")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        h_layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(header)

        content_frame = QFrame()
        c_layout = QVBoxLayout(content_frame)
        c_layout.setContentsMargins(30, 20, 30, 20)

        help_box = QFrame()
        help_box.setObjectName("HelpBox")
        help_layout = QVBoxLayout(help_box)
        help_title = QLabel("💡 独立ノード構成システム")
        help_title.setStyleSheet("font-weight: bold; color: #f08c00;")
        help_layout.addWidget(help_title)
        
        usage_text = (
            "・<b>Action生成</b>: アクションごとに独立したPythonノードファイルが生成されます。\n"
            "・<b>自動登録</b>: setup.pyとLaunchファイルが自動更新されます。\n"
            "・<b>実行</b>: ロジックサーバーを一括起動するには <code>run_logic</code> を実行してください。"
        )
        help_desc = QLabel(usage_text)
        help_desc.setWordWrap(True)
        help_desc.setStyleSheet("font-size: 11px; line-height: 1.4;")
        help_layout.addWidget(help_desc)
        c_layout.addWidget(help_box)
        c_layout.addSpacing(20)

        c_layout.addWidget(QLabel("<b>Tree XML Filename:</b>"))
        self.tree_name_input = QLineEdit()
        self.tree_name_input.setText("my_tree.xml")
        c_layout.addWidget(self.tree_name_input)

        self.new_tree_btn = QPushButton("✨ この名前で空のツリーを新規作成")
        self.new_tree_btn.setObjectName("NewTreeBtn")
        self.new_tree_btn.clicked.connect(self.create_empty_tree)
        c_layout.addWidget(self.new_tree_btn)
        
        c_layout.addSpacing(20)
        c_layout.addWidget(QLabel("<hr>"))
        c_layout.addSpacing(10)

        c_layout.addWidget(QLabel("<b>New Action Name (PascalCase):</b>"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: CleanRoom")
        c_layout.addWidget(self.name_input)

        c_layout.addSpacing(20)
        c_layout.addWidget(QLabel("<b>Arguments (Input Ports):</b>"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.fields_container)
        c_layout.addWidget(self.scroll)

        self.field_rows = []
        self.addFieldRow()

        add_btn = QPushButton("+ Add Port")
        add_btn.setObjectName("AddBtn")
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self.addFieldRow)
        c_layout.addWidget(add_btn)

        c_layout.addSpacing(20)
        
        self.palette_only_cb = QCheckBox("Groot2のパレット更新のみ行う (コード生成をスキップ)")
        self.palette_only_cb.setStyleSheet("font-weight: bold; color: #007bff;")
        c_layout.addWidget(self.palette_only_cb)

        c_layout.addSpacing(10)
        
        self.gen_btn = QPushButton("実行する")
        self.gen_btn.setObjectName("GenerateBtn")
        self.gen_btn.setFixedHeight(50)
        self.gen_btn.clicked.connect(self.generate)
        c_layout.addWidget(self.gen_btn)

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

    def create_empty_tree(self):
        tree_name = self.tree_name_input.text().strip()
        if not tree_name.endswith('.xml'): tree_name += '.xml'

        reply = QMessageBox.question(self, '確認', 
                                   f"'{tree_name}' を新規作成しますか？",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            tree_path = f"src/bt_example/tree/{tree_name}"
            os.makedirs(os.path.dirname(tree_path), exist_ok=True)
            empty_xml = f"""<root BTCPP_format="4">
    <BehaviorTree ID="MainTree">
        <Sequence>
            <AlwaysSuccess name="placeholder"/>
            <!-- {tree_name} の内容をここに作成してください -->
        </Sequence>
    </BehaviorTree>
</root>
"""
            with open(tree_path, 'w') as f:
                f.write(empty_xml)
            
            update_tree_path_in_cpp("src/bt_example/src/main.cpp", tree_name)
            QMessageBox.information(self, "成功", f"'{tree_name}' を作成しました。")

    def generate(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.critical(self, "エラー", "Action Name を入力してください")
            return

        fields = []
        for w, n, t in self.field_rows:
            f_name = n.text().strip()
            if f_name:
                fields.append(f"{f_name}:{t.currentText()}")

        try:
            if self.palette_only_cb.isChecked():
                self.update_palette_only(name, fields)
                QMessageBox.information(self, "成功", f"パレットに '{name}' を追加しました。")
            else:
                self.create_action_files(name, fields)
                QMessageBox.information(self, "成功", f"アクション '{name}' の生成が完了しました！")
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "エラー", str(e) + "\n" + traceback.format_exc())

    def update_palette_only(self, name, fields):
        palette_path = "src/bt_example/tree/nodes_library.xml"
        os.makedirs(os.path.dirname(palette_path), exist_ok=True)
        cpp_types = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        
        port_xml = ""
        for fld in fields:
            fname, ftype = fld.split(':')
            cpp_t = cpp_types[ftype]
            port_xml += f'            <input_port name="{fname}" type="{cpp_t}"/>\n'
            
        node_xml = f"""        <Action ID="{name}">
{port_xml}        </Action>
"""
        add_to_file_after_marker(palette_path, node_xml, "<TreeNodesModel>")

    def create_action_files(self, name, fields):
        snake_name = camel_to_snake(name)
        node_exec_name = f"{snake_name}_node"

        # 1. .action
        os.makedirs("src/bt_msgs/action", exist_ok=True)
        with open(f"src/bt_msgs/action/{name}.action", 'w') as f:
            f.write("# Request\n")
            for fld in fields:
                fname, ftype = fld.split(':')
                f.write(f"{ftype} {fname}\n")
            f.write("---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")

        # 2. CMake
        add_to_file_after_marker("src/bt_msgs/CMakeLists.txt", f'  "action/{name}.action"\n', 'rosidl_generate_interfaces(${PROJECT_NAME}')

        # 3. Python Independent Node
        py_path = f"src/bt_python_logic/bt_python_logic/{node_exec_name}.py"
        arg_gets = "\n        ".join([f"{fname} = goal_handle.request.{fname}" for f in fields for fname, ftype in [f.split(':')]])
        
        node_content = f"""import time
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from bt_msgs.action import {name}

class {name}Node(Node):
    def __init__(self):
        super().__init__('{node_exec_name}')
        self._action_server = ActionServer(
            self, {name}, '{snake_name}', self.execute_callback)
        self.get_logger().info('{name} Node initialized')

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing {name}...')
        {arg_gets}
        
        # TODO: 具体的なロジックをここに実装
        
        goal_handle.succeed()
        return {name}.Result(success=True)

def main(args=None):
    rclpy.init(args=args)
    node = {name}Node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
"""
        with open(py_path, 'w') as f:
            f.write(node_content)

        # 4. setup.py Entry Point
        setup_path = "src/bt_python_logic/setup.py"
        entry_line = f"            '{node_exec_name} = bt_python_logic.{node_exec_name}:main',\n"
        add_to_file_after_marker(setup_path, entry_line, "# --- [CONSOLE_SCRIPTS_MARKER] ---")

        # 5. Launch File
        launch_path = "src/bt_python_logic/launch/action_logic.launch.py"
        launch_node = f"""        Node(
            package='bt_python_logic',
            executable='{node_exec_name}',
            name='{node_exec_name}',
            output='screen'
        ),
"""
        add_to_file_after_marker(launch_path, launch_node, "# --- [ACTION_NODES_MARKER] ---")

        # 6. C++ Code
        cpp_path = "src/bt_example/src/main.cpp"
        add_to_file_after_marker(cpp_path, f'#include <bt_msgs/action/{snake_name}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
        
        cpp_types = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        ports = ", ".join([f'InputPort<{cpp_types[ftype]}>("{fname}")' for f in fields for fname, ftype in [f.split(':')]])
        goal_sets = "\n        ".join([f'getInput("{fname}", goal.{fname});' for f in fields for fname, ftype in [f.split(':')]])
        
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
        add_to_file_after_marker(cpp_path, class_content, "using namespace BT;")
        
        reg_content = f"""
    params.default_port_value = "{snake_name}";
    factory.registerNodeType<{name}Action>("{name}", params);
"""
        add_to_file_after_marker(cpp_path, reg_content, "// --- [ACTION_REGISTRATION_MARKER] ---")

        # 7. Palette Update
        self.update_palette_only(name, fields)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ActionCreatorGUI()
    ex.show()
    sys.exit(app.exec())
