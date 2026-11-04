# Replacing the existing public GitHub repository

Repository: https://github.com/ravalpriyankm/nurse-stress-prediction-wearable-sensors

The downloadable ZIP is **source files**, not a Git repository. Do not upload the ZIP itself as a single file and expect GitHub to expand it. Extract the archive first.

## Recommended procedure (existing Git repository)

1. Backup any unpublished local modifications and confirm you have permission to update the repository.
2. Clone the existing repo using Git:

   ```bash
   git clone https://github.com/ravalpriyankm/nurse-stress-prediction-wearable-sensors.git
   cd nurse-stress-prediction-wearable-sensors
   ```

3. Extract the provided updated ZIP somewhere else. Copy **the contents** of its `nurse-stress-prediction-wearable-sensors/` folder into the cloned repo, replacing matching source files. Do not copy any `.git` directory or local raw research data.
4. Remove obsolete root-level files *only after checking you have backups*:

   - `main.ipynb` (an output-free copy is now in `archive/legacy_analysis.ipynb`)
   - `Pre-Processing Python Files/` (archived under `archive/original_scripts/`)
   - `images/` (the old participant-specific plots and misleading maxima chart are excluded from the revised public package)
   - `SurveyResults.xlsx`, `survey_results_cleaned.csv`, `survey_results_cleaned.xlsx` and any other local participant-level datasets.

5. Review exactly what will change:

   ```bash
   git status --short
   git diff --stat
   git add -A
   git diff --cached --stat
   git diff --cached --check
   ```

6. Run tests and commit:

   ```bash
   python -m pip install -r requirements-dev.txt
   python -m pytest -q
   git commit -m "Rebuild reproducible nurse stress research pipeline and documentation"
   git push
   ```

## Important: Git history privacy

Deleting `SurveyResults.xlsx` or other tracked data in a new commit removes them from the *latest version*, **not from older commits or forks**. These records come from an openly indexed research archive, but physiological and survey data still warrant privacy review. If you need to purge prior data, assess the historical content and follow GitHub's official guidance for removing sensitive information from a repository. Coordinate history rewriting with collaborators, as it changes commit identifiers.

## Suggested GitHub repository description

> University of Essex CE888 (2022-2023) coursework: wearable-sensor stress prediction, rebuilt for reproducible Python analysis and participant-disjoint evaluation.

Include the academic context in the README, but keep the original Dryad dataset authors credited separately.

## After publishing

- Confirm the GitHub Actions test matrix passes on Python 3.11, 3.12 and 3.13.
- In the repository's **About** panel, add a concise description and topics such as `machine-learning`, `wearable-sensors`, `stress-detection`, `python`, `reproducible-research`, `healthcare-data`, `scikit-learn`.
- Link the Dryad DOI in the README rather than reposting raw nurse data.
- Keep the GPL-3.0 licence unless there is a separate conscious and legally permitted relicensing decision.
- Feature the repository on your GitHub profile after the README, tests and data rights are verified.
