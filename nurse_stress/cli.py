"""Portable CLI entry point. No network access or cloud service required."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .demo import generate_demo_dataset
from .modelling import train_and_evaluate
from .processing import preprocess
from .unpack import unpack_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='nurse-stress', description='Reproducible wearable stress research pipeline')
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='Generate synthetic labelled sample data (never clinical results)')
    demo.add_argument('--out', type=Path, default=Path('data/demo_labeled.csv'))
    demo.add_argument('--seed', type=int, default=11)

    unpack = sub.add_parser('unpack', help='Safely expand downloaded nested recording ZIPs')
    unpack.add_argument('--archive', type=Path, required=True)
    unpack.add_argument('--out', type=Path, default=Path('data/raw'))

    prepare = sub.add_parser('preprocess', help='Align extracted E4 recordings with survey intervals')
    prepare.add_argument('--raw', type=Path, required=True, help='Extracted folders: <participant>/<session>/*.csv')
    prepare.add_argument('--survey', type=Path, required=True)
    prepare.add_argument('--out', type=Path, default=Path('data/processed/labeled.csv'))
    prepare.add_argument('--timezone', default='America/Chicago', help='Survey event timezone (IANA name)')

    train = sub.add_parser('train', help='Train and evaluate models on disjoint participants')
    train.add_argument('--data', type=Path, required=True)
    train.add_argument('--out', type=Path, default=Path('results/metrics.json'))
    train.add_argument('--seed', type=int, default=42)
    train.add_argument('--test-size', type=float, default=0.25)
    train.add_argument('--max-rows', type=int, default=200_000)
    train.add_argument('--n-estimators', type=int, default=120)
    train.add_argument('--synthetic-demo', action='store_true', help='Mark results as synthetic demonstration only')

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        if args.command == 'demo':
            print(f'Generated {generate_demo_dataset(args.out, seed=args.seed):,} SYNTHETIC rows at {args.out}')
        elif args.command == 'unpack':
            print(json.dumps(unpack_dataset(args.archive, args.out), indent=2))
        elif args.command == 'preprocess':
            print(json.dumps(preprocess(args.raw, args.survey, args.out, args.timezone), indent=2))
        elif args.command == 'train':
            record = train_and_evaluate(args.data, args.out, args.seed, args.test_size,
                                        args.n_estimators, args.max_rows,
                                        'synthetic_demo' if args.synthetic_demo else 'research')
            print(f'Wrote participant-disjoint evaluation to {args.out}')
            for name, result in record['models'].items():
                print(f'{name}: macro F1={result["macro_f1"]:.3f} | balanced accuracy={result["balanced_accuracy"]:.3f}')
    except (FileNotFoundError, ValueError, NotADirectoryError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    return 0
