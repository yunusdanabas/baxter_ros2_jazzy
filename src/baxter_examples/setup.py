from setuptools import setup

package_name = "baxter_examples"

setup(
    name=package_name,
    version="0.2.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", [
            "launch/sim_tiny_trajectory.launch.py",
        ]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            # ponytail: ament_python so --symlink-install actually symlinks.
            # install(PROGRAMS) copies even under --symlink-install, which is
            # how two I19 hardware rehearsals silently tested stale code.
            "sim_tiny_trajectory = baxter_examples.sim_tiny_trajectory:main",
            "moveit_left_tiny = baxter_examples.moveit_left_tiny:main",
            # moveit_tiny is the documented alias (moveit_guide.md,
            # ci_release_checklist.md); same entry point, different name.
            "moveit_tiny = baxter_examples.moveit_left_tiny:main",
            "moveit_pose = baxter_examples.moveit_pose:main",
            "ik_service_client = baxter_examples.ik_service_client:main",
        ],
    },
)
