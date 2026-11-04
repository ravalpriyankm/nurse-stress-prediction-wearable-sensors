Most generated result files are ignored by Git. The included `demo_metrics.json` is a **synthetic example**, not an evaluated result on the nurse dataset. Recreate reports with:

    python -m nurse_stress demo --out data/demo_labeled.csv
    python -m nurse_stress train --data data/demo_labeled.csv --out results/demo_metrics.json --synthetic-demo

Synthetic demonstration metrics are not peer-reviewed model performance estimates.
