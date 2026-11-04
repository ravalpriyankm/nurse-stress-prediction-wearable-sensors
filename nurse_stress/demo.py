"""Generate deterministic, completely synthetic data for smoke tests only."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def generate_demo_dataset(output: Path, seed: int = 11, participants: int = 12,
                          seconds_per_participant: int = 180) -> int:
    if participants < 4 or seconds_per_participant < 30:
        raise ValueError('Need >=4 participants and >=30 seconds per participant')
    rng = np.random.default_rng(seed)
    frames = []
    base_time = pd.Timestamp('2020-04-15T13:00:00Z')
    for i in range(participants):
        labels = np.arange(seconds_per_participant) % 3
        rng.shuffle(labels)
        person_offset = rng.normal(0, 0.2)
        frames.append(pd.DataFrame({
            'participant_id': f'SYN{i+1:03d}',
            'session_id': f'DEMO{i+1:03d}',
            'datetime_utc': pd.date_range(base_time, periods=seconds_per_participant, freq='s').strftime('%Y-%m-%dT%H:%M:%SZ'),
            'X': rng.normal(0, 3, seconds_per_participant),
            'Y': rng.normal(0, 3, seconds_per_participant),
            'Z': rng.normal(0, 3, seconds_per_participant),
            'EDA': rng.normal(1.0 + labels * 0.5 + person_offset, 0.7, seconds_per_participant),
            'HR': rng.normal(75 + labels * 8 + 2 * person_offset, 9, seconds_per_participant),
            'TEMP': rng.normal(32 + labels * 0.2, 0.8, seconds_per_participant),
            'label': labels,
        }))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_csv(output, index=False)
    return participants * seconds_per_participant
