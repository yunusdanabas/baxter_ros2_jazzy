from setuptools import setup

package_name = "baxter_hardware_bridge"

setup(
    name=package_name,
    version="0.2.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", [
            "launch/hardware_bringup.launch.py",
            "launch/dry_run.launch.py",
        ]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "follow_joint_trajectory_shim = baxter_hardware_bridge.follow_joint_trajectory_shim:main",
            "mock_robot = baxter_hardware_bridge.mock_robot:main",
            "dry_run_test = baxter_hardware_bridge.dry_run_test:main",
            "baxter_safety_check = baxter_hardware_bridge.safety:main",
        ],
    },
)
