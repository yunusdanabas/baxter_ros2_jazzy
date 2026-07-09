cmake_minimum_required(VERSION 3.8)
project(baxter_examples)

find_package(ament_cmake REQUIRED)

install(PROGRAMS baxter_examples/sim_tiny_trajectory.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME sim_tiny_trajectory
)

install(PROGRAMS baxter_examples/moveit_left_tiny.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME moveit_left_tiny
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
