cmake_minimum_required(VERSION 3.8)
project(bt_example)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(behaviortree_ros2 REQUIRED)
find_package(bt_msgs REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(bt_node src/main.cpp)
target_include_directories(bt_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_link_libraries(bt_node
  behaviortree_cpp::behaviortree_cpp
  behaviortree_ros2::behaviortree_ros2
)

ament_target_dependencies(bt_node
  bt_msgs
  rclcpp
)

install(TARGETS bt_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY tree
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
