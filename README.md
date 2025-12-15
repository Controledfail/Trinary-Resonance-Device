# Trinary Resonance Device (TRD)

This repository collects simulations, visualizers and analysis tools for the Trinary Resonance Device project.

Structure (recommended)
- web/: React UI and static HTML demos
  - web/src/components: TSX components
  - web/static: standalone HTML demos
- py/: Python analysis and Dash visualizers
- data/: CSV and other datasets
- scripts/: helper and maintenance scripts
- docs/: design notes, derivations, papers
- tests/: unit and integration tests

Quick start (Python)
1. Create a venv and install:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Run a script:
   python py/trd_worldmap.py

Quick start (Web)
1. Install dependencies and run:
   cd web
   npm install
   npm run dev

Contributing
- Use the `reorg/structure` branch for reorganization.
- Keep large data in `data/`.
- Add unit tests in `tests/` for any numeric code (use pytest).

License
- Add an appropriate LICENSE file (MIT, Apache-2.0, etc).
