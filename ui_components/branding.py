"""
Branded UI components for consistent brand identity across the application.

This module provides branded headers, styling, and visual elements that
reinforce the Aero Crew Data brand identity throughout the user interface.
"""

from pathlib import Path
import streamlit as st


def render_app_header():
    """
    Render branded application header with logo and tagline.

    Displays the Aero Crew Data logo alongside the application title
    and descriptive tagline using brand colors and typography.
    """
    col1, col2 = st.columns([1.8, 3.2])

    with col1:
        # Display logo if available
        logo_path = Path("logo-full.svg")
        if logo_path.exists():
            st.image(str(logo_path), width=420)
        else:
            # Fallback to emoji if logo not found
            st.markdown("<div style='font-size: 180px; text-align: center;'>✈️</div>", unsafe_allow_html=True)

    with col2:
        # Branded header with custom styling
        st.markdown("""
        <div style='padding-top: 10px;'>
            <h1 style='margin-bottom: 0; color: #0C1E36; font-weight: 600;'>
                Pairing Analyzer Tool
            </h1>
            <p style='color: #5B6168; margin-top: 5px; font-size: 16px;'>
                Comprehensive scheduling analysis for airline pilots • Powered by Aero Crew Data
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = None, icon: str = "📊"):
    """
    Render a consistent section header with optional subtitle.

    Args:
        title: Main section title
        subtitle: Optional subtitle or description
        icon: Emoji icon to display (default: 📊)
    """
    st.markdown(f"""
    <div style='margin-bottom: 20px;'>
        <h2 style='color: #0C1E36; margin-bottom: 5px;'>
            {icon} {title}
        </h2>
        {f"<p style='color: #5B6168; margin-top: 0; font-size: 14px;'>{subtitle}</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def apply_brand_styling():
    """
    Apply global brand styling to the Streamlit application.

    This includes custom CSS for consistent colors, typography, and spacing
    that align with the Aero Crew Data brand identity.
    """
    st.markdown("""
    <style>
        /* Brand Color Variables */
        :root {
            --brand-primary: #0C1E36;    /* Navy */
            --brand-accent: #1BB3A4;     /* Teal */
            --brand-sky: #2E9BE8;        /* Sky Blue */
            --brand-gray: #5B6168;       /* Muted Gray */
            --brand-bg-alt: #F8FAFC;     /* Light Gray */
        }

        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid var(--brand-bg-alt);
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-top: 10px;
            padding-left: 20px;
            padding-right: 20px;
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            color: var(--brand-gray);
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--brand-bg-alt);
            color: var(--brand-primary);
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--brand-accent);
            color: white;
        }

        /* Primary Buttons */
        .stButton > button[kind="primary"] {
            background-color: var(--brand-accent);
            border: none;
            color: white;
            font-weight: 500;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #159A8C;
            border: none;
        }

        /* Metric Cards */
        [data-testid="stMetricValue"] {
            color: var(--brand-primary);
            font-weight: 600;
        }

        /* Dividers */
        hr {
            border-color: var(--brand-bg-alt);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--brand-bg-alt);
        }

        /* Info Boxes */
        .stAlert {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
