"""Reproducible Empatica E4 signal alignment and survey-window labelling.

Raw CSV: first row Unix timestamp, second row sample rate, later rows signal values.
No participant records are fetched, downloaded or transmitted by this module.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

LOG = logging.getLogger(__name__)
SIGNALS = {'ACC': ('X', 'Y', 'Z'), 'EDA': ('EDA',), 'HR': ('HR',), 'TEMP': ('TEMP',)}
FEATURES = ('X', 'Y', 'Z', 'EDA', 'HR', 'TEMP')
OUTPUT_COLUMNS = ('participant_id', 'session_id', 'datetime_utc', *FEATURES, 'label')
MAX_RECORDING_SECONDS = 72 * 3600


def read_e4_signal(path: Path, columns: tuple[str, ...], chunksize: int = 200_000) -> pd.DataFrame:
    """Aggregate an E4 CSV to UTC epoch-second means in bounded input chunks."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Missing signal: {path.name}')
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        start_row = next(reader, None)
        freq_row = next(reader, None)
    if not start_row or not freq_row:
        raise ValueError(f'{path.name}: missing timestamp or sampling-rate header')
    try:
        start = float(start_row[0]); frequency = float(freq_row[0])
    except (ValueError, IndexError) as exc:
        raise ValueError(f'{path.name}: invalid timestamp or sampling-rate header') from exc
    if not np.isfinite(start) or not np.isfinite(frequency) or not (0 < frequency <= 1024):
        raise ValueError(f'{path.name}: invalid signal header values')
    if not (1_000_000_000 <= start <= 4_102_444_800):
        raise ValueError(f'{path.name}: timestamp outside supported Unix epoch range')

    pieces_sum: list[pd.DataFrame] = []
    pieces_count: list[pd.DataFrame] = []
    offset = 0
    for chunk in pd.read_csv(path, header=None, skiprows=2, names=columns, chunksize=chunksize,
                             dtype=str, on_bad_lines='error'):
        if chunk.empty:
            continue
        elapsed = (offset + np.arange(len(chunk), dtype=np.float64)) / frequency
        if elapsed[-1] > MAX_RECORDING_SECONDS:
            raise ValueError(f'{path.name}: recording exceeds safety duration limit')
        seconds = np.floor(start + elapsed + 1e-8).astype(np.int64)
        numeric = chunk.apply(pd.to_numeric, errors='coerce')
        numeric = numeric.replace([np.inf, -np.inf], np.nan)
        numeric.index = seconds
        pieces_sum.append(numeric.groupby(level=0, sort=True).sum())
        pieces_count.append(numeric.groupby(level=0, sort=True).count())
        offset += len(chunk)
    if not pieces_sum:
        raise ValueError(f'{path.name}: no sensor samples')
    sums = pd.concat(pieces_sum).groupby(level=0).sum()
    counts = pd.concat(pieces_count).groupby(level=0).sum()
    return (sums / counts.where(counts.ne(0))).sort_index()


def load_survey(path: Path, local_timezone: str = 'America/Chicago') -> pd.DataFrame:
    """Load the public study's event survey, retaining only labelling fields."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Survey file does not exist: {path}')
    required = ['ID', 'Start time', 'End time', 'date', 'Stress level']
    if path.suffix.lower() == '.xlsx':
        raw = pd.read_excel(path, usecols=required, dtype={'ID': str})
    elif path.suffix.lower() == '.csv':
        raw = pd.read_csv(path, usecols=required, dtype={'ID': str})
    else:
        raise ValueError('Survey must be an .xlsx or .csv file')

    raw = raw[required].dropna(subset=required).copy()
    raw['ID'] = raw['ID'].astype(str).str.strip()
    raw['label'] = pd.to_numeric(raw['Stress level'], errors='coerce')
    raw = raw[raw['label'].isin((0, 1, 2))].copy()
    if raw.empty:
        raise ValueError('Survey contains no valid 0, 1, 2 stress labels')
    raw['label'] = raw['label'].astype('int64')

    date_part = pd.to_datetime(raw['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    raw['start_local'] = pd.to_datetime(date_part + ' ' + raw['Start time'].astype(str), errors='coerce')
    raw['end_local'] = pd.to_datetime(date_part + ' ' + raw['End time'].astype(str), errors='coerce')
    # Survey events that cross midnight are labelled on the next day.
    crosses_midnight = raw['end_local'] < raw['start_local']
    raw.loc[crosses_midnight, 'end_local'] += pd.Timedelta(days=1)
    # Survey clock times are local to the original Louisiana study (US Central Time).
    # Ambiguous or nonexistent DST times are explicitly discarded, not guessed.
    raw['start_utc'] = raw['start_local'].dt.tz_localize(
        local_timezone, ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    raw['end_utc'] = raw['end_local'].dt.tz_localize(
        local_timezone, ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    n_before = len(raw)
    raw = raw.dropna(subset=['start_utc', 'end_utc']).copy()
    if n_before != len(raw):
        LOG.warning('Dropped %s survey windows with invalid or ambiguous timestamps', n_before-len(raw))
    if raw.empty:
        raise ValueError('Survey has no valid time windows')
    return raw[['ID', 'start_utc', 'end_utc', 'label']].reset_index(drop=True)


def label_recording(seconds: Iterable[int], participant_id: str, survey: pd.DataFrame) -> tuple[np.ndarray, int]:
    """Match 1 Hz UTC samples to survey windows; drop conflicting overlapping labels."""
    seconds_arr = np.asarray(seconds, dtype=np.int64)
    labels = np.full(len(seconds_arr), -1, dtype=np.int64)
    conflicting = np.zeros(len(seconds_arr), dtype=bool)
    windows = survey.loc[survey['ID'] == str(participant_id)]
    for window in windows.itertuples(index=False):
        start = window.start_utc.timestamp()
        end = window.end_utc.timestamp()
        in_window = (seconds_arr >= start) & (seconds_arr <= end)
        conflicting |= in_window & (labels >= 0) & (labels != int(window.label))
        labels[in_window & (labels < 0)] = int(window.label)
    labels[conflicting] = -1
    return labels, int(conflicting.sum())


def align_recording(recording_dir: Path, participant_id: str, survey: pd.DataFrame,
                    session_id: str | None = None) -> tuple[pd.DataFrame, int]:
    """Return labelled data at 1 Hz; never fill backwards or across recordings."""
    recording_dir = Path(recording_dir)
    frames = {sig: read_e4_signal(recording_dir / f'{sig}.csv', cols)
              for sig, cols in SIGNALS.items()}
    acc = frames['ACC']
    seconds = acc.index.to_numpy(dtype=np.int64)
    if len(seconds) == 0:
        return pd.DataFrame(columns=OUTPUT_COLUMNS), 0
    out = acc.copy()
    for key in ('EDA', 'HR', 'TEMP'):
        signal = frames[key].reindex(seconds)
        # Strictly forward-fill only short gaps (up to two seconds) in this recording.
        out = out.join(signal.ffill(limit=2), how='left')
    labels, ambiguous_count = label_recording(seconds, participant_id, survey)
    keep = labels >= 0
    out = out.loc[keep].copy()
    if out.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS), ambiguous_count
    out.insert(0, 'participant_id', str(participant_id))
    out.insert(1, 'session_id', str(session_id or recording_dir.name))
    out.insert(2, 'datetime_utc', pd.to_datetime(out.index, unit='s', utc=True).strftime('%Y-%m-%dT%H:%M:%SZ'))
    out['label'] = labels[keep]
    return out[list(OUTPUT_COLUMNS)].reset_index(drop=True), ambiguous_count


def find_recordings(raw_dir: Path) -> list[tuple[str, Path]]:
    root = Path(raw_dir).resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    found = []
    for acc_path in sorted(root.rglob('ACC.csv')):
        if acc_path.is_symlink() or not acc_path.resolve().is_relative_to(root):
            continue
        folder = acc_path.parent
        if any(not (folder / f'{sig}.csv').is_file() for sig in SIGNALS):
            LOG.warning('Skipping incomplete recording directory: %s', folder)
            continue
        participant = folder.parent.name
        if folder.parent == root:
            LOG.warning('Skipping ambiguous participant directory: %s', folder)
            continue
        found.append((participant, folder))
    return found


def preprocess(raw_dir: Path, survey_path: Path, output: Path,
               local_timezone: str = 'America/Chicago') -> dict[str, int]:
    survey = load_survey(survey_path, local_timezone)
    recordings = find_recordings(raw_dir)
    if not recordings:
        raise ValueError('No complete recordings found. Expected <raw>/<participant>/<session>/ACC.csv, EDA.csv, HR.csv, TEMP.csv')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.resolve() == Path(survey_path).resolve():
        raise ValueError('Output cannot overwrite survey input')
    counts = {'recordings_seen': 0, 'recordings_written': 0, 'labelled_seconds': 0,
              'conflicting_label_seconds_dropped': 0, 'recordings_failed': 0}
    tmp = output.with_name(output.name + '.partial')
    try:
        with tmp.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(OUTPUT_COLUMNS)
            for participant_id, folder in recordings:
                counts['recordings_seen'] += 1
                try:
                    frame, conflicts = align_recording(folder, participant_id, survey)
                except (ValueError, OSError, pd.errors.ParserError) as exc:
                    counts['recordings_failed'] += 1
                    LOG.warning('Skipping invalid recording %s: %s', folder, exc)
                    continue
                counts['conflicting_label_seconds_dropped'] += conflicts
                if not frame.empty:
                    writer.writerows(frame.itertuples(index=False, name=None))
                    counts['recordings_written'] += 1
                    counts['labelled_seconds'] += len(frame)
        if counts['labelled_seconds'] == 0:
            raise ValueError('No labelled sensor samples were produced. Check dataset structure and survey time zone.')
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    return counts
