# Contributing

Thanks for improving this research project. Open an issue before introducing new models, data sources or major preprocessing changes so evaluation remains comparable.

1. Clone the project and set up Python 3.11+.
2. Run `python -m pip install -r requirements-dev.txt`.
3. Run `python -m pytest -q` and confirm the CLI synthetic demo passes.
4. Keep holdout splits participant-disjoint and show the class distribution and metrics.
5. Add tests for bug fixes and record any changes to timestamps or labels.
6. Never attach real participant survey files, raw physiological recordings, model artefacts containing private data or access tokens to an issue or pull request.
7. Keep source citations and licensing clear.

The original raw dataset is available separately through Dryad. Do not commit it here.
