# Review and repository improvements

This release was rebuilt from the uploaded `nurse-stress-prediction-wearable-sensors-main.zip` (4 November 2026), while preserving historical material under `archive/` without the notebook's personal observations and stored outputs. The **original university coursework** was undertaken in the **2022–2023 academic year** at the **University of Essex** for the **CE888: Data Science and Decision Making** module. The 2026 release is a subsequent code/documentation refresh and must not be presented as new coursework or a new clinical validation.

## Corrected

1. Repository README claimed MIT but the file `LICENSE` contains the **GNU GPL v3**. The existing licence is preserved and documentation made consistent.
2. README referred to `data/`, `src/`, `notebooks/` and `requirements.txt` files that did not exist in the supplied archive. New real module, notebook, dependencies and directory docs are included.
3. Old preprocessing scripts relied on `C:\\Users\\...` absolute file paths. New CLI accepts configurable file locations and works on Windows, Linux and macOS.
4. Old timestamp joining used exact float time comparisons and both forward/backward filling. New pipeline aggregates at 1 Hz and limits imputation to two seconds forward **inside** each recording.
5. Original survey conversion hardcoded daylight-saving dates. New implementation supports the IANA `America/Chicago` zone and configurable fixed-offset option; timezone verification remains necessary.
6. Historical research code excluded label 1 in one run and duplicated some descriptive summaries. New pipeline retains categories 0, 1 and 2 and discards contradictory overlapping intervals.
7. Historical model evaluation used random row-wise splits and inconsistent test fractions; the same participant could appear in training and test. Revised evaluation holds out whole participants and explicitly compares to a majority baseline.
8. Historical notebook reported up to 99.64% accuracy and misleading regression metrics on class IDs. New code reports suitable classification metrics but **no replacement real-data result is asserted**.
9. Source sensor and per-participant survey files were bundled directly in the old GitHub repository. The refreshed public package omits participant-level data and clears notebook outputs. The official Dryad source is properly acknowledged.
10. Added versioned package metadata, a reproducible synthetic demo, tests, optional secure nested ZIP extraction, contributor guidance and GitHub CI workflow.

## Validation scope

The pipeline was tested using synthetic E4-style recordings and generated labelled data. It was **not** validated end-to-end on the complete approximately 1.16 GB official source archive, which was not present in the user upload. GitHub CI has not yet run after this updated package is uploaded.

## Potential follow-on research

- Verify clock offset by comparing actual sensor timestamps and survey intervals.
- Report repeated group-stratified or leave-one-nurse-out estimates with confidence intervals.
- Evaluate missingness, classes, outliers and false-negative costs by participant.
- Improve signal quality filters and study fairness/generalisation across devices and sites.
