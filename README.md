# Nurse Stress Prediction with Wearable Sensors

**Reproducible research pipeline for nurse stress classification using Empatica E4 signals and survey annotations.**

[![Licence: GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-blue)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB)](pyproject.toml)
[![Dataset: Dryad](https://img.shields.io/badge/data-Dryad%20DOI-4078c0)](https://doi.org/10.5061/dryad.5hqbzkh6f)

This repository explores whether physiological measurements recorded from wearable sensors can help classify self-reported stress events in a hospital setting. The original project was completed during the **2022–2023 academic year** at the **University of Essex**, as coursework for the **CE888: Data Science and Decision Making** module (2023 course year). It began as a notebook-based university project and was subsequently reorganised in 2026 to make the code portable, the data source traceable and the evaluation safer against participant leakage.

**Project history:** The original academic analysis dates to **2022–2023**. The updated code, documentation and validation pipeline are part of a **2026 reproducibility refresh**, not new clinical research or independently verified historical performance.

> **Research only.** The tools are not clinically validated and must not be used for medical diagnosis, employee surveillance or decisions about individual workers. No live participant data, patient records or external AI service is required to run the demonstration.

## Academic background

- **Institution:** University of Essex, United Kingdom
- **Module:** CE888 - Data Science and Decision Making
- **Academic year:** 2022–2023 (2023 course year)
- **Original work:** University module project exploring nurse stress classification using an existing published wearable-sensor dataset
- **Current release:** Engineering and reproducibility updates prepared in 2026; historical coursework remains available under `archive/`

The university/course attribution describes **where the student project originated**. The underlying nurse-sensor recordings were collected and published by the study authors credited under [Source dataset and scholarly attribution](#source-dataset-and-scholarly-attribution), not by this student project.

## What is included

- **Wearable data preparation:** Read ACC (three axes), EDA, heart rate and skin temperature from Empatica E4 CSV files.
- **Time alignment:** Aggregate signals to one-second intervals, filling only short gaps forward within a recording.
- **Survey labelling:** Convert local event times to UTC; keep labels 0 (no stress), 1 (medium stress) and 2 (high stress). Discard conflicting overlap intervals.
- **Evaluation:** Separate participants between training and testing using `GroupShuffleSplit`.
- **Baselines:** Majority-class dummy model, class-weighted logistic regression and random forest.
- **Reporting:** Save per-class precision, recall and F1, macro F1, balanced accuracy, confusion matrices and group counts as JSON.
- **Synthetic demo:** Test the code with fabricated sensor values, without downloading the research dataset.

## Quick start (works without research data)

Requires **Python 3.11+**. Commands below work on Windows, macOS and Linux from the repository root.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

python -m nurse_stress demo --out data/demo_labeled.csv
python -m nurse_stress train --data data/demo_labeled.csv --out results/demo_metrics.json --synthetic-demo
```

The above scores are **synthetic functional demonstrations, not validated nurse-stress prediction results**.

## Reproduce an experiment with the real dataset

Download the original source files from **[Dryad, DOI 10.5061/dryad.5hqbzkh6f](https://doi.org/10.5061/dryad.5hqbzkh6f)**:

- `Stress_dataset.zip` (approximately 1.16 GB)
- `SurveyResults.xlsx`

Keep original files local. The full raw dataset is intentionally **not copied into this code repository**.

```bash
# Optional: safely expand the outer archive and nested recording ZIPs.
python -m nurse_stress unpack --archive /path/to/Stress_dataset.zip --out data/raw

# Each recording should appear as .../<participant>/<session>/ACC.csv, EDA.csv, HR.csv, TEMP.csv
python -m nurse_stress preprocess --raw data/raw --survey /path/to/SurveyResults.xlsx --out data/processed/labeled.csv
python -m nurse_stress train --data data/processed/labeled.csv --out results/metrics.json
```

The study description refers to US Central Standard Time, while the historical notebook handled daylight saving time. The new pipeline defaults to `America/Chicago` **with daylight saving rules**. Verify alignment against sensor timestamps before treating any evaluation as reproducible; `--timezone Etc/GMT+6` uses a fixed UTC-6 offset. See [Data guide](docs/DATA.md) for details.

**Actual results are not bundled** because the full raw sensor dataset was not available for independent rerunning. A valid evaluation needs the original recordings and participant-disjoint testing. See [Methods and limitations](docs/METHODS.md).

## Project structure

```text
nurse_stress/           Portable Python package and CLI
notebooks/              Clean example for Jupyter users (no stored outputs)
archive/                Original scripts and output-free historical notebook
                          (preserved, not supported)
tests/                  Synthetic preprocessing, timezone, leakage and ZIP-security tests
docs/                   Dataset provenance, methodology and review notes
.github/workflows/      Automated tests for supported Python versions
data/                   Local data directory (real data ignored by Git)
results/                Local reports (ignored by Git)
```

## Why the previous 99.64% accuracy is not a validated result

The historical notebook split highly correlated measurements **by row**, which may place records from the same participant and session in both train and test. This is a substantial risk of overly optimistic evaluation. It also used varying split ratios across models and used regression-oriented metrics for class labels. The older accuracy is kept only in the [review notes](docs/REVIEW_NOTES.md) for historical context.

The revised workflow holds out entire **participants**, compares against a simple majority-class baseline and reports macro-averaged metrics. This is a more defensible evaluation, but the small number of participants, survey labelling limitations and possible temporal dependence still restrict conclusions. See the [scikit-learn grouped cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).

## Source dataset and scholarly attribution

This project uses (but does not own) the dataset described in:

> Hosseini, S., Gottumukkala, R., Katragadda, S., Bhupatiraju, R. T., Ashkar, Z., Borst, C. W. & Cochran, K. (2022). *A multimodal sensor dataset for continuous stress detection of nurses in a hospital*. Scientific Data, 9, 255. https://doi.org/10.1038/s41597-022-01361-y

> Hosseini, S. et al. (2021). *A multi-modal sensor dataset for continuous stress detection of nurses in a hospital* [Dataset]. Dryad. https://doi.org/10.5061/dryad.5hqbzkh6f

The Dryad dataset is marked CC0 by public metadata providers. **The dataset licence and this repository's code licence are separate.** Please verify the dataset's latest terms at its original landing page before any redistribution.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m nurse_stress --help
```

- Read [METHODS.md](docs/METHODS.md) for evaluation decisions and known limitations.
- Read [DATA.md](docs/DATA.md) for raw recording layout and privacy considerations.
- Read [REVIEW_NOTES.md](docs/REVIEW_NOTES.md) for what changed from the original project.
- Contributions and bug reports: see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Licence

**GPL-3.0**, as stated in the repository's original `LICENSE` file. The original README incorrectly referred to MIT; the historical licence has been retained rather than silently changed. Other datasets, publications and third-party images remain subject to their respective terms.
