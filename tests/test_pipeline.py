from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from nurse_stress.demo import generate_demo_dataset
from nurse_stress.modelling import group_split, train_and_evaluate
from nurse_stress.processing import align_recording, find_recordings, label_recording, load_survey, preprocess, read_e4_signal
from nurse_stress.unpack import extract_zip, unpack_dataset


def write_sensor(folder: Path, name: str, start: int, rate: int, n_seconds: int = 3) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f'{name}.csv').open('w', newline='') as handle:
        w = csv.writer(handle)
        w.writerow([start])
        w.writerow([rate])
        for i in range(rate * n_seconds):
            if name == 'ACC':
                w.writerow([i % 4, 2, 3])
            else:
                w.writerow([1.5 if name == 'EDA' else 80 if name == 'HR' else 32])


def make_recording(root: Path, participant: str, session: str, start: int) -> Path:
    folder = root / participant / session
    for signal, rate in (('ACC', 32), ('EDA', 4), ('HR', 1), ('TEMP', 4)):
        write_sensor(folder, signal, start, rate)
    return folder


def make_survey(path: Path, entries: list[dict]) -> None:
    pd.DataFrame(entries).to_csv(path, index=False)


def test_e4_read_1hz_mean(tmp_path):
    folder = make_recording(tmp_path, 'P01', 'S01', 1_586_954_400)
    result = read_e4_signal(folder / 'ACC.csv', ('X', 'Y', 'Z'))
    assert len(result) == 3
    assert np.isclose(result['Y'].iloc[0], 2)
    assert np.isclose(result['X'].iloc[0], 1.5)


def test_e4_reject_invalid_header(tmp_path):
    bad = tmp_path / 'ACC.csv'
    bad.write_text('unparseable\n0\n1,2,3\n')
    with pytest.raises(ValueError, match='invalid'):
        read_e4_signal(bad, ('X', 'Y', 'Z'))


def test_timezone_conversion_with_dst(tmp_path):
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [
        {'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:01:00', 'date': '2020-04-15', 'Stress level': 0},
        {'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:01:00', 'date': '2020-11-15', 'Stress level': 2},
    ])
    df = load_survey(survey)
    assert [row.hour for row in df['start_utc']] == [13, 14]
    assert df['label'].tolist() == [0, 2]


def test_overlap_with_different_labels_excludes_ambiguous_seconds(tmp_path):
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [
        {'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:00:02', 'date': '2020-04-15', 'Stress level': 0},
        {'ID': 'P01', 'Start time': '08:00:01', 'End time': '08:00:03', 'date': '2020-04-15', 'Stress level': 2},
    ])
    df = load_survey(survey)
    seconds = pd.Timestamp('2020-04-15T13:00:00Z').timestamp() + np.arange(4)
    label, conflict = label_recording(seconds, 'P01', df)
    assert conflict == 2
    assert label.tolist() == [0, -1, -1, 2]


def test_same_label_overlaps_not_discarded(tmp_path):
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [
        {'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:00:02', 'date': '2020-04-15', 'Stress level': 1},
        {'ID': 'P01', 'Start time': '08:00:01', 'End time': '08:00:03', 'date': '2020-04-15', 'Stress level': 1},
    ])
    seconds = pd.Timestamp('2020-04-15T13:00:00Z').timestamp() + np.arange(4)
    label, conflict = label_recording(seconds, 'P01', load_survey(survey))
    assert conflict == 0
    assert label.tolist() == [1, 1, 1, 1]


def test_preprocess_end_to_end_retains_middle_stress_class(tmp_path):
    root = tmp_path / 'raw'
    t = int(pd.Timestamp('2020-04-15T13:00:00Z').timestamp())
    folder = make_recording(root, 'P01', 'SessionA', t)
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [{'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:00:02',
                          'date': '2020-04-15', 'Stress level': 1}])
    out = tmp_path / 'processed.csv'
    stats = preprocess(root, survey, out)
    df = pd.read_csv(out)
    assert stats['labelled_seconds'] == 3
    assert stats['recordings_failed'] == 0
    assert df['label'].tolist() == [1, 1, 1]
    assert df['participant_id'].iloc[0] == 'P01'
    assert df['HR'].tolist() == [80, 80, 80]
    assert list(df.columns) == ['participant_id', 'session_id', 'datetime_utc', 'X', 'Y', 'Z', 'EDA', 'HR', 'TEMP', 'label']


def test_no_backward_fill_at_signal_start(tmp_path):
    t = int(pd.Timestamp('2020-04-15T13:00:00Z').timestamp())
    folder = make_recording(tmp_path, 'P01', 'S01', t)
    write_sensor(folder, 'HR', t + 1, 1, n_seconds=2)
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [{'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:00:02',
                          'date': '2020-04-15', 'Stress level': 0}])
    out, _ = align_recording(folder, 'P01', load_survey(survey))
    assert np.isnan(out['HR'].iloc[0])
    assert out['HR'].iloc[1] == 80


def test_missing_input_recordings_controlled_error(tmp_path):
    root = tmp_path / 'raw'
    root.mkdir()
    survey = tmp_path / 'survey.csv'
    make_survey(survey, [{'ID': 'P01', 'Start time': '08:00:00', 'End time': '08:00:02',
                          'date': '2020-04-15', 'Stress level': 1}])
    with pytest.raises(ValueError, match='No complete recordings'):
        preprocess(root, survey, tmp_path / 'processed.csv')


def test_demo_is_deterministic(tmp_path):
    a = tmp_path / 'a.csv'; b = tmp_path / 'b.csv'
    assert generate_demo_dataset(a) == 2160
    assert generate_demo_dataset(b) == 2160
    assert a.read_bytes() == b.read_bytes()
    assert pd.read_csv(a)['participant_id'].nunique() == 12


def test_train_subject_disjoint_and_baselines(tmp_path):
    data = tmp_path / 'demo.csv'
    generate_demo_dataset(data)
    out = tmp_path / 'metrics.json'
    result = train_and_evaluate(data, out, dataset_type='synthetic_demo', n_estimators=12)
    assert json.loads(out.read_text()) == result
    assert result['split']['participant_disjoint'] is True
    assert result['split']['train_participants'] + result['split']['test_participants'] == 12
    assert set(result['models']) == {'majority_baseline', 'logistic_regression', 'random_forest'}
    assert all(0 <= v['macro_f1'] <= 1 for v in result['models'].values())
    assert result['dataset_type'] == 'synthetic_demo'


def test_group_split_no_shared_subjects(tmp_path):
    df = pd.DataFrame({'participant_id': list('AAAABBBBCCCCDDDD'), 'label': [0, 1] * 8})
    tr, te = group_split(df)
    assert not set(df.iloc[tr]['participant_id']) & set(df.iloc[te]['participant_id'])


def test_group_split_requires_enough_participants():
    df = pd.DataFrame({'participant_id': ['A', 'A', 'B', 'B'], 'label': [0, 1, 0, 1]})
    with pytest.raises(ValueError, match='4 independent'):
        group_split(df)


def test_zip_reject_path_traversal(tmp_path):
    attack = tmp_path / 'evil.zip'
    with ZipFile(attack, 'w') as z:
        z.writestr('../outside.txt', 'should never write')
    with pytest.raises(ValueError, match='Unsafe'):
        extract_zip(attack, tmp_path / 'unpack')
    assert not (tmp_path / 'outside.txt').exists()


def test_nested_zip_unpack(tmp_path):
    import io
    nested = io.BytesIO()
    with ZipFile(nested, 'w') as z:
        z.writestr('ACC.csv', '1586954400\n32\n1,2,3\n')
    top = tmp_path / 'dataset.zip'
    with ZipFile(top, 'w') as z:
        z.writestr('P01/session.zip', nested.getvalue())
    result = unpack_dataset(top, tmp_path / 'data')
    assert result['archives_extracted'] == 2
    assert (tmp_path / 'data/P01/session/ACC.csv').exists()


def test_find_recordings_in_nested_tree(tmp_path):
    make_recording(tmp_path / 'raw' / 'dataset', 'P01', 'S01', 1586954400)
    participants = find_recordings(tmp_path / 'raw')
    assert len(participants) == 1 and participants[0][0] == 'P01'
