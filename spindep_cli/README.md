# spindep-cli

Command-line interface for the SPINDEP physics engine. Provides the `spin` terminal command.

## Install

```bash
cd spindep-cli
pip install -e .
```

Requires **spindep-core** to be present. The CLI searches for it automatically in the following order:

1. Sibling `spindep-core/` directory (monorepo layout — recommended)
2. Legacy in-tree `src/` or `spindep/src/`
3. `SPINDEP_HOME` environment variable
4. `~/spindep_framework/spindep-core/`

## Usage

```
spin run       --data ./datasets          # Full pipeline
spin test      matter.csv anti.csv        # Quick CPT test on two files
spin validate  --data ./datasets          # Pre-flight checks
spin import    --from /data --coupling gAgA --potential V2 ...
spin gaps      --data ./datasets          # Gap figures only
spin atlas     --data ./datasets          # Constraint atlas only
spin config    myrun.yaml                 # Run from a config file
spin batch     jobs.yaml                  # Run multiple jobs
spin info      --data ./datasets          # Framework status
```

## Monorepo layout

```
spindep_framework/
├── spindep-core/   ← physics engine (src/parser.py, src/pipeline.py, …)
├── spindep-cli/    ← this package  (spin command)
├── spindep-api/    ← FastAPI service
└── gui/            ← React frontend
```

## Config files

### spin_run.yaml

```yaml
command: run
data:    ./datasets
output:  ./results
```

### spin_test.yaml

```yaml
command:    test
matter:     ./data/electron_bounds.csv
antimatter: ./data/positron_bounds.csv
plot:       ./results/cpt_test.png
save:       ./results/cpt_results.csv
points:     300
```

### spin_import.yaml

```yaml
command:              import
from:                 /path/to/my/csv/files
dest:                 ./datasets/normalized
coupling:             gAgA
potential:            V2
sector_matter:        ee
sector_antimatter:    eebar
interaction_class:    lepton-lepton
run:                  true
```

### spin_batch_jobs.yaml

```yaml
- name: "gAgA V2 electron sector"
  command: run
  data:   ./datasets/gAgA_V2
  output: ./results/gAgA_V2

- name: "Quick test — positronium vs torsion balance"
  command:    test
  matter:     ./data/torsion_ee.csv
  antimatter: ./data/positronium_eebar.csv
  plot:       ./results/torsion_vs_positronium.png
  save:       ./results/torsion_vs_positronium.csv
```