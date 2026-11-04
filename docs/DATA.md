# Dataset provenance, layout and privacy

## Official source

- Dryad: https://doi.org/10.5061/dryad.5hqbzkh6f
- Associated peer-reviewed article: https://doi.org/10.1038/s41597-022-01361-y
- Original data attribution: Hosseini, Gottumukkala, Katragadda et al.

Download `Stress_dataset.zip` and `SurveyResults.xlsx` from the original landing page. The experiment uses anonymised participant identifiers but still contains sensitive physiological observations. It is preferable to keep study data local rather than checking raw data, survey spreadsheets, or person-level plots into public source control.

This distribution **does not include** the source recordings, survey workbook, derived per-participant CSV files or the historical notebook outputs.

## Expected layout

After extracting outer and nested ZIPs, the folder structure should contain paths such as:

```text
data/raw/
  Stress_dataset/
    15/
      <recording-name>/
        ACC.csv
        EDA.csv
        HR.csv
        TEMP.csv
        ... other unused E4 channels
    5C/
      <recording-name>/
        ACC.csv
        EDA.csv
        HR.csv
        TEMP.csv
```

`python -m nurse_stress unpack --archive /path/to/Stress_dataset.zip --out data/raw` safely expands nested `.zip` files. It does not follow symlinks or accept path traversal. Free disk space for a multiple-gigabyte extraction and do not use this tool for untrusted arbitrary ZIP archives without independent sandboxing.

`preprocess` searches for complete recording folders (`ACC.csv`, `EDA.csv`, `HR.csv`, `TEMP.csv`). It requires the immediate parent of each recording folder to be a participant ID, as in the original archive. Incomplete recordings are skipped with a warning.

## Label file schema

The original `SurveyResults.xlsx` contains these fields:

| Field | Meaning |
| --- | --- |
| `ID` | Pseudonymous nurse identifier; must match the recording folder |
| `Start time`, `End time` | Local clock times of the survey event |
| `date` | Local date |
| `Stress level` | 0, 1 or 2 stress category |

Only these five fields are read. Free-text or contextual survey responses are not loaded by the application. The dataset was collected in Louisiana in 2020; verify the local-time/DST convention against the original data before analysis.

## Processed output

| Column | Description |
| --- | --- |
| `participant_id` | Pseudonymous subject identifier |
| `session_id` | Recording session name |
| `datetime_utc` | Aligned 1 Hz timestamp in UTC |
| `X`, `Y`, `Z` | One-second averaged accelerometer axes |
| `EDA`, `HR`, `TEMP` | One-second physiological values |
| `label` | Validated survey category |

## Data ownership and licences

The code carries GPL-3.0. Public metadata for the dataset reports CC0, but do not conflate the dataset's rights with the code's rights. Check the original Dryad page for updated terms and respect the privacy/ethics of participants regardless of licence. The associated paper has a separate Creative Commons Attribution licence.

## Privacy-safe publishing notes

- Do not commit `data/raw/`, `data/processed/`, local survey workbooks or generated metrics containing participant-level identifiers.
- Before sharing example visuals, prefer aggregate summaries that do not identify individual participants or reveal granular timelines.
- The original Git history may still include participant-level files. Replacing the working tree in a later commit does **not** remove them from Git history; consider whether history rewriting is warranted after assessing actual redistribution risk.
- Do not use stress predictions for healthcare, personnel management or worker monitoring without the necessary independent scientific, legal and ethical review.
