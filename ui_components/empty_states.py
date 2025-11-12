"""
Empty State Components

Provides branded empty state messages with clear user guidance
for various no-data scenarios throughout the application.
"""

from typing import List, Dict, Any, Optional
import streamlit as st


def render_empty_state(
    state_type: str,
    icon: str = "📊",
    title: str = "No Data Yet",
    message: str = "",
    actions: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Render branded empty state with clear guidance.

    Creates a visually appealing empty state message with consistent
    branding, clear messaging, and optional call-to-action buttons.

    Args:
        state_type: Type of empty state
            - 'no_upload': No file uploaded yet
            - 'no_results': Query returned no results
            - 'no_data': No data available
            - 'error': Error state
        icon: Emoji or icon to display (default: 📊)
        title: Primary message headline
        message: Secondary descriptive message
        actions: Optional list of action buttons, each dict with:
            - 'label': Button text
            - 'callback': Function to call on click
            - 'type': Optional button type ('primary' or 'secondary')

    Example:
        >>> render_empty_state(
        ...     state_type='no_upload',
        ...     icon='📄',
        ...     title='Upload a PDF to Get Started',
        ...     message='Select a pairing PDF to begin analysis'
        ... )
    """
    # Style the empty state container with brand colors
    st.markdown(
        f"""
        <div style='
            text-align: center;
            padding: 60px 20px;
            background-color: #F8FAFC;
            border-radius: 10px;
            border: 2px dashed #E5E7EB;
            margin: 40px 0;
        '>
            <div style='font-size: 64px; margin-bottom: 20px;'>{icon}</div>
            <h3 style='
                color: #0C1E36;
                margin-bottom: 10px;
                font-weight: 600;
            '>{title}</h3>
            <p style='
                color: #5B6168;
                margin-bottom: 20px;
                font-size: 16px;
                line-height: 1.5;
            '>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render action buttons if provided
    if actions and len(actions) > 0:
        cols = st.columns(len(actions))
        for i, action in enumerate(actions):
            with cols[i]:
                btn_type = action.get("type", "primary")
                if st.button(action["label"], type=btn_type, key=f"empty_state_action_{i}"):
                    if action.get("callback"):
                        action["callback"]()


def render_no_upload_state(
    upload_type: str = "PDF",
    file_description: str = "pairing or bid line PDF",
) -> None:
    """
    Render empty state for file upload scenario.

    Args:
        upload_type: Type of file to upload (e.g., "PDF", "CSV")
        file_description: Description of expected file content
    """
    render_empty_state(
        state_type="no_upload",
        icon="📄",
        title=f"Upload a {upload_type} to Get Started",
        message=f"Select a {file_description} from your computer to begin analysis",
    )


def render_no_results_state(
    context: str = "",
    suggestions: Optional[List[str]] = None,
) -> None:
    """
    Render empty state for no query results scenario.

    Args:
        context: Context for why no results (e.g., "for the selected filters")
        suggestions: List of suggestions to try
    """
    suggestions_text = ""
    if suggestions:
        suggestions_text = "<br>".join([f"• {s}" for s in suggestions])
        suggestions_text = f"<div style='margin-top: 20px; text-align: left; display: inline-block;'><strong>Try:</strong><br>{suggestions_text}</div>"

    message = f"No results found {context}.{suggestions_text}" if suggestions else f"No results found {context}."

    render_empty_state(
        state_type="no_results",
        icon="🔍",
        title="No Results Found",
        message=message,
    )


def render_no_data_state(
    data_type: str = "data",
    reason: str = "",
) -> None:
    """
    Render empty state for no data available scenario.

    Args:
        data_type: Type of data that's missing (e.g., "pairings", "bid lines")
        reason: Optional reason why no data is available
    """
    message = f"No {data_type} available"
    if reason:
        message += f" - {reason}"

    render_empty_state(
        state_type="no_data",
        icon="📊",
        title="No Data Available",
        message=message,
    )


def render_error_state(
    error_title: str = "Something Went Wrong",
    error_message: str = "",
    show_details: bool = False,
    details: str = "",
) -> None:
    """
    Render empty state for error scenario.

    Args:
        error_title: Error headline
        error_message: User-friendly error description
        show_details: Whether to show technical details
        details: Technical error details (shown in expander)
    """
    render_empty_state(
        state_type="error",
        icon="⚠️",
        title=error_title,
        message=error_message,
    )

    if show_details and details:
        with st.expander("🔍 Technical Details"):
            st.code(details, language="text")


def render_loading_state(
    message: str = "Loading data...",
    show_spinner: bool = True,
) -> None:
    """
    Render loading state with spinner.

    Args:
        message: Loading message to display
        show_spinner: Whether to show animated spinner
    """
    if show_spinner:
        with st.spinner(message):
            # Spinner is shown by context manager
            pass
    else:
        st.info(f"⏳ {message}")
