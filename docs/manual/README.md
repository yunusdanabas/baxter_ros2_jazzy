# Manual

LaTeX sources for *Baxter on ROS 2 Jazzy*, a ~30-page workspace manual assembled
from the documentation in `docs/`. Sources are tracked; the built PDF is not.

```bash
cd docs/manual
make            # -> baxter_manual.pdf
make clean
```

Needs TeX Live with `tikz`, `pgfplots`, `listings`, `tcolorbox`, `booktabs`,
`tabularx` — all in `texlive-latex-extra` / `texlive-pictures`.

## Figures

All figures are original to this repository and BSD-3-Clause with it. The legacy
Rethink PDFs under `docs/reference/baxter_legacy/` were used as *information*
sources for Chapter 2; no artwork was taken from them, and none of their figures
appear here.

| Figure | Kind | Regenerate |
|---|---|---|
| `architecture.tex` | TikZ | hand-drawn |
| `safety_gate.tex` | TikZ | hand-drawn |
| `kinematic_chain.tex` | TikZ | hand-drawn, limits from the shim's `JOINT_LIMITS` |
| `lag_vs_velocity.tex` | pgfplots | measured 2026-07-25, three points |
| `tf_tree.pdf` | graphviz | `bash figures/generate.sh` |
| `sim_rviz.png`, `moveit_rviz.png` | screenshots | needs a GUI session, see below |

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
bash docs/manual/figures/generate.sh      # tf_tree only
```

Screenshots are captured by hand because they need a display:

```bash
ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false        # -> sim_rviz.png
ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false  # -> moveit_rviz.png
```

The manual builds without them — missing artwork degrades to a visible
placeholder box rather than failing the build.

## Keeping it honest

Chapters restate material from `docs/`; that directory is the source of truth and
CI checks it. If the two disagree, fix the manual. Every hardware number in the
manual has been cross-checked against `docs/support_matrix.md`, and the joint
limit and shim parameter tables against
`src/baxter_hardware_bridge/.../follow_joint_trajectory_shim.py`.
