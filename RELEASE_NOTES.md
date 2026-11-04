# Public repository refresh - 4 November 2026

This is a source-code and documentation refresh of the existing nurse stress prediction research repository. The project originally arose from **University of Essex CE888: Data Science and Decision Making module coursework (academic year 2022–2023)**. It is **not** a publication of newly validated clinical or research performance results.

Highlights:
- Source licence documentation corrected to match the existing GPL-3.0 file.
- Clear links and attribution to the primary Dryad dataset and associated research paper.
- Portable sensor preprocessing and survey-event matching with safer timestamp alignment.
- Participant-disjoint evaluation with baseline comparator and classification-focused metrics.
- Synthetic sample data generator, Jupyter quickstart, tests and automated CI workflow.
- Legacy notebook preserved without stored outputs; original scripts placed in an archive folder.
- Individual-level study records, survey spreadsheets and raw per-participant plots excluded from the release ZIP.

Validation:
- Preprocessing and modelling smoke tests: runnable locally against synthetic data.
- Real `SurveyResults.xlsx`: parsed locally against existing workbook structure (245 usable windows, 15 pseudonymous participant IDs).
- Full 1.16 GB research dataset evaluation: **not run** because full recordings were not in the uploaded ZIP.
- GitHub CI matrix: configured, but only the local environment has been checked so far.

For a clean replacement of your existing GitHub repo, see `docs/UPDATE_GITHUB.md`.
