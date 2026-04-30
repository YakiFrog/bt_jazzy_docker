#!/usr/bin/env python3
import os
import sys
import re
import threading
import importlib
import time
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QScrollArea, QFrame, QMessageBox, QCheckBox, QTabWidget, QListWidget, QRadioButton, QButtonGroup, QTextEdit)
from PySide6.QtCore import Qt, QTimer, Signal, QObject

# ROS 2 imports (GUI process needs to be a ROS node for testing)
try:
    import rclpy
    from rclpy.action import ActionClient
except ImportError:
    pass

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

class RosWorker(QObject):
    log_signal = Signal(str)
    result_signal = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.node = None
        if 'rclpy' in sys.modules:
            if not rclpy.ok(): rclpy.init()
            self.node = rclpy.create_node('bt_node_manager_tester')
            self.thread = threading.Thread(target=self.spin, daemon=True)
            self.thread.start()

    def spin(self):
        rclpy.spin(self.node)

    def send_action_goal(self, action_name, params):
        try:
            module = importlib.import_module(f"bt_msgs.action")
            action_cls = getattr(module, action_name)
            client = ActionClient(self.node, action_cls, camel_to_snake(action_name))
            
            if not client.wait_for_server(timeout_sec=2.0):
                self.log_signal.emit(f"Error: Action server for '{action_name}' not found.")
                return

            goal_msg = action_cls.Goal()
            for k, v in params.items():
                # Simple type conversion
                attr_type = type(getattr(goal_msg, k))
                setattr(goal_msg, k, attr_type(v))

            self.log_signal.emit(f"Sending goal to {action_name}...")
            send_goal_future = client.send_goal_async(goal_msg, feedback_callback=self.action_feedback_cb)
            send_goal_future.add_done_callback(self.action_goal_response_cb)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")

    def action_feedback_cb(self, feedback_msg):
        self.log_signal.emit(f"Feedback: {feedback_msg.feedback.progress}%")

    def action_goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.log_signal.emit("Goal rejected")
            return
        self.log_signal.emit("Goal accepted")
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.action_result_cb)

    def action_result_cb(self, future):
        result = future.result().result
        status = future.result().status
        self.log_signal.emit(f"Result received. Success: {result.success}")
        self.result_signal.emit(result.success, f"Action Finished: {result.success}")

    def call_service(self, srv_name, params):
        try:
            module = importlib.import_module(f"bt_msgs.srv")
            srv_cls = getattr(module, srv_name)
            client = self.node.create_client(srv_cls, camel_to_snake(srv_name))
            
            if not client.wait_for_service(timeout_sec=2.0):
                self.log_signal.emit(f"Error: Service server for '{srv_name}' not found.")
                return

            req = srv_cls.Request()
            for k, v in params.items():
                attr_type = type(getattr(req, k))
                setattr(req, k, attr_type(v))

            self.log_signal.emit(f"Calling service {srv_name}...")
            future = client.call_async(req)
            future.add_done_callback(lambda f: self.srv_result_cb(f, srv_name))
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")

    def srv_result_cb(self, future, name):
        try:
            res = future.result()
            self.log_signal.emit(f"Service Response: {res.result}")
            self.result_signal.emit(res.result, f"Condition Result: {res.result}")
        except Exception as e:
            self.log_signal.emit(f"Srv Error: {str(e)}")

class ActionManagerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.ros = RosWorker()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BT Node Manager & Tester")
        self.setMinimumSize(750, 950)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; color: #333333; font-family: 'Noto Sans CJK JP', sans-serif; }
            QTabWidget::pane { border: 1px solid #cccccc; }
            QPushButton#GenerateBtn { background-color: #28a745; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
            QPushButton#RemoveBtn { background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
            QPushButton#TestBtn { background-color: #007bff; color: white; font-weight: bold; border-radius: 4px; padding: 12px; }
            QLineEdit, QComboBox, QTextEdit { padding: 8px; border: 1px solid #cccccc; border-radius: 4px; }
            QFrame#HelpBox { background-color: #fff9db; border: 1px solid #ffec99; border-radius: 8px; }
            QListWidget { border: 1px solid #cccccc; border-radius: 4px; }
            QRadioButton { spacing: 8px; font-weight: bold; }
        """)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tab_widget(), "作成 (Create)")
        self.tabs.addTab(self.manage_tab_widget(), "管理 (Manage)")
        self.tabs.addTab(self.test_tab_widget(), "テスト (Test)")
        main_layout.addWidget(self.tabs)

        self.ros.log_signal.connect(self.update_test_log)

    def create_tab_widget(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setContentsMargins(20, 20, 20, 20)
        help_box = QFrame(); help_box.setObjectName("HelpBox"); h_layout = QVBoxLayout(help_box)
        h_layout.addWidget(QLabel("<b>💡 ノード作成</b><br>ActionかConditionを選んで作成してください。"))
        layout.addWidget(help_box); layout.addSpacing(15)
        layout.addWidget(QLabel("<b>種類 (Node Type):</b>"))
        type_layout = QHBoxLayout(); self.type_group = QButtonGroup(self)
        self.radio_action = QRadioButton("Action (動作)"); self.radio_condition = QRadioButton("Condition (判定)")
        self.radio_action.setChecked(True); self.type_group.addButton(self.radio_action); self.type_group.addButton(self.radio_condition)
        type_layout.addWidget(self.radio_action); type_layout.addWidget(self.radio_condition); layout.addLayout(type_layout)
        layout.addSpacing(10); layout.addWidget(QLabel("<b>Tree XML Filename:</b>"))
        self.tree_name_input = QLineEdit("my_tree.xml"); layout.addWidget(self.tree_name_input)
        btn_new_tree = QPushButton("空のツリーを新規作成"); btn_new_tree.clicked.connect(self.create_empty_tree); layout.addWidget(btn_new_tree)
        layout.addSpacing(10); layout.addWidget(QLabel("<hr>"))
        layout.addWidget(QLabel("<b>New Node Name:</b>")); self.name_input = QLineEdit(); self.name_input.setPlaceholderText("例: CleanRoom")
        layout.addWidget(self.name_input); layout.addSpacing(15); layout.addWidget(QLabel("<b>Arguments (Input Ports):</b>"))
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.fields_container = QWidget(); self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setAlignment(Qt.AlignTop); self.scroll.setWidget(self.fields_container); layout.addWidget(self.scroll)
        self.field_rows = []; self.addFieldRow()
        add_btn = QPushButton("+ Port を追加"); add_btn.clicked.connect(self.addFieldRow); layout.addWidget(add_btn)
        layout.addSpacing(15); self.palette_only_cb = QCheckBox("Palette更新のみ（コード生成スキップ）"); layout.addWidget(self.palette_only_cb)
        self.gen_btn = QPushButton("ノードを生成・登録する"); self.gen_btn.setObjectName("GenerateBtn"); self.gen_btn.clicked.connect(self.generate); layout.addWidget(self.gen_btn)
        return tab

    def manage_tab_widget(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<b>📦 登録済みノード一覧</b>")); self.node_list = QListWidget(); layout.addWidget(self.node_list)
        refresh_btn = QPushButton("リストを更新"); refresh_btn.clicked.connect(self.refresh_node_list); layout.addWidget(refresh_btn)
        layout.addSpacing(20); remove_btn = QPushButton("選択したノードを完全に削除"); remove_btn.setObjectName("RemoveBtn"); remove_btn.clicked.connect(self.remove_node); layout.addWidget(remove_btn)
        self.refresh_node_list()
        return tab

    def test_tab_widget(self):
        tab = QWidget(); layout = QVBoxLayout(tab); layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<b>🎯 ノード単体テスト</b>"))
        self.test_selector = QComboBox(); self.test_selector.currentIndexChanged.connect(self.on_test_node_selected)
        layout.addWidget(self.test_selector)
        
        layout.addSpacing(15); layout.addWidget(QLabel("<b>Test Parameters:</b>"))
        self.test_params_container = QWidget(); self.test_params_layout = QVBoxLayout(self.test_params_container)
        layout.addWidget(self.test_params_container)
        
        self.test_btn = QPushButton("実行 (Run Test)"); self.test_btn.setObjectName("TestBtn")
        self.test_btn.clicked.connect(self.run_test); layout.addWidget(self.test_btn)
        
        layout.addSpacing(15); layout.addWidget(QLabel("<b>Execution Log:</b>"))
        self.test_log = QTextEdit(); self.test_log.setReadOnly(True); self.test_log.setStyleSheet("background-color: #f8f9fa; color: #1e2125;")
        layout.addWidget(self.test_log)
        
        self.refresh_test_selector()
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

    def refresh_node_list(self):
        self.node_list.clear()
        for f in os.listdir("src/bt_msgs/action") if os.path.exists("src/bt_msgs/action") else []:
            if f.endswith(".action"): self.node_list.addItem(f"Action: {f.replace('.action', '')}")
        for f in os.listdir("src/bt_msgs/srv") if os.path.exists("src/bt_msgs/srv") else []:
            if f.endswith(".srv") and f != "ConditionCheck.srv": self.node_list.addItem(f"Condition: {f.replace('.srv', '')}")
        self.refresh_test_selector()

    def refresh_test_selector(self):
        if not hasattr(self, 'test_selector'): return
        self.test_selector.clear()
        self.test_selector.addItem("-- テストするノードを選択 --")
        for i in range(self.node_list.count()): self.test_selector.addItem(self.node_list.item(i).text())

    def on_test_node_selected(self):
        while self.test_params_layout.count():
            child = self.test_params_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        text = self.test_selector.currentText()
        if "--" in text or not text: return
        node_type, name = text.split(": ")
        
        # Parse definition file to get parameters
        ext = ".srv" if node_type == "Condition" else ".action"
        path = f"src/bt_msgs/{'srv' if node_type == 'Condition' else 'action'}/{name}{ext}"
        if not os.path.exists(path): return
        
        with open(path, 'r') as f: content = f.read()
        req_part = content.split("---")[0]
        self.test_inputs = {}
        for line in req_part.splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2:
                    t, n = parts[0], parts[1]
                    row = QHBoxLayout(); row.addWidget(QLabel(f"{n} ({t}):"))
                    in_field = QLineEdit(); in_field.setPlaceholderText(f"{t} value")
                    row.addWidget(in_field); self.test_params_layout.addLayout(row)
                    self.test_inputs[n] = in_field

    def run_test(self):
        text = self.test_selector.currentText()
        if "--" in text: return
        node_type, name = text.split(": ")
        params = {k: v.text() for k, v in self.test_inputs.items()}
        self.test_log.append(f"--- Starting Test for {name} ---")
        if node_type == "Action": self.ros.send_action_goal(name, params)
        else: self.ros.call_service(name, params)

    def update_test_log(self, text):
        self.test_log.append(text)
        self.test_log.ensureCursorVisible()

    def generate(self):
        name = self.name_input.text().strip()
        if not name: return QMessageBox.critical(self, "Error", "Name is required")
        fields = [f"{n.text().strip()}:{t.currentText()}" for w, n, t in self.field_rows if n.text().strip()]
        is_condition = self.radio_condition.isChecked()
        try:
            if self.palette_only_cb.isChecked(): self.update_palette_only(name, fields, is_condition)
            else: self.create_node_files(name, fields, is_condition)
            QMessageBox.information(self, "Success", f"Node '{name}' generated.")
            self.refresh_node_list()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def create_empty_tree(self):
        name = self.tree_name_input.text().strip()
        if not name.endswith(".xml"): name += ".xml"
        tree_path = f"src/bt_core/tree/{name}"
        os.makedirs(os.path.dirname(tree_path), exist_ok=True)
        with open(tree_path, 'w') as f:
            f.write(f'<root BTCPP_format="4">\n  <BehaviorTree ID="MainTree">\n    <Sequence>\n      <AlwaysSuccess name="placeholder"/>\n    </Sequence>\n  </BehaviorTree>\n</root>')
        QMessageBox.information(self, "Success", "Empty tree created.")

    def update_palette_only(self, name, fields, is_condition):
        path = "src/bt_core/tree/nodes_library.xml"
        cpp_t = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        ports = "".join([f'            <input_port name="{f.split(":")[0]}" type="{cpp_t[f.split(":")[1]]}"/>\n' for f in fields])
        node_tag = "Condition" if is_condition else "Action"
        node_xml = f'        <{node_tag} ID="{name}">\n{ports}        </{node_tag}>\n'
        add_to_file_after_marker(path, node_xml, "<TreeNodesModel>")

    def create_node_files(self, name, fields, is_condition):
        snake = camel_to_snake(name); node_exec_name = f"{snake}_node"
        cpp_t_map = {"float32": "float", "int32": "int", "string": "std::string", "bool": "bool"}
        if is_condition:
            os.makedirs("src/bt_msgs/srv", exist_ok=True)
            with open(f"src/bt_msgs/srv/{name}.srv", 'w') as f:
                f.write("# Request\n" + "".join([f"{f.split(':')[1]} {f.split(':')[0]}\n" for f in fields]) + "---\n# Result\nbool result\n")
            add_to_file_after_marker("src/bt_msgs/CMakeLists.txt", f'  "srv/{name}.srv"\n', "rosidl_generate_interfaces(${PROJECT_NAME}")
            args_get = "\n        ".join([f"{f.split(':')[0]} = request.{f.split(':')[0]}" for f in fields])
            py_content = f"import rclpy\nfrom rclpy.node import Node\nfrom bt_msgs.srv import {name}\n\nclass {name}Node(Node):\n    def __init__(self):\n        super().__init__('{node_exec_name}')\n        self.srv = self.create_service({name}, '{snake}', self.handle_service)\n        self.get_logger().info('{name} Condition Node initialized')\n\n    def handle_service(self, request, response):\n        {args_get}\n        response.result = True\n        return response\n\ndef main(args=None):\n    rclpy.init(args=args); node = {name}Node(); rclpy.spin(node); rclpy.shutdown()\n\nif __name__ == '__main__': main()"
            with open(f"src/bt_logic/bt_logic/{node_exec_name}.py", 'w') as f: f.write(py_content)
            cpp_path = "src/bt_core/src/main.cpp"
            add_to_file_after_marker(cpp_path, f'#include <bt_msgs/srv/{snake}.hpp>\n', "#include <bt_msgs/srv/condition_check.hpp>")
            ports = ", ".join([f'InputPort<{cpp_t_map[f.split(":")[1]]}>("{f.split(":")[0]}")' for f in fields])
            sets = "\n        ".join([f'getInput("{f.split(":")[0]}", request->{f.split(":")[0]});' for f in fields])
            class_code = f"class {name}Condition : public RosServiceNode<bt_msgs::srv::{name}>\n{{\npublic:\n    {name}Condition(const std::string& name, const NodeConfig& conf, const RosNodeParams& params) : RosServiceNode<bt_msgs::srv::{name}>(name, conf, params) {{}}\n    static PortsList providedPorts() {{ return providedBasicPorts({{ {ports} }}); }}\n    bool setRequest(std::shared_ptr<bt_msgs::srv::{name}::Request>& request) override {{ {sets}\n        return true; }}\n    bool onResponseReceived(const std::shared_ptr<bt_msgs::srv::{name}::Response>& response) override {{ return response->result; }}\n}};\n\n"
            add_to_file_after_marker(cpp_path, class_code, "using namespace BT;")
            add_to_file_after_marker(cpp_path, f'    params.default_port_value = "{snake}";\n    factory.registerNodeType<{name}Condition>("{name}", params);\n', "[ACTION_REGISTRATION_MARKER]")
        else:
            os.makedirs("src/bt_msgs/action", exist_ok=True)
            with open(f"src/bt_msgs/action/{name}.action", 'w') as f:
                f.write("# Request\n" + "".join([f"{f.split(':')[1]} {f.split(':')[0]}\n" for f in fields]) + "---\n# Result\nbool success\n---\n# Feedback\nfloat32 progress\n")
            add_to_file_after_marker("src/bt_msgs/CMakeLists.txt", f'  "action/{name}.action"\n', "rosidl_generate_interfaces(${PROJECT_NAME}")
            args = "\n        ".join([f"{f.split(':')[0]} = goal_handle.request.{f.split(':')[0]}" for f in fields])
            with open(f"src/bt_logic/bt_logic/{node_exec_name}.py", 'w') as f:
                f.write(f"import time\nimport rclpy\nfrom rclpy.action import ActionServer\nfrom rclpy.node import Node\nfrom bt_msgs.action import {name}\n\nclass {name}Node(Node):\n    def __init__(self):\n        super().__init__('{node_exec_name}')\n        self._action_server = ActionServer(self, {name}, '{snake}', self.execute_callback)\n        self.get_logger().info('{name} Node initialized')\n\n    def execute_callback(self, goal_handle):\n        self.get_logger().info('Executing {name}...')\n        {args}\n        goal_handle.succeed()\n        return {name}.Result(success=True)\n\ndef main(args=None):\n    rclpy.init(args=args); node = {name}Node(); rclpy.spin(node); rclpy.shutdown()\n\nif __name__ == '__main__': main()")
            cpp_path = "src/bt_core/src/main.cpp"
            add_to_file_after_marker(cpp_path, f'#include <bt_msgs/action/{snake}.hpp>\n', "#include <rclcpp/rclcpp.hpp>")
            ports = ", ".join([f'InputPort<{cpp_t_map[f.split(":")[1]]}>("{f.split(":")[0]}")' for f in fields])
            sets = "\n        ".join([f'getInput("{f.split(":")[0]}", goal.{f.split(":")[0]});' for f in fields])
            class_code = f"class {name}Action : public RosActionNode<bt_msgs::action::{name}>\n{{\npublic:\n    {name}Action(const std::string& name, const NodeConfig& conf, const RosNodeParams& params) : RosActionNode<bt_msgs::action::{name}>(name, conf, params) {{}}\n    static PortsList providedPorts() {{ return providedBasicPorts({{ {ports} }}); }}\n    bool setGoal(Goal& goal) override {{ {sets}\n        return true; }}\n    NodeStatus onResultReceived(const WrappedResult& wr) override {{ return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE; }}\n}};\n\n"
            add_to_file_after_marker(cpp_path, class_code, "using namespace BT;")
            add_to_file_after_marker(cpp_path, f'    params.default_port_value = "{snake}";\n    factory.registerNodeType<{name}Action>("{name}", params);\n', "[ACTION_REGISTRATION_MARKER]")
        add_to_file_after_marker("src/bt_logic/setup.py", f"            '{node_exec_name} = bt_logic.{node_exec_name}:main',\n", "[CONSOLE_SCRIPTS_MARKER]")
        launch_node = f"        Node(package='bt_logic', executable='{node_exec_name}', name='{node_exec_name}', output='screen'),\n"
        add_to_file_after_marker("src/bt_logic/launch/action_logic.launch.py", launch_node, "[ACTION_NODES_MARKER]")
        self.update_palette_only(name, fields, is_condition)

    def remove_node(self):
        item = self.node_list.currentItem()
        if not item: return
        text = item.text(); node_type, name = text.split(": "); snake = camel_to_snake(name)
        if QMessageBox.question(self, "Confirm", f"Delete {name}?") != QMessageBox.Yes: return
        ext = ".srv" if node_type == "Condition" else ".action"
        subdir = "srv" if node_type == "Condition" else "action"
        for p in [f"src/bt_msgs/{subdir}/{name}{ext}", f"src/bt_logic/bt_logic/{snake}_node.py"]:
            if os.path.exists(p): os.remove(p)
        remove_from_file_by_pattern("src/bt_msgs/CMakeLists.txt", f'"{name}{ext}"')
        remove_from_file_by_pattern("src/bt_logic/setup.py", f"'{snake}_node")
        lp = "src/bt_logic/launch/action_logic.launch.py"
        if os.path.exists(lp):
            with open(lp, 'r') as f: content = f.read()
            content = re.sub(rf'        Node\(.*?executable=\'{snake}_node\'.*?\),?\n', '', content, flags=re.DOTALL)
            with open(lp, 'w') as f: f.write(content)
        cp = "src/bt_core/src/main.cpp"
        if os.path.exists(cp):
            with open(cp, 'r') as f: content = f.read()
            content = re.sub(f'#include <bt_msgs/{subdir}/{snake}.hpp>\n', '', content)
            sfx = "Condition" if node_type == "Condition" else "Action"
            base = f"RosServiceNode<bt_msgs::srv::{name}>" if node_type == "Condition" else f"RosActionNode<bt_msgs::action::{name}>"
            content = re.sub(rf'class {name}{sfx} : public {base}.*?\n}};\n\n', '', content, flags=re.DOTALL)
            content = re.sub(rf'params\.default_port_value = "{snake}";\n    factory\.registerNodeType<{name}{sfx}>\("{name}", params\);\n', '', content)
            with open(cp, 'w') as f: f.write(content)
        pp = "src/bt_core/tree/nodes_library.xml"
        if os.path.exists(pp):
            with open(pp, 'r') as f: content = f.read()
            tag = "Condition" if node_type == "Condition" else "Action"
            content = re.sub(rf'        <{tag} ID="{name}">.*?\n        </{tag}>\n', '', content, flags=re.DOTALL)
            with open(pp, 'w') as f: f.write(content)
        self.refresh_node_list()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ActionManagerGUI()
    ex.show()
    sys.exit(app.exec())
