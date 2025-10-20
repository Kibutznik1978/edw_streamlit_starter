"""Generate PDF reports for bid line analysis."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Iterable, Optional

import math
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    from fpdf import FPDF  # type: ignore
except ImportError:  # pragma: no cover - tested via integration
    FPDF = None


@dataclass
class ReportMetadata:
    title: str = "Bid Line Analysis"
    subtitle: Optional[str] = None
    filters: Optional[Dict[str, Iterable]] = None


def build_analysis_pdf(df: pd.DataFrame, metadata: Optional[ReportMetadata] = None, pay_periods: Optional[pd.DataFrame] = None, reserve_lines: Optional[pd.DataFrame] = None) -> bytes:
    """Create a simple PDF summary for the provided bid line DataFrame."""

    if df.empty:
        raise ValueError("Cannot render PDF for empty dataset.")

    if FPDF is None:
        raise RuntimeError("Missing optional dependency 'fpdf'. Install it with 'pip install fpdf2'.")
    if plt is None:
        raise RuntimeError("Missing optional dependency 'matplotlib'. Install it with 'pip install matplotlib'.")

    metadata = metadata or ReportMetadata()
    pdf = FPDF(unit="pt", format="letter")
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()

    _add_title(pdf, metadata)
    _add_summary_table(pdf, df)

    # Add pay period averages if available
    if pay_periods is not None and not pay_periods.empty:
        _add_pay_period_averages(pdf, df, pay_periods)

    # Add reserve line statistics if available
    if reserve_lines is not None and not reserve_lines.empty:
        _add_reserve_statistics(pdf, df, reserve_lines)

    _add_distribution_tables(pdf, df)
    _add_distribution_charts(pdf, df)
    _add_buy_up_table(pdf, df)
    _add_buy_up_chart(pdf, df)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def _add_title(pdf: FPDF, metadata: ReportMetadata) -> None:
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 24, metadata.title, ln=1)
    if metadata.subtitle:
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 16, metadata.subtitle, ln=1)

    if metadata.filters:
        pdf.set_font("Helvetica", size=10)
        for label, values in metadata.filters.items():
            if isinstance(values, (list, tuple, set)):
                rendered = ', '.join(map(str, values))
            else:
                rendered = str(values)
            pdf.cell(0, 14, f'{label}: {rendered}', ln=1)
    pdf.ln(10)


def _add_summary_table(pdf: FPDF, df: pd.DataFrame) -> None:
    summary = df[["CT", "BT", "DO", "DD"]].agg(["min", "max", "mean", "median", "std"]).transpose()
    summary.rename(columns={"min": "Min", "max": "Max", "mean": "Average", "median": "Median", "std": "Std Dev"}, inplace=True)
    summary.index.name = "Metric"
    summary.reset_index(inplace=True)

    numeric_cols = ["Min", "Max", "Average", "Median", "Std Dev"]
    for col in numeric_cols:
        summary[col] = summary[col].apply(lambda value: _format_number(value))

    _render_table(pdf, "Summary Statistics", summary)


def _add_pay_period_averages(pdf: FPDF, df: pd.DataFrame, pay_periods: pd.DataFrame) -> None:
    """Add per-pay-period averages table."""
    # Filter pay periods to only include lines in the filtered dataframe
    subset = pay_periods[pay_periods["Line"].isin(df["Line"])].copy()

    if subset.empty:
        return

    # Calculate averages per pay period
    period_metrics = subset.groupby("Period")[["CT", "BT", "DO", "DD"]].mean().round(2)

    if period_metrics.empty:
        return

    # Format the table
    period_metrics.reset_index(inplace=True)
    period_metrics["Period"] = period_metrics["Period"].apply(lambda p: f"PP{int(p)}")
    period_metrics.rename(columns={
        "Period": "Pay Period",
        "CT": "Avg CT",
        "BT": "Avg BT",
        "DO": "Avg DO",
        "DD": "Avg DD"
    }, inplace=True)

    # Add aggregate row
    overall = subset[["CT", "BT", "DO", "DD"]].mean().round(2)
    aggregate_row = pd.DataFrame([{
        "Pay Period": "Overall",
        "Avg CT": overall["CT"],
        "Avg BT": overall["BT"],
        "Avg DO": overall["DO"],
        "Avg DD": overall["DD"]
    }])

    period_table = pd.concat([period_metrics, aggregate_row], ignore_index=True)

    # Format numeric columns
    for col in ["Avg CT", "Avg BT", "Avg DO", "Avg DD"]:
        period_table[col] = period_table[col].apply(lambda value: _format_number(value))

    _render_table(pdf, "Pay Period Averages", period_table)


def _add_reserve_statistics(pdf: FPDF, df: pd.DataFrame, reserve_lines: pd.DataFrame) -> None:
    """Add reserve line statistics table."""
    # Filter reserve lines to only include lines in the filtered dataframe
    reserve_subset = reserve_lines[reserve_lines["Line"].isin(df["Line"])].copy()
    reserve_subset = reserve_subset[reserve_subset["IsReserve"] == True]

    if reserve_subset.empty:
        return

    total_reserve = len(reserve_subset)
    captain_slots = int(reserve_subset["CaptainSlots"].sum())
    fo_slots = int(reserve_subset["FOSlots"].sum())
    total_slots = captain_slots + fo_slots

    # Total regular lines (non-reserve)
    total_regular = len(df) - total_reserve

    # Calculate percentage
    if total_regular > 0:
        reserve_percentage = (total_slots / total_regular) * 100
    else:
        reserve_percentage = 0.0

    # Create table
    stats_table = pd.DataFrame([
        {"Metric": "Total Reserve Lines", "Value": str(total_reserve)},
        {"Metric": "Captain Slots", "Value": str(captain_slots)},
        {"Metric": "First Officer Slots", "Value": str(fo_slots)},
        {"Metric": "Total Reserve Slots", "Value": str(total_slots)},
        {"Metric": "Regular Lines", "Value": str(total_regular)},
        {"Metric": "Reserve Percentage", "Value": f"{reserve_percentage:.1f}%"},
    ])

    _render_table(pdf, "Reserve Lines Analysis", stats_table)


def _add_distribution_tables(pdf: FPDF, df: pd.DataFrame) -> None:
    ct_distribution = _create_binned_distribution(df['CT'], bin_width=5.0, label='Range')
    _render_table(pdf, 'CT Distribution (5-hour buckets)', ct_distribution)

    bt_distribution = _create_binned_distribution(df['BT'], bin_width=5.0, label='Range')
    _render_table(pdf, 'BT Distribution (5-hour buckets)', bt_distribution)

    do_distribution = _create_value_distribution(df['DO'], label='Days Off')
    _render_table(pdf, 'Days Off Distribution', do_distribution)

def _add_distribution_charts(pdf: FPDF, df: pd.DataFrame) -> None:
    ct_distribution = _create_binned_distribution(df['CT'], bin_width=5.0, label='Range')
    _render_bar_chart(pdf, 'CT Distribution', ct_distribution, category_key='Range', value_key='Lines', xlabel='Credit Range', ylabel='Lines')

    bt_distribution = _create_binned_distribution(df['BT'], bin_width=5.0, label='Range')
    _render_bar_chart(pdf, 'BT Distribution', bt_distribution, category_key='Range', value_key='Lines', xlabel='Block Range', ylabel='Lines')

    do_distribution = _create_value_distribution(df['DO'], label='Days Off')
    _render_bar_chart(pdf, 'Days Off Distribution', do_distribution, category_key='Days Off', value_key='Lines', xlabel='Days Off', ylabel='Lines')



def _add_buy_up_table(pdf: FPDF, df: pd.DataFrame, threshold: float = 75.0) -> None:
    total = len(df)
    groups = [
        (f'Buy-up (<{threshold:.0f} CT)', df[df['CT'] < threshold]),
        (f'Non Buy-up (>={threshold:.0f} CT)', df[df['CT'] >= threshold]),
    ]

    rows = []
    for label, subset in groups:
        count = len(subset)
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append(
            {
                'Category': label,
                'Lines': count,
                'Percent': percent,
                'Avg CT': _format_number(subset['CT'].mean()),
                'Avg BT': _format_number(subset['BT'].mean()),
                'Avg DO': _format_number(subset['DO'].mean()),
                'Avg DD': _format_number(subset['DD'].mean()),
            }
        )

    table = pd.DataFrame(rows)
    _render_table(pdf, f'Buy-up vs Non Buy-up (threshold {threshold:.0f} CT)', table)

def _add_buy_up_chart(pdf: FPDF, df: pd.DataFrame, threshold: float = 75.0) -> None:
    total = len(df)
    if total == 0:
        return

    labels = [f'Buy-up (<{threshold:.0f} CT)', f'Non Buy-up (>={threshold:.0f} CT)']
    counts = [int((df['CT'] < threshold).sum()), int((df['CT'] >= threshold).sum())]

    _render_pie_chart(pdf, 'Buy-up vs Non Buy-up', labels, counts)



def _format_number(value: float, decimals: int = 2) -> str:
    return 'N/A' if pd.isna(value) else f"{value:.{decimals}f}"

def _render_bar_chart(
    pdf: FPDF,
    title: str,
    data: pd.DataFrame,
    *,
    category_key: str,
    value_key: str,
    xlabel: str,
    ylabel: str,
) -> None:
    if data.empty:
        return

    labels = data[category_key].astype(str).tolist()
    values = data[value_key].astype(float).tolist()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(labels, values, color='#2A9D8F')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='PNG', bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)

    available_width = pdf.w - 2 * pdf.l_margin
    pdf.image(buffer, w=min(available_width, 400))
    pdf.ln(10)


def _render_pie_chart(pdf: FPDF, title: str, labels: list[str], values: list[int]) -> None:
    if not values or sum(values) == 0:
        return

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#F4A261', '#264653'])
    ax.set_title(title)
    ax.axis('equal')
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format='PNG', bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)

    available_width = pdf.w - 2 * pdf.l_margin
    pdf.image(buffer, w=min(available_width, 320))
    pdf.ln(10)



def _render_table(pdf: FPDF, title: str, data: pd.DataFrame) -> None:
    if data.empty:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 16, f"{title}: No data", ln=1)
        pdf.ln(8)
        return

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 16, title, ln=1)
    pdf.set_font('Helvetica', 'B', 10)

    columns = list(data.columns)
    table = data.copy()
    for column in columns:
        table[column] = table[column].astype(str)
    col_widths = _compute_column_widths(pdf, columns, table)

    for col, width in zip(columns, col_widths):
        pdf.cell(width, 16, col, border=1)
    pdf.ln(16)

    pdf.set_font('Helvetica', size=10)
    for _, row in table.iterrows():
        for col, width in zip(columns, col_widths):
            pdf.cell(width, 16, str(row[col]), border=1)
        pdf.ln(16)
    pdf.ln(8)


def _create_binned_distribution(series: pd.Series, bin_width: float, label: str) -> pd.DataFrame:
    if series.empty:
        return pd.DataFrame(columns=[label, 'Lines', 'Percent'])

    minimum = float(series.min())
    maximum = float(series.max())
    if bin_width <= 0:
        bin_width = max((maximum - minimum) / 5, 1) or 1

    start = math.floor(minimum / bin_width) * bin_width
    end = math.ceil(maximum / bin_width) * bin_width
    if end <= start:
        end = start + bin_width

    edges = [start]
    while edges[-1] < end:
        edges.append(edges[-1] + bin_width)
    if edges[-1] < maximum + 1e-6:
        edges.append(edges[-1] + bin_width)

    bins = pd.cut(series, bins=edges, include_lowest=True, right=False)
    counts = bins.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for interval, count in counts.items():
        left = interval.left
        right = interval.right
        label_text = f"{left:.1f}-{right:.1f}" if bin_width < 1 else f"{left:.0f}-{right:.0f}"
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: label_text, 'Lines': int(count), 'Percent': percent})

    return pd.DataFrame(rows)


def _create_value_distribution(series: pd.Series, label: str) -> pd.DataFrame:
    if series.empty:
        return pd.DataFrame(columns=[label, 'Lines', 'Percent'])

    # Convert to integers for day counts (DO/DD should be whole days only)
    series_int = series.astype(int)
    counts = series_int.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for value, count in counts.items():
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: int(value), 'Lines': int(count), 'Percent': percent})

    return pd.DataFrame(rows)



def _compute_column_widths(pdf: FPDF, columns: Iterable[str], data: pd.DataFrame) -> list:
    padding = 12
    widths = []
    for col in columns:
        max_text = max([col] + data[col].astype(str).tolist(), key=len)
        width = pdf.get_string_width(max_text) + padding
        widths.append(width)
    return widths
