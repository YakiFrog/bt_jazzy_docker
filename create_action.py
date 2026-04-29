#!/usr/bin/env python3
import os
import sys
import re
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QScrollArea, QFrame, QMessageBox)
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

        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(120)
        h_layout = QVBoxLayout(header)
        title = QLabel("BT Action Scaffolder")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        h_layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(header)

        content_frame = QFrame()
        c_layout = QVBoxLayout(content_frame)
        c_layout.setContentsMargins(30, 20, 30, 20)

        c_layout.addWidget(QLabel("<b>Action Name (Class Name):</b>"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. CleanRoom")
        c_layout.addWidget(self.name_input)

        c_layout.addSpacing(20)
        c_layout.addWidget(QLabel("<b>Arguments (Ports):</b>"))
        
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
        add_btn.clicked.connect(self.addFieldRow)
        c_layout.addWidget(add_btn)

        c_layout.addSpacing(30)
        self.gen_btn = QPushButton("GENERATE ACTION")
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
        type_in = QComboBox()
        type_in.addItems(["float32", "int32", "string", "bool"])
        del_btn = QPushButton("×")
        del_btn.setFixedWidth(30)
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
        if not name: return

        fields = []
        for w, n, t in self.field_rows:
            f_name = n.text().strip()
            if f_name: fields.append(f"{f_name}:{t.currentText()}")

        try:
            self.create_action_files(name, fields)
            QMessageBox.information(self, "Success", f"Action '{name}' created!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def create_action_files(self, name, fields):
        # snake_case name for files and internal ROS names
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ActionCreatorGUI()
    ex.show()
    sys.exit(app.exec())
