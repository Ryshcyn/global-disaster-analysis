"""Cleaning and metrics. Unknown impacts remain unknown; no imputation."""
from pathlib import Path
import hashlib

import numpy as np
import pandas as pd

START_YEAR = 1970
END_YEAR = 2020  # Fixed common window; 2021 completeness is not established.
DAMAGE = "Total Damages ('000 US$)"
IMPACTS = ['Total Deaths', 'Total Affected', DAMAGE]
REQUIRED = ['Dis No', 'Year', 'Country', 'ISO', 'Continent', 'Disaster Type',
            'Start Month', *IMPACTS]


def load_data(path):
    """Read the legacy course snapshot; reject ambiguous schemas and IDs."""
    raw = pd.read_csv(path)
    missing = set(REQUIRED) - set(raw.columns)
    if missing:
        raise ValueError(f'Missing required legacy columns: {sorted(missing)}')
    return raw


def prepare(raw, start=START_YEAR, end=END_YEAR):
    df = raw.copy()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].str.strip().replace('', pd.NA)
    for col in ['Year', 'Start Month', *IMPACTS]:
        original = df[col]
        df[col] = pd.to_numeric(original, errors='coerce')
        if (original.notna() & df[col].isna()).any():
            raise ValueError(f'Unparseable numeric values in {col}')
    if df['Year'].isna().any() or ((df['Year'] % 1) != 0).any():
        raise ValueError('Year must be a complete integer field')
    df = df[df['Year'].between(start, end)].copy()
    if df.empty:
        raise ValueError('No records in the selected analysis window')
    if df['Dis No'].isna().any() or df['Dis No'].duplicated().any():
        raise ValueError('Country-impact record IDs must be present and unique')
    if df[['Country', 'ISO', 'Continent', 'Disaster Type']].isna().any().any():
        raise ValueError('Missing grouping identifiers; review before analysis')
    if not df['Dis No'].str.match(r'^\d{4}-\d{4}-[A-Z]{3}$').all():
        raise ValueError('Unexpected legacy country-impact ID format')
    if not (df['Dis No'].str[-3:] == df['ISO']).all():
        raise ValueError('Record ID country suffix differs from ISO')
    for col in IMPACTS:
        if ((df[col] < 0) | (df[col].notna() & ~np.isfinite(df[col]))).any():
            raise ValueError(f'Negative or infinite impact in {col}')
    month = df['Start Month']
    valid_month = month.between(1, 12) & month.eq(month.round())
    df['Month_Invalid'] = month.notna() & ~valid_month
    df['Start Month'] = month.where(valid_month)
    df['Year'] = df['Year'].astype(int)
    df['Event_ID'] = df['Dis No'].str.rsplit('-', n=1).str[0]
    # Calendar month is globally meaningful; no hemisphere-based season assumption.
    df['Decade'] = (df['Year'] // 10) * 10
    return df.reset_index(drop=True)


def group_metrics(df, keys):
    """size counts every record, including records with no event name."""
    return df.groupby(keys, dropna=False).agg(
        records=('Dis No', 'size'),
        damage_observed=(DAMAGE, 'count'),
        reported_damage_thousand_usd=(DAMAGE, lambda s: s.sum(min_count=1)),
        deaths_observed=('Total Deaths', 'count'),
        reported_deaths=('Total Deaths', lambda s: s.sum(min_count=1)),
    ).reset_index().assign(
        damage_coverage_pct=lambda x: x['damage_observed'] / x['records'] * 100,
        deaths_coverage_pct=lambda x: x['deaths_observed'] / x['records'] * 100,
    )


def pareto(df):
    values = df[DAMAGE].dropna().sort_values(ascending=False).to_numpy()
    if not len(values) or values.sum() <= 0:
        return pd.DataFrame(columns=['rank', 'record_share_pct', 'damage_share_pct']), {
            'observed_records': len(values), 'top_records': None, 'top_share_pct': None}
    cumulative = values.cumsum() / values.sum()
    count = int(np.searchsorted(cumulative, .8)) + 1
    ranks = np.arange(1, len(values) + 1)
    return pd.DataFrame({'rank': ranks, 'record_share_pct': ranks / len(values) * 100,
                         'damage_share_pct': cumulative * 100}), {
        'observed_records': len(values), 'top_records': count,
        'top_share_pct': count / len(values) * 100}


def summarize(df):
    _, concentration = pareto(df)
    return {
        'start_year': int(df['Year'].min()), 'end_year': int(df['Year'].max()),
        'records': len(df), 'distinct_event_ids': df['Event_ID'].nunique(),
        'countries': df['ISO'].nunique(),
        'damage_missing_pct': df[DAMAGE].isna().mean() * 100,
        'deaths_missing_pct': df['Total Deaths'].isna().mean() * 100,
        'month_unknown_records': int(df['Start Month'].isna().sum()),
        'invalid_month_records': int(df['Month_Invalid'].sum()),
        'reported_damage_trillion_usd': df[DAMAGE].sum(min_count=1) / 1e9,
        'pareto': concentration,
    }


def source_fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tables(df):
    quality = pd.DataFrame({
        'field': IMPACTS + ['Start Month'],
        'observed': [int(df[c].notna().sum()) for c in IMPACTS + ['Start Month']],
        'missing': [int(df[c].isna().sum()) for c in IMPACTS + ['Start Month']],
        'missing_pct': [df[c].isna().mean() * 100 for c in IMPACTS + ['Start Month']],
    })
    monthly = df.dropna(subset=['Start Month']).groupby('Start Month').size().reindex(
        range(1, 13), fill_value=0).rename('records').rename_axis('month').reset_index()
    return {'annual': group_metrics(df, ['Year']),
            'countries': group_metrics(df, ['Country', 'ISO']),
            'types': group_metrics(df, ['Disaster Type']),
            'continents': group_metrics(df, ['Continent']),
            'monthly': monthly, 'quality': quality,
            'type_continent': pd.crosstab(df['Disaster Type'], df['Continent'])}
