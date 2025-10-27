"""
pdf_generation/charts.py
Chart generation functions for PDF reports using Matplotlib.

Contains:
- Generic chart functions (bar, percentage bar, pie)
- EDW-specific charts (trip length, duty day stats, weighted methods)
- Bid line-specific charts (distributions, buy-up analysis)
"""

import tempfile
from typing import List, Dict, Optional
import math

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


# ============================================================================
# GENERIC CHART FUNCTIONS
# ============================================================================

def save_bar_chart(
    data: pd.DataFrame,
    title: str,
    category_key: str,
    value_key: str,
    xlabel: str,
    ylabel: str,
    color: str = '#3B82F6'
) -> Optional[str]:
    """
    Create and save a generic bar chart to temp file.

    Args:
        data: DataFrame with category and value columns
        title: Chart title
        category_key: Column name for x-axis categories
        value_key: Column name for y-axis values
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Bar color (hex string)

    Returns:
        Path to temp PNG file, or None if data is empty
    """
    if data.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))

    labels = data[category_key].astype(str).tolist()
    values = data[value_key].astype(float).tolist()

    bars = ax.bar(labels, values, color=color, alpha=0.8)

    ax.set_xlabel(xlabel, fontsize=11, weight='bold')
    ax.set_ylabel(ylabel, fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9
            )

    # Rotate x-axis labels if many categories
    if len(labels) > 6:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_percentage_bar_chart(
    data: pd.DataFrame,
    title: str,
    category_key: str,
    percent_key: str,
    xlabel: str,
    color: str = '#3B82F6'
) -> Optional[str]:
    """
    Create and save a percentage bar chart to temp file.

    Args:
        data: DataFrame with category and percentage columns
        title: Chart title
        category_key: Column name for x-axis categories
        percent_key: Column name for percentage values (can be "45.2%" or 45.2)
        xlabel: X-axis label
        color: Bar color (hex string)

    Returns:
        Path to temp PNG file, or None if data is empty
    """
    if data.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))

    labels = data[category_key].astype(str).tolist()
    # Extract percentage values (remove % sign if present and convert to float)
    percentages = [float(str(p).replace('%', '')) for p in data[percent_key].tolist()]

    bars = ax.bar(labels, percentages, color=color, alpha=0.8)

    ax.set_xlabel(xlabel, fontsize=11, weight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, max(percentages) * 1.15 if percentages else 100)  # Add 15% headroom
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add percentage labels on bars
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2., height,
                f'{pct:.1f}%',
                ha='center', va='bottom', fontsize=9, weight='bold'
            )

    # Rotate x-axis labels if many categories
    if len(labels) > 6:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_pie_chart(
    title: str,
    labels: List[str],
    values: List[int],
    colors_list: List[str]
) -> Optional[str]:
    """
    Create and save a pie chart to temp file.

    Args:
        title: Chart title
        labels: List of slice labels
        values: List of slice values
        colors_list: List of hex color strings for slices

    Returns:
        Path to temp PNG file, or None if values are empty
    """
    if not values or sum(values) == 0:
        return None

    # Large square figure for long labels
    fig, ax = plt.subplots(figsize=(7, 7), dpi=100)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        labeldistance=1.12  # Move labels outward for long text
    )

    # Style text
    for text in texts:
        text.set_fontsize(9)
        text.set_weight('bold')
    for autotext in autotexts:
        autotext.set_color('#1F2937')  # Dark gray for visibility
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.axis('equal')  # Ensure perfect circle

    # Wide margins to accommodate long labels
    plt.subplots_adjust(left=0.22, right=0.78, top=0.78, bottom=0.22)

    # Save to temp file with fixed bbox to maintain square aspect ratio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Keep square shape
    plt.close(fig)

    return temp_file.name


# ============================================================================
# EDW-SPECIFIC CHART FUNCTIONS
# ============================================================================

def save_edw_pie_chart(edw_trips: int, non_edw_trips: int) -> str:
    """
    Create and save EDW vs Non-EDW pie chart to temp file.

    Args:
        edw_trips: Number of EDW trips
        non_edw_trips: Number of non-EDW trips

    Returns:
        Path to temp PNG file
    """
    # Large square figure for perfect circles with room for labels
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)

    labels = ['EDW', 'Non-EDW']
    sizes = [edw_trips, non_edw_trips]
    # Brand colors: Teal for EDW (accent/highlight), Sky for Non-EDW (supporting)
    colors_list = ['#1BB3A4', '#2E9BE8']

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        labeldistance=1.05  # Move labels slightly outward to prevent cutoff
    )

    # Style text with brand navy
    for text in texts:
        text.set_fontsize(11)
        text.set_weight('bold')
        text.set_color('#0C1E36')  # Brand navy for labels
    for autotext in autotexts:
        autotext.set_color('white')  # White percentage text for visibility
        autotext.set_fontsize(11)
        autotext.set_weight('bold')

    # Title with fixed position
    ax.set_title('EDW vs Non-EDW Trips', fontsize=12, weight='bold', pad=10, color='#0C1E36')
    ax.axis('equal')  # Ensure perfect circle

    # Adjust subplot to ensure labels fit within square canvas
    plt.subplots_adjust(left=0.15, right=0.85, top=0.82, bottom=0.15)

    # Save to temp file with fixed bbox to maintain square aspect ratio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Keep square shape
    plt.close(fig)

    return temp_file.name


def save_trip_length_bar_chart(
    trip_length_distribution: List[Dict[str, int]],
    title: str = "Trip Length Distribution"
) -> str:
    """
    Create and save trip length distribution bar chart to temp file.

    Args:
        trip_length_distribution: List of dicts with 'duty_days' and 'trips' keys
        title: Chart title

    Returns:
        Path to temp PNG file
    """
    fig, ax = plt.subplots(figsize=(5, 4))

    duty_days = [str(item["duty_days"]) for item in trip_length_distribution]
    trips = [item["trips"] for item in trip_length_distribution]

    # Use brand teal for primary data visualization
    bars = ax.bar(duty_days, trips, color='#1BB3A4', alpha=0.9)

    ax.set_xlabel('Duty Days', fontsize=11, weight='bold')
    ax.set_ylabel('Number of Trips', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=9
        )

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_trip_length_percentage_bar_chart(
    trip_length_distribution: List[Dict[str, int]],
    title: str = "Trip Length Distribution (%)"
) -> str:
    """
    Create and save trip length percentage bar chart to temp file.

    Args:
        trip_length_distribution: List of dicts with 'duty_days' and 'trips' keys
        title: Chart title

    Returns:
        Path to temp PNG file
    """
    fig, ax = plt.subplots(figsize=(5, 4))

    duty_days = [str(item["duty_days"]) for item in trip_length_distribution]
    trips = [item["trips"] for item in trip_length_distribution]

    # Calculate percentages
    total_trips = sum(trips)
    percentages = [(t / total_trips * 100) if total_trips > 0 else 0 for t in trips]

    # Use brand sky for percentage bars (lighter/supporting accent)
    bars = ax.bar(duty_days, percentages, color='#2E9BE8', alpha=0.9)

    ax.set_xlabel('Duty Days', fontsize=11, weight='bold')
    ax.set_ylabel('Percentage of Trips (%)', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, max(percentages) * 1.15 if percentages else 100)  # Add 15% headroom
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add percentage labels on bars
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{pct:.1f}%',
            ha='center', va='bottom', fontsize=9, weight='bold'
        )

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_edw_percentages_comparison_chart(weighted_summary: Dict[str, str]) -> str:
    """
    Create and save EDW percentages comparison bar chart to temp file.

    Args:
        weighted_summary: Dict with keys like "Trip-weighted EDW trip %"

    Returns:
        Path to temp PNG file
    """
    fig, ax = plt.subplots(figsize=(6, 4))

    # Extract percentages (remove % sign and convert to float)
    methods = ['Trip-Weighted', 'TAFB-Weighted', 'Duty Day-Weighted']
    percentages = []

    for key in ["Trip-weighted EDW trip %", "TAFB-weighted EDW trip %", "Duty-day-weighted EDW trip %"]:
        value_str = weighted_summary.get(key, "0%")
        # Handle both "46.4%" and "46.4" formats
        value_str = value_str.replace('%', '').strip()
        try:
            percentages.append(float(value_str))
        except ValueError:
            percentages.append(0.0)

    # Use brand palette: Teal, Sky, and darker teal/navy blend for variety
    colors_list = ['#1BB3A4', '#2E9BE8', '#0C7C73']
    bars = ax.bar(methods, percentages, color=colors_list, alpha=0.9)

    ax.set_ylabel('EDW Percentage (%)', fontsize=11, weight='bold')
    ax.set_title('EDW Percentages by Weighting Method', fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}%',
            ha='center', va='bottom', fontsize=10, weight='bold'
        )

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_weighted_method_pie_chart(
    edw_pct: float,
    method_name: str,
    color_scheme: str = 'default'
) -> str:
    """
    Create and save weighted method pie chart to temp file.

    Args:
        edw_pct: EDW percentage (0-100)
        method_name: Method name for title
        color_scheme: Color scheme ('trip', 'tafb', 'duty', or 'default')

    Returns:
        Path to temp PNG file
    """
    # Large square figure for perfect circles with room for labels
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)

    labels = ['EDW', 'Non-EDW']
    sizes = [edw_pct, 100 - edw_pct]

    # Brand color schemes for different methods (EDW, Non-EDW)
    color_schemes = {
        'trip': ['#1BB3A4', '#2E9BE8'],      # Teal, Sky
        'tafb': ['#0C7C73', '#5BCFC2'],      # Dark Teal, Light Teal
        'duty': ['#2E9BE8', '#7EC8F6']       # Sky, Light Sky
    }
    # Default to brand teal and sky
    colors_list = color_schemes.get(color_scheme, ['#1BB3A4', '#2E9BE8'])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        labeldistance=1.05  # Move labels slightly outward to prevent cutoff
    )

    # Style text with brand navy
    for text in texts:
        text.set_fontsize(10)
        text.set_weight('bold')
        text.set_color('#0C1E36')  # Brand navy for labels
    for autotext in autotexts:
        autotext.set_color('white')  # White percentage text for visibility
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    # Title with fixed position to ensure consistent spacing
    ax.set_title(method_name, fontsize=11, weight='bold', pad=10)
    ax.axis('equal')  # Ensure perfect circle

    # Adjust subplot to ensure labels fit within square canvas
    plt.subplots_adjust(left=0.15, right=0.85, top=0.82, bottom=0.15)

    # Save to temp file with fixed bbox to maintain square aspect ratio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Keep square shape
    plt.close(fig)

    return temp_file.name


def save_duty_day_grouped_bar_chart(duty_day_stats: List[List[str]]) -> str:
    """
    Create and save grouped bar chart for duty day statistics.

    Args:
        duty_day_stats: 2D list with header row and data rows
                        Format: [["Metric", "All", "EDW", "Non-EDW"], ...]

    Returns:
        Path to temp PNG file
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Extract metrics and values from the table (skip header row)
    metrics = []
    all_values = []
    edw_values = []
    non_edw_values = []

    for row in duty_day_stats[1:]:  # Skip header
        metric = row[0]
        all_val = row[1]
        edw_val = row[2]
        non_edw_val = row[3]

        # Parse values (handle "X.XXh" or "X.XX h" format)
        def parse_value(val_str):
            val_str = val_str.replace(' h', '').replace('h', '').strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        metrics.append(metric)
        all_values.append(parse_value(all_val))
        edw_values.append(parse_value(edw_val))
        non_edw_values.append(parse_value(non_edw_val))

    # Set up bar positions
    x = np.arange(len(metrics))
    width = 0.25

    # Create bars with brand colors
    bars1 = ax.bar(x - width, all_values, width, label='All Trips', color='#5B6168', alpha=0.9)  # Brand gray
    bars2 = ax.bar(x, edw_values, width, label='EDW Trips', color='#1BB3A4', alpha=0.9)  # Brand teal
    bars3 = ax.bar(x + width, non_edw_values, width, label='Non-EDW Trips', color='#2E9BE8', alpha=0.9)  # Brand sky

    # Customize chart
    ax.set_ylabel('Value', fontsize=11, weight='bold')
    ax.set_title('Duty Day Statistics Comparison', fontsize=12, weight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=9, rotation=15, ha='right')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=7)

    add_labels(bars1)
    add_labels(bars2)
    add_labels(bars3)

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def save_duty_day_radar_chart(duty_day_stats: List[List[str]]) -> str:
    """
    Create and save radar/spider chart for duty day statistics.

    Args:
        duty_day_stats: 2D list with header row and data rows
                        Format: [["Metric", "All", "EDW", "Non-EDW"], ...]

    Returns:
        Path to temp PNG file
    """
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(projection='polar'))

    # Extract metrics and values
    metrics = []
    edw_values = []
    non_edw_values = []

    for row in duty_day_stats[1:]:  # Skip header
        metric = row[0]
        edw_val = row[2]
        non_edw_val = row[3]

        # Parse values (handle "X.XXh" or "X.XX h" format)
        def parse_value(val_str):
            val_str = val_str.replace(' h', '').replace('h', '').strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        metrics.append(metric.replace('Avg ', ''))
        edw_values.append(parse_value(edw_val))
        non_edw_values.append(parse_value(non_edw_val))

    # Normalize values to 0-10 scale for better visualization
    max_vals = [max(edw_values[i], non_edw_values[i]) for i in range(len(edw_values))]
    edw_normalized = [(edw_values[i] / max_vals[i] * 10) if max_vals[i] > 0 else 0 for i in range(len(edw_values))]
    non_edw_normalized = [(non_edw_values[i] / max_vals[i] * 10) if max_vals[i] > 0 else 0 for i in range(len(non_edw_values))]

    # Number of variables
    num_vars = len(metrics)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Complete the circle
    edw_normalized += edw_normalized[:1]
    non_edw_normalized += non_edw_normalized[:1]
    angles += angles[:1]

    # Plot data with brand colors
    ax.plot(angles, edw_normalized, 'o-', linewidth=2, label='EDW Trips', color='#1BB3A4', alpha=0.8)  # Brand teal
    ax.fill(angles, edw_normalized, alpha=0.2, color='#1BB3A4')

    ax.plot(angles, non_edw_normalized, 'o-', linewidth=2, label='Non-EDW Trips', color='#2E9BE8', alpha=0.8)  # Brand sky
    ax.fill(angles, non_edw_normalized, alpha=0.2, color='#2E9BE8')

    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2.5, 5, 7.5, 10])
    ax.set_yticklabels(['', '', '', ''], fontsize=7)
    ax.grid(True, alpha=0.3)

    # Add legend and title
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=9)
    ax.set_title('EDW vs Non-EDW Profile', fontsize=12, weight='bold', pad=20)

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name
