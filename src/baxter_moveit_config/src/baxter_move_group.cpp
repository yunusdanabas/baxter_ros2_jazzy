/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2012, Willow Garage, Inc.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following disclaimer
 *     in the documentation and/or other materials provided with the distribution.
 *   * Neither the name of Willow Garage nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 *********************************************************************/

// Based on MoveIt 2.12.4 move_group.cpp.

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <boost/tokenizer.hpp>
#include <moveit/macros/console_colors.hpp>
#include <moveit/move_group/move_group_capability.hpp>
#include <moveit/move_group/move_group_context.hpp>
#include <moveit/moveit_cpp/moveit_cpp.hpp>
#include <moveit/trajectory_execution_manager/trajectory_execution_manager.hpp>
#include <moveit/utils/logger.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/rclcpp.hpp>

namespace
{
std::atomic_bool stop_requested{ false };

void request_stop(int)
{
  stop_requested.store(true);
}

rclcpp::Logger get_logger()
{
  return moveit::getLogger("moveit.ros.move_group.executable");
}

constexpr const char* DEFAULT_CAPABILITIES[] = {
  "move_group/LoadGeometryFromFileService",
  "move_group/SaveGeometryToFileService",
  "move_group/GetUrdfService",
  "move_group/MoveGroupCartesianPathService",
  "move_group/MoveGroupKinematicsService",
  "move_group/MoveGroupExecuteTrajectoryAction",
  "move_group/MoveGroupMoveAction",
  "move_group/MoveGroupPlanService",
  "move_group/MoveGroupQueryPlannersService",
  "move_group/MoveGroupStateValidationService",
  "move_group/MoveGroupGetPlanningSceneService",
  "move_group/ApplyPlanningSceneService",
  "move_group/ClearOctomapService",
};

class MoveGroupExecutable
{
public:
  MoveGroupExecutable(const moveit_cpp::MoveItCppPtr& moveit_cpp, const std::string& default_pipeline, bool debug)
  {
    bool allow_trajectory_execution;
    moveit_cpp->getNode()->get_parameter_or("allow_trajectory_execution", allow_trajectory_execution, true);
    context_ = std::make_shared<move_group::MoveGroupContext>(moveit_cpp, default_pipeline,
                                                              allow_trajectory_execution, debug);
    configure_capabilities();
  }

  ~MoveGroupExecutable()
  {
    capabilities_.clear();
    context_.reset();
    capability_loader_.reset();
  }

  void status() const
  {
    if (!context_)
    {
      RCLCPP_ERROR(get_logger(), "No MoveGroup context created. Nothing will work.");
      return;
    }
    if (!context_->status())
      return;
    if (capabilities_.empty())
      RCLCPP_WARN(get_logger(), "move_group is running but no capabilities are loaded.");
    else
      RCLCPP_INFO(get_logger(), "You can start planning now!");
  }

  void stop() const
  {
    if (!context_)
      return;
    context_->trajectory_execution_manager_->stopExecution();
  }

private:
  void configure_capabilities()
  {
    try
    {
      capability_loader_ = std::make_shared<pluginlib::ClassLoader<move_group::MoveGroupCapability>>(
          "moveit_ros_move_group", "move_group::MoveGroupCapability");
    }
    catch (const pluginlib::PluginlibException& error)
    {
      RCLCPP_FATAL(get_logger(), "Unable to create move_group capability loader: %s", error.what());
      return;
    }

    std::set<std::string> capability_names(std::begin(DEFAULT_CAPABILITIES), std::end(DEFAULT_CAPABILITIES));
    std::string configured;
    if (context_->moveit_cpp_->getNode()->get_parameter("capabilities", configured))
    {
      boost::char_separator<char> separator(" ");
      boost::tokenizer<boost::char_separator<char>> tokens(configured, separator);
      capability_names.insert(tokens.begin(), tokens.end());
    }
    for (const auto& pipeline : context_->moveit_cpp_->getPlanningPipelines())
    {
      if (context_->moveit_cpp_->getNode()->get_parameter(pipeline.first + ".capabilities", configured))
      {
        boost::char_separator<char> separator(" ");
        boost::tokenizer<boost::char_separator<char>> tokens(configured, separator);
        capability_names.insert(tokens.begin(), tokens.end());
      }
    }
    if (context_->moveit_cpp_->getNode()->get_parameter("disable_capabilities", configured))
    {
      boost::char_separator<char> separator(" ");
      boost::tokenizer<boost::char_separator<char>> tokens(configured, separator);
      for (const auto& name : tokens)
        capability_names.erase(name);
    }

    for (const auto& name : capability_names)
    {
      try
      {
        move_group::MoveGroupCapabilityPtr capability = capability_loader_->createUniqueInstance(name);
        capability->setContext(context_);
        capability->initialize();
        capabilities_.push_back(capability);
      }
      catch (const pluginlib::PluginlibException& error)
      {
        RCLCPP_ERROR(get_logger(), "Unable to load move_group capability '%s': %s", name.c_str(), error.what());
      }
    }
  }

  move_group::MoveGroupContextPtr context_;
  std::shared_ptr<pluginlib::ClassLoader<move_group::MoveGroupCapability>> capability_loader_;
  std::vector<move_group::MoveGroupCapabilityPtr> capabilities_;
};
}  // namespace

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv, rclcpp::InitOptions(), rclcpp::SignalHandlerOptions::None);
  std::signal(SIGINT, request_stop);
  std::signal(SIGTERM, request_stop);

  int exit_code = 0;
  rclcpp::NodeOptions options;
  options.allow_undeclared_parameters(true);
  options.automatically_declare_parameters_from_overrides(true);
  auto node = rclcpp::Node::make_shared("move_group", options);
  moveit::setNodeLoggerName(node->get_name());

  moveit_cpp::MoveItCpp::Options moveit_options(node);
  moveit_options.planning_pipeline_options.parent_namespace =
      node->get_effective_namespace() + ".planning_pipelines";
  std::vector<std::string> pipeline_names;
  if (node->get_parameter("planning_pipelines", pipeline_names))
    moveit_options.planning_pipeline_options.pipeline_names = pipeline_names;

  std::string default_pipeline;
  node->get_parameter("default_planning_pipeline", default_pipeline);
  if (default_pipeline.empty() && !pipeline_names.empty())
    default_pipeline = pipeline_names.front();

  auto moveit_cpp = std::make_shared<moveit_cpp::MoveItCpp>(node, moveit_options);
  const auto planning_scene_monitor = moveit_cpp->getPlanningSceneMonitorNonConst();
  if (!planning_scene_monitor->getPlanningScene())
  {
    RCLCPP_ERROR(node->get_logger(), "Planning scene not configured");
    exit_code = 1;
  }
  else
  {
    bool debug = false;
    bool monitor_dynamics = false;
    node->get_parameter("monitor_dynamics", monitor_dynamics);
    if (monitor_dynamics)
      planning_scene_monitor->getStateMonitor()->enableCopyDynamics(true);
    planning_scene_monitor->publishDebugInformation(debug);

    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(node);
    MoveGroupExecutable move_group(moveit_cpp, default_pipeline, debug);
    move_group.status();

    std::thread spinner([&executor]() { executor.spin(); });
    while (rclcpp::ok() && !stop_requested.load())
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    move_group.stop();
    executor.cancel();
    spinner.join();
    executor.remove_node(node);
    RCLCPP_INFO(node->get_logger(), "Stopping move_group before ROS context shutdown");
  }
  rclcpp::shutdown();

  // ponytail: MoveIt 2.12.4 teardown corrupts callback-group waitables
  // (moveit/moveit2#3721); remove this when that upstream bug is fixed.
  std::_Exit(exit_code);
}
