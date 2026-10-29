"""Figures for the Markdown case study and the companion notebook."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import plotly.express as px

from .analysis import tables, pareto

BLUE = '#255F85'
ORANGE = '#B85B24'


def make_figures(df, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold', 'figure.facecolor': 'white',
                         'svg.hashsalt': 'disaster-analysis'})
    t = tables(df)
    window = f"{df['Year'].min()}–{df['Year'].max()}"
    files = []

    def save(fig, name, note):
        fig.text(.11, .025, note, fontsize=9, color='#444444', va='bottom')
        fig.tight_layout(rect=(0, .075, 1, 1))
        path = output / f'{name}.png'
        fig.savefig(path, dpi=160, metadata={'Software': 'Disaster analysis'})
        plt.close(fig)
        files.append(path)

    annual = t['annual']
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(annual['Year'], annual['records'], color=BLUE, linewidth=2)
    ax.set(title=f'Recorded country-level disaster impacts | {window}',
           xlabel='Year', ylabel='Country-impact records', ylim=(0, None))
    ax.set_xticks([1970, 1980, 1990, 2000, 2010, 2020])
    ax.grid(axis='y', alpha=.18)
    save(fig, '01_annual_records', 'Records reflect reporting coverage as well as hazard occurrence; no causal attribution.')

    types = t['types'].sort_values('records')
    fig, ax = plt.subplots(figsize=(10, 6.7))
    ax.barh(types['Disaster Type'], types['records'], color=BLUE)
    ax.set(title=f'Disaster type mix | {window}', xlabel='Country-impact records')
    ax.bar_label(ax.containers[0], padding=4, fmt='%.0f', fontsize=9)
    ax.set_xlim(0, types['records'].max() * 1.15)
    save(fig, '02_disaster_types', 'Every record is counted, including unnamed events. Categories retain the legacy snapshot taxonomy.')

    quality = t['quality'].copy()
    quality['label'] = ['Deaths', 'Affected people', 'Economic loss', 'Start month']
    fig, ax = plt.subplots(figsize=(10, 4.7))
    ax.barh(quality['label'], quality['missing_pct'], color=ORANGE)
    ax.set(title=f'Missing data by field | {window}', xlabel='Missing share of country-impact records', xlim=(0, 100))
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.bar_label(ax.containers[0], labels=[f'{x:.1f}%' for x in quality['missing_pct']], padding=4)
    save(fig, '03_missingness', 'Unknown impacts are retained as missing values; missing does not mean zero.')

    curve, p = pareto(df)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    if len(curve):
        ax.plot(np.r_[0, curve['record_share_pct']], np.r_[0, curve['damage_share_pct']], color=BLUE, linewidth=2)
        ax.axhline(80, color='#555555', linestyle='--', linewidth=1)
        ax.axvline(p['top_share_pct'], color=ORANGE, linestyle=':', linewidth=1.5)
        ax.annotate(f"{p['top_records']:,} records ({p['top_share_pct']:.2f}%) → 80% of reported loss",
                    xy=(p['top_share_pct'], 80), xytext=(25, 52),
                    arrowprops={'arrowstyle': '->', 'color': '#555555'}, fontsize=10)
    ax.set(title=f'Concentration of reported economic loss | {window}',
           xlabel='Share of records with observed economic loss (ranked largest first)',
           ylabel='Cumulative share of reported loss', xlim=(0, 100), ylim=(0, 102))
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.yaxis.set_major_formatter(PercentFormatter())
    save(fig, '04_loss_concentration', f"Denominator: {p['observed_records']:,} records with loss data; missing-loss records are excluded. Nominal USD.")

    fig, axes = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True)
    axes[0].plot(annual['Year'], annual['reported_damage_thousand_usd'] / 1e6, color=BLUE, linewidth=2)
    axes[0].set(title=f'Reported economic loss and data coverage | {window}', ylabel='Reported loss (USD billions)', ylim=(0, None))
    axes[1].plot(annual['Year'], annual['damage_coverage_pct'], color=ORANGE, linewidth=2)
    axes[1].set(ylabel='Records with loss data', xlabel='Year', ylim=(0, 100))
    axes[1].yaxis.set_major_formatter(PercentFormatter())
    axes[1].set_xticks([1970, 1980, 1990, 2000, 2010, 2020])
    for ax in axes:
        ax.grid(axis='y', alpha=.18)
    save(fig, '05_loss_and_coverage', 'Nominal USD; no inflation or exposure adjustment. Missing losses are excluded, so totals are reported amounts only.')

    monthly = t['monthly']
    fig, ax = plt.subplots(figsize=(10, 4.7))
    ax.bar(monthly['month'], monthly['records'], color=BLUE)
    ax.set(title=f'Recorded impacts by calendar month | {window}', xlabel='Start month', ylabel='Country-impact records')
    ax.set_xticks(range(1, 13))
    save(fig, '06_calendar_month', f"{df['Start Month'].isna().sum():,} records without a valid start month excluded; no global season labels or date imputation.")

    matrix = t['type_continent']
    fig, ax = plt.subplots(figsize=(11, 7.2))
    image = ax.imshow(matrix, cmap='Blues', aspect='auto', vmin=0)
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title(f'Disaster type and continent | {window}')
    midpoint = matrix.to_numpy().max() * .55
    for (i, j), value in np.ndenumerate(matrix.to_numpy()):
        ax.text(j, i, f'{value:,}', ha='center', va='center', fontsize=9,
                color='white' if value > midpoint else '#222222')
    fig.colorbar(image, ax=ax, label='Country-impact records', shrink=.8)
    save(fig, '07_type_continent', 'Includes unnamed records. Zeros indicate no records in this snapshot, not proof of no hazard.')

    # A country ranking retains hover details without remote map topology.
    country = t['countries'].sort_values('records', ascending=False).head(20)
    top10 = country.head(10).sort_values('records')
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(top10['Country'], top10['records'], color=BLUE)
    ax.bar_label(ax.containers[0], padding=4, fmt='%.0f', fontsize=10)
    ax.set(title=f'Top 10 countries by recorded impacts | {window}', xlabel='Country-impact records')
    ax.set_xlim(0, top10['records'].max() * 1.15)
    save(fig, '08_country_records', 'Absolute counts; not adjusted for population, land area, exposure or reporting coverage.')
    fig = px.bar(country.sort_values('records'), x='records', y='Country', orientation='h',
                 hover_data=['damage_coverage_pct', 'reported_damage_thousand_usd'],
                 title=f'Top 20 countries by recorded disaster impacts | {window}',
                 labels={'records': 'Country-impact records', 'damage_coverage_pct': 'Loss coverage (%)',
                         'reported_damage_thousand_usd': 'Reported loss (USD thousands)'})
    fig.update_traces(marker_color=BLUE)
    fig.update_layout(template='plotly_white', height=720, margin={'l': 140},
                      annotations=[dict(text='Country totals reflect reporting and exposure; they are not normalized risk rates.',
                                        x=0, y=-.13, xref='paper', yref='paper', showarrow=False)])
    fig.write_html(output / '08_country_explorer.html', include_plotlyjs=True, full_html=True,
                   div_id='country-impact-ranking')
    return files
