"""Run with python -m src.run --input data/raw/1970-2021_DISASTERS.csv."""
import argparse
import json
from pathlib import Path

from .analysis import load_data, prepare, summarize, tables, source_fingerprint
from .visuals import make_figures

ROOT = Path(__file__).resolve().parents[1]


def run(input_path, output=ROOT / 'reports'):
    output = Path(output)
    raw = load_data(input_path)
    df = prepare(raw)
    summary = summarize(df)
    summary['input_rows'] = len(raw)
    summary['excluded_outside_window'] = len(raw) - len(df)
    summary['input_sha256'] = source_fingerprint(input_path)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'tables').mkdir(exist_ok=True)
    for name, table in tables(df).items():
        table.to_csv(output / 'tables' / f'{name}.csv', index=name == 'type_continent')
    # Do not distribute row-level rankings: these approximate the original losses.
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    make_figures(df, output / 'figures')
    from .report import write_report
    write_report(raw, df, summary, output)
    from .report_en import write_report_en
    write_report_en(raw, df, summary, output)
    return df, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/1970-2021_DISASTERS.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    if not args.input.exists():
        parser.error('Input CSV not found. Follow docs/DATA.md; raw data is not distributed.')
    _, result = run(args.input, args.output)
    print(json.dumps(result, indent=2))
