cmake_minimum_required(VERSION 3.8)
project(baxter_moveit_config)

find_package(ament_cmake REQUIRED)
find_package(Boost REQUIRED)
find_package(moveit_core REQUIRED)
find_package(moveit_ros_move_group REQUIRED)
find_package(moveit_ros_planning REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(baxter_move_group src/baxter_move_group.cpp)
ament_target_dependencies(baxter_move_group
  moveit_core
  moveit_ros_move_group
  moveit_ros_planning
  pluginlib
  rclcpp
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

install(FILES .setup_assistant
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS scripts/wait_for_sim_ready.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME wait_for_sim_ready
)

install(TARGETS baxter_move_group
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
