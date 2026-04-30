cmake_minimum_required(VERSION 3.8)
project(bt_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/CheckBattery.srv"
  "srv/ConditionCheck.srv"
  "action/TekitoAction.action"
  "action/CleanRoom.action"
  "action/SaySomething.action"
  "action/MoveToTarget.action"
  "action/PickUpItem.action"
  DEPENDENCIES action_msgs
)

ament_package()
