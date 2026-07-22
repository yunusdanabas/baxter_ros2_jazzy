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

install(PROGRAMS baxter_examples/moveit_left_tiny.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME moveit_tiny
)

install(PROGRAMS baxter_examples/moveit_pose.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME moveit_pose
)

install(PROGRAMS baxter_examples/ik_service_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME ik_service_client
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
