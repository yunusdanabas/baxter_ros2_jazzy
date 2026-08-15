#!/bin/bash
# Regenerate the figures that are derived from the workspace rather than drawn
# by hand. Run from a built, sourced workspace:
#
#   source /opt/ros/jazzy/setup.bash && source install/setup.bash
#   bash docs/manual/figures/generate.sh
#
# The TikZ and pgfplots figures are source files and are not touched here.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
cd "$REPO_ROOT"

command -v dot >/dev/null || { echo "need graphviz (dot)" >&2; exit 1; }
command -v ros2 >/dev/null || { echo "source the workspace first" >&2; exit 1; }

URDF="$(mktemp)"
trap 'rm -f "$URDF"' EXIT
ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro >"$URDF"

# The kinematic tree straight from the model. Deriving it from the URDF rather
# than from `tf2_tools view_frames` keeps it reproducible with nothing running,
# and it is the model's tree that the manual is describing.
python3 - "$URDF" "$HERE/tf_tree.dot" <<'PY'
import sys
import xml.etree.ElementTree as ET

urdf, out = sys.argv[1], sys.argv[2]
root = ET.parse(urdf).getroot()

ARM = ('_s0', '_s1', '_e0', '_e1', '_w0', '_w1', '_w2')
lines = [
    'digraph tf {',
    '  rankdir=LR;',
    '  node [shape=box, style="rounded,filled", fontname="Helvetica",',
    '        fontsize=9, margin="0.06,0.03"];',
    '  edge [fontname="Helvetica", fontsize=7, color="#8B949E"];',
]
for joint in root.findall('joint'):
    name = joint.attrib['name']
    jtype = joint.attrib.get('type', 'fixed')
    parent = joint.find('parent').attrib['link']
    child = joint.find('child').attrib['link']
    if jtype == 'fixed':
        colour = '#F6F8FA'
    elif name.endswith(ARM):
        colour = '#EEF4FF'
    else:
        colour = '#FFF4E5'
    lines.append(f'  "{child}" [fillcolor="{colour}"];')
    style = '' if jtype != 'fixed' else ', style=dashed'
    label = name if jtype != 'fixed' else ''
    lines.append(f'  "{parent}" -> "{child}" [label="{label}"{style}];')
lines.append('  "world" [fillcolor="#FFFFFF", shape=doublecircle];')
lines.append('}')

with open(out, 'w') as handle:
    handle.write('\n'.join(lines) + '\n')
print(f'wrote {out}')
PY

dot -Tpdf "$HERE/tf_tree.dot" -o "$HERE/tf_tree.pdf"
echo "wrote $HERE/tf_tree.pdf"

cat <<'EOF'

Screenshots are not generated: they need a GUI session. Capture them yourself.

  ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false
  # -> docs/manual/figures/sim_rviz.png

  ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false
  # -> docs/manual/figures/moveit_rviz.png

The manual builds without them; the figures degrade to a placeholder box.
EOF
