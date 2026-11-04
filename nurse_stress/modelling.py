"""Subject-disjoint evaluation of nurse stress classification models."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ('X', 'Y', 'Z', 'EDA', 'HR', 'TEMP')
LABELS = [0, 1, 2]


def group_split(df: pd.DataFrame, test_size: float = 0.25, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    if not (0.1 <= test_size <= 0.5):
        raise ValueError('test_size must be between 0.1 and 0.5')
    if 'participant_id' not in df or 'label' not in df:
        raise ValueError('Data must contain participant_id and label columns')
    groups = df['participant_id'].astype(str)
    if groups.nunique() < 4:
        raise ValueError('At least 4 independent participants are required for hold-out evaluation')
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, df['label'], groups=groups))
    if set(groups.iloc[train_idx]) & set(groups.iloc[test_idx]):
        raise AssertionError('Participant leakage in group split')
    return train_idx, test_idx


def train_and_evaluate(data: Path, output: Path, seed: int = 42,
                       test_size: float = 0.25, n_estimators: int = 120,
                       max_rows: int = 200_000, dataset_type: str = 'research') -> dict:
    data = Path(data)
    if not data.is_file():
        raise FileNotFoundError(data)
    if not (10 <= n_estimators <= 500):
        raise ValueError('n_estimators must be between 10 and 500')
    if max_rows < 100:
        raise ValueError('max_rows must be >= 100')
    if dataset_type not in ('research', 'synthetic_demo'):
        raise ValueError('dataset_type must be research or synthetic_demo')
    needed = ['participant_id', 'label', *FEATURES]
    df = pd.read_csv(data, dtype={'participant_id': str}, usecols=needed, low_memory=False)
    if df.empty:
        raise ValueError('Dataset is empty')
    df['label'] = pd.to_numeric(df['label'], errors='coerce')
    df = df.dropna(subset=['participant_id', 'label']).copy()
    df = df[df['label'].isin(LABELS)].copy()
    if df.empty:
        raise ValueError('No rows have valid labels 0, 1, 2')
    df['label'] = df['label'].astype(int)
    for feature in FEATURES:
        df[feature] = pd.to_numeric(df[feature], errors='coerce').replace([np.inf, -np.inf], np.nan)
    df = df.loc[df[list(FEATURES)].notna().any(axis=1)].copy()
    if df.empty:
        raise ValueError('No usable physiological features')
    # Deterministically cap rows for laptop-friendly experiments. Participants stay disjoint.
    original_rows = len(df)
    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=seed).sort_index().copy()
    train_idx, test_idx = group_split(df, test_size=test_size, seed=seed)
    train = df.iloc[train_idx]
    test = df.iloc[test_idx]
    X_train = train[list(FEATURES)]
    X_test = test[list(FEATURES)]
    y_train = train['label']
    y_test = test['label']
    if y_train.nunique() < 2:
        raise ValueError('Training participant groups contain fewer than 2 stress classes; choose another seed or additional participants')
    if any(X_train[col].notna().sum() == 0 for col in FEATURES):
        raise ValueError('A feature contains only missing values in training data')
    models = {
        'majority_baseline': make_pipeline(SimpleImputer(strategy='median'), DummyClassifier(strategy='most_frequent')),
        'logistic_regression': make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                                             LogisticRegression(max_iter=800, class_weight='balanced', random_state=seed)),
        'random_forest': make_pipeline(SimpleImputer(strategy='median'),
                                     RandomForestClassifier(n_estimators=n_estimators, random_state=seed,
                                                            n_jobs=-1, class_weight='balanced_subsample', min_samples_leaf=2)),
    }
    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        results[name] = {
            'accuracy': round(float(accuracy_score(y_test, predicted)), 5),
            'balanced_accuracy': round(float(balanced_accuracy_score(y_test, predicted)), 5),
            'macro_f1': round(float(f1_score(y_test, predicted, labels=LABELS, average='macro', zero_division=0)), 5),
            'confusion_matrix_labels_0_1_2': confusion_matrix(y_test, predicted, labels=LABELS).tolist(),
            'per_class': classification_report(y_test, predicted, labels=LABELS, output_dict=True, zero_division=0),
        }
    record = {
        'dataset_type': dataset_type,
        'warning': ('Synthetic sample: metrics demonstrate software functionality only, not research performance.'
                    if dataset_type == 'synthetic_demo' else
                    'Research evaluation: participant-disjoint holdout, not externally validated or clinically deployable.'),
        'split': {'method': 'GroupShuffleSplit', 'participant_disjoint': True, 'seed': seed,
                  'test_size': test_size, 'train_participants': int(train['participant_id'].nunique()),
                  'test_participants': int(test['participant_id'].nunique()),
                  'train_rows': len(train), 'test_rows': len(test),
                  'all_input_rows': original_rows, 'sampled_rows': len(df)},
        'features': list(FEATURES),
        'labels': {'0': 'no stress', '1': 'medium stress', '2': 'high stress'},
        'training_label_counts': {str(i): int((y_train == i).sum()) for i in LABELS},
        'test_label_counts': {str(i): int((y_test == i).sum()) for i in LABELS},
        'models': results,
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + '.partial')
    try:
        tmp.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    return record
