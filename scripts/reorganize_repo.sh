#!/usr/bin/env bash
set -euo pipefail
# Dry-run: set DRY_RUN=1 to just print operations
DRY_RUN=${DRY_RUN:-0}
mv_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY] mkdir -p \"$1\" && mv \"$2\" \"$3\""
  else
    mkdir -p "$1"
    mv "$2" "$3"
    echo "Moved $2 -> $3"
  fi
}

echo "Reorganizing repository..."

# Web UI
mv_cmd "web/src/components" "incircle_deformation.txt" "web/src/components/IncircleDeformation.tsx" || true
mv_cmd "web/src/components" "trd_full_simulator.tsx" "web/src/components/trd_full_simulator.tsx" || true
mv_cmd "web/src/components" "trd_full_simulator1.tsx" "web/src/components/trd_full_simulator1.tsx" || true

# Static HTML
mv_cmd "web/static" "trd Lagrangian.html" "web/static/trd_lagrangian.html" || true
mv_cmd "web/static" "TRD omega.html" "web/static/trd_omega.html" || true
mv_cmd "web/static" "TRD test.html" "web/static/trd_test.html" || true

# Python
mv_cmd "py" "riemann_three_tests.py" "py/riemann_three_tests.py" || true
mv_cmd "py" "TRD world map.py" "py/trd_worldmap.py" || true
mv_cmd "py" "trd_explorer_v21 (1).py" "py/trd_explorer_v21_modular.py" || true
mv_cmd "py" "trd_explorer_v21 (2).py" "py/trd_worldmap_dash.py" || true
mv_cmd "py" "trd_explorer_v21.py" "py/trd_explorer_v21.py" || true
mv_cmd "py" "trd_prime_detector.py" "py/trd_prime_detector.py" || true
mv_cmd "py" "trd_sphere_viz (1).py" "py/trd_sphere_viz.py" || true

# Data
mv_cmd "data" "pi_geometric_range.csv" "data/pi_geometric_range.csv" || true

echo "Done. If DRY_RUN=1 was used, run with DRY_RUN=0 to execute moves."
