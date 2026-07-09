# Repos And Pins

## Default `.repos`

The default source import is `repos/baxter_core.repos`:

```yaml
repositories:
  baxter_common_ros2:
    type: git
    url: https://github.com/CentraleNantesRobotics/baxter_common_ros2.git
    version: 678bfabea8c895b4134951a6c076217a90b9e0e6
```

Import from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p src
vcs import src < repos/baxter_core.repos
```

Verify the checkout:

```bash
git -C src/baxter_common_ros2 rev-parse HEAD
```

Expected SHA:

```text
678bfabea8c895b4134951a6c076217a90b9e0e6
```

## Pin Rule

Default `.repos` may include only `CentraleNantesRobotics/baxter_common_ros2` at the full pinned SHA above. Do not add unlicensed external imports to the default path.

Pin update rule:

1. Use a full commit SHA, not a branch or tag.
2. Update `repos/baxter_core.repos` only after re-running the default build and sim smoke.
3. Record the new SHA, commands, and evidence in the relevant step log.
4. Do not update pins as part of unrelated docs or feature work.
5. Use the `Dependency pin update` issue template and update release notes when a public support label or compatibility row changes.

## Optional `.repos` Files

| File | Current role | Default path? |
|---|---|---:|
| `repos/baxter_core.repos` | Default ECN source pin. | yes |
| `repos/baxter_sim.repos` | Empty placeholder; no external sim repos. | no-op |
| `repos/baxter_hardware.repos` | Bridge-host-only import, same ECN pin. | no |
| `repos/baxter_experimental.repos` | Empty opt-in placeholder for future fallback work. | no-op |

Hardware and experimental `.repos` files are not part of the default install, devcontainer, or CI path.
