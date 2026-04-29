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
    
    # 既存の .createTreeFromFile("...") の中身を置換
    new_path = f'/ros2_ws/src/bt_example/tree/{new_xml_name}'
    updated_content = re.sub(r'createTreeFromFile\(".+?"\)', f'createTreeFromFile("{new_path}")', content)
    
    with open(file_path, 'w') as f:
        f.write(updated_content)

def add_to_import_line(file_path, new_item, marker):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    with open(file_path, 'w') as f:
        for line in lines:
            if marker in line and new_item not in line:
                f.write(line.strip() + f", {new_item}\n")
            else:
                f.write(line)

class ActionCreatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BT Action Scaffolder (PySide6)")
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
        help_title = QLabel("💡 使い方とルール")
        help_title.setStyleSheet("font-weight: bold; color: #f08c00;")
        help_layout.addWidget(help_title)
        
        usage_text = (
            "・<b>Action生成</b>: 下のフォームからアクションを追加します。\n"
            "・<b>ツリー管理</b>: ファイル名を指定して新規作成できます。作成するとプログラムの読み込み先も自動で切り替わります。"
        )
        help_desc = QLabel(usage_text)
        help_desc.setWordWrap(True)
        help_desc.setStyleSheet("font-size: 11px; line-height: 1.4;")
        help_layout.addWidget(help_desc)
        c_layout.addWidget(help_box)
        c_layout.addSpacing(20)

        # ツリーファイル名入力
        c_layout.addWidget(QLabel("<b>Tree XML Filename:</b>"))
        self.tree_name_input = QLineEdit()
        self.tree_name_input.setText("my_tree.xml")
        c_layout.addWidget(self.tree_name_input)

        self.new_tree_btn = QPushButton("✨ この名前で空のツリーを新規作成・設定")
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
                                   f"'{tree_name}' を新規作成し、プログラムの読み込み先として設定しますか？",
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
            
            # main.cpp のパスを更新
            update_tree_path_in_cpp("src/bt_example/src/main.cpp", tree_name)
            
            QMessageBox.information(self, "成功", f"'{tree_name}' を作成しました。\nmain.cpp の読み込み先も更新しました。")

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
                QMessageBox.information(self, "成功", f"アクション '{name}' の全生成が完了しました！")
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

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

        # 3. Python
        py_path = "src/bt_python_logic/bt_python_logic/action_server.py"
        add_to_import_line(py_path, name, "from bt_msgs.action import")
        add_to_file_after_marker(py_path, f"        self._{snake_name}_server = ActionServer(self, {name}, '{snake_name}', self.{snake_name}_callback)\n", "def __init__(self):")
        
        cb_content = f"""    def {snake_name}_callback(self, goal_handle):
        self.get_logger().info('{name} started')
        # TODO: 具体的なロジックをここに実装
        goal_handle.succeed()
        return {name}.Result(success=True)

"""
        add_to_file_after_marker(py_path, cb_content, "class MultiActionServer(Node):")

        # 4. C++
        cpp_path = "src/bt_example/src/main.cpp"
        add_to_file_after_marker(cpp_path, f'#include <bt_msgs/action/{snake_name}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
        
        cpp_types = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        ports = ", ".join([f'InputPort<{cpp_types[f.split(":")[1]]}>("{f.split(":")[0]}")' for f in fields])
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
        add_to_file_after_marker(cpp_path, class_content, "using namespace BT;")
        add_to_file_after_marker(cpp_path, f'    params.default_port_value = "{snake_name}";\n    factory.registerNodeType<{name}Action>("{name}", params);\n\n', "BehaviorTreeFactory factory;")

        # 5. Palette Update
        self.update_palette_only(name, fields)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ActionCreatorGUI()
    ex.show()
    sys.exit(app.exec())
