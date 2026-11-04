# Evaluation methods and limitations

## Research question

Can short-interval wearable sensor measurements (accelerometer, electrodermal activity, heart rate and skin temperature) predict survey-labelled stress-event categories for nurses whose data were not used during training?

## Label definitions

The source publication discusses 0 = no stress, 1 = medium stress, 2 = high stress. Only survey-validated intervals are labelled. Unlabelled periods are **not** automatically inferred to be no stress. This matters because the survey event sample is not a random sample of all working hours.

## Preprocessing

1. Read the Empatica E4 CSV headers: starting epoch timestamp and sampling frequency.
2. Aggregate each channel to 1 Hz by the arithmetic mean of measurements within a UTC epoch second. This is an engineering baseline; it is not a clinically established signal-processing standard.
3. Align the channels by timestamp per recording. Fill at most two missing seconds **forward**. Never backfill from the future or across recording boundaries.
4. Interpret survey event times in a configurable local zone. Default: `America/Chicago` using daylight-saving rules. An alternative fixed standard-time offset can be passed using `--timezone Etc/GMT+6`.
5. Label each 1 Hz row when it falls within a survey interval for the **same participant**. Preserve all three stress categories. If two overlapping survey windows disagree about the category, discard those ambiguous seconds.
6. Leave signal missingness as missing. The model imputes with the **training-set** median, never from test labels or test statistics.

> Important timezone uncertainty: the historical notebook used DST offsets (+5 / +6 hours), while the source publication calls its timestamps Central Standard Time (UTC-6). Sensor-survey timestamp matching must be checked on the full raw data to determine which convention is appropriate.

## Evaluation design

- Split at participant level using `GroupShuffleSplit`, fixed random seed, test fraction 25%.
- Apply class weighting only in fitted models. No participant appears in both train and test subsets.
- Compare three methods: majority-class dummy, class-weighted logistic regression, and balanced random forest.
- Report accuracy, balanced accuracy, macro F1, confusion matrices, individual class metrics and counts. Primary descriptive metrics should be **macro F1 / balanced accuracy**, because the classes are imbalanced.
- Training is limited to 200,000 sampled 1 Hz rows by default for practical laptop speed. The sample uses a fixed seed; the reported size and holdout participant counts are saved in JSON. Increase `--max-rows` for larger runs.

This is a single grouped holdout experiment, not cross-site, prospective, multi-seed or external clinical validation. The training algorithm and parameters are deliberately simple baselines, not a claim of state-of-the-art predictive performance.

## Why the original scores are not a valid public benchmark

The preserved notebook reported a 99.64% random-forest accuracy and about 98.12% decision-tree accuracy for row-wise splits on a large time-series sample. Because adjacent samples and the same nurse can appear on both sides, they are vulnerable to participant and temporal leakage. The notebook also:

- Changes the test fraction between models, preventing an apples-to-apples comparison.
- Uses R-squared and regression RMSE for categorical stress classes.
- At times fills missing data backwards using future observations.
- Performs exploratory analyses on the full dataset prior to splitting.
- Reports per-nurse plots that risk exposing individual-level physiological patterns.

The figures above describe the **historical notebook**, not validated estimates of performance on unseen nurses. The new pipeline must be run against the official raw data before replacement empirical metrics can be published.

## Remaining limitations

- Small, non-representative sample of study participants; confidence intervals are not computed.
- User-reported labels have missingness, uncertain temporal precision and uneven class frequencies.
- Evaluation can vary substantially depending on which participants are held out.
- E4 channels have different native sampling rates; 1 Hz means may discard important temporal signals.
- No hyperparameter tuning, external validation, signal quality filtering or calibration.
- Potential sensor and survey timing alignment uncertainty.
- Ethical/privacy restrictions on employee monitoring and health-related inference.

## Suggested further work

Repeat across multiple participant-disjoint splits or leave-one-participant-out cross-validation with uncertainty intervals; examine per-class false negatives, participant-specific failures, signal quality, alternative timestamp conventions and the effect of per-group label prevalence. Use the same held-out participant protocol across candidate models. Never interpret an improvement from one split alone as reliable clinical evidence.
