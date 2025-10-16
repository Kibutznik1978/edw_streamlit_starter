import tempfile
from pathlib import Path
import streamlit as st
from edw_reporter import run_edw_report

st.set_page_config(page_title="EDW Pairing Analyzer", layout="centered")
st.title("EDW Pairing Analyzer")

st.markdown(
    "Upload a formatted bid-pack PDF. I'll return an **Excel** workbook and a **3-page PDF** "
    "with the trip-length breakdown, EDW vs Day, and length-weighted explanation."
)

with st.expander("Labels (optional)"):
    dom = st.text_input("Domicile", value="ONT")
    ac  = st.text_input("Aircraft", value="757")
    bid = st.text_input("Bid period", value="2507")

uploaded = st.file_uploader("Pairings PDF", type=["pdf"])

# Initialize session state for results
if "results" not in st.session_state:
    st.session_state.results = None

run = st.button("Run Analysis", disabled=(uploaded is None))
if run:
    if uploaded is None:
        st.warning("Please upload a PDF first.")
        st.stop()

    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(progress, message):
        progress_bar.progress(progress / 100)
        status_text.text(message)

    tmpdir = Path(tempfile.mkdtemp())
    pdf_path = tmpdir / uploaded.name
    pdf_path.write_bytes(uploaded.getvalue())

    out_dir = tmpdir / "outputs"
    out_dir.mkdir(exist_ok=True)

    res = run_edw_report(
        pdf_path,
        out_dir,
        domicile=dom.strip() or "DOM",
        aircraft=ac.strip() or "AC",
        bid_period=bid.strip() or "0000",
        progress_callback=update_progress,
    )

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    # Store results in session state
    st.session_state.results = {
        "res": res,
        "out_dir": out_dir,
        "dom": dom,
        "ac": ac,
        "bid": bid,
    }

    st.success("Done! Download your files below:")

# Display download buttons and visualizations if results exist
if st.session_state.results is not None:
    result_data = st.session_state.results
    out_dir = result_data["out_dir"]
    res = result_data["res"]
    dom = result_data["dom"]
    ac = result_data["ac"]
    bid = result_data["bid"]

    # === SUMMARY SECTION ===
    st.header("📊 Analysis Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Trip Summary")
        st.dataframe(res["trip_summary"], hide_index=True, width="stretch")

    with col2:
        st.subheader("Weighted Summary")
        st.dataframe(res["weighted_summary"], hide_index=True, width="stretch")

    with col3:
        st.subheader("Hot Standby Summary")
        st.dataframe(res["hot_standby_summary"], hide_index=True, width="stretch")

    st.divider()

    # === CHARTS SECTION ===
    st.header("📈 Visualizations")

    # Duty Day Distribution
    st.subheader("Trip Length Distribution (excludes Hot Standby)")
    duty_dist = res["duty_dist"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Duty Days vs Trips**")
        st.bar_chart(duty_dist.set_index("Duty Days")["Trips"], x_label="Duty Days", y_label="Trips")
    with col2:
        st.markdown("**Duty Days vs Percentage**")
        st.bar_chart(duty_dist.set_index("Duty Days")["Percent"], x_label="Duty Days", y_label="Percent")

    st.divider()

    # === TRIP RECORDS PREVIEW ===
    st.header("🗂️ Trip Records")
    df_trips = res["df_trips"]

    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_edw = st.selectbox("Filter by EDW:", ["All", "EDW Only", "Day Only"])
    with col2:
        filter_hs = st.selectbox("Filter by Hot Standby:", ["All", "Hot Standby Only", "Exclude Hot Standby"])
    with col3:
        sort_by = st.selectbox("Sort by:", ["Trip ID", "Frequency", "TAFB Hours", "Duty Days"])

    # Apply filters
    filtered_df = df_trips.copy()
    if filter_edw == "EDW Only":
        filtered_df = filtered_df[filtered_df["EDW"] == True]
    elif filter_edw == "Day Only":
        filtered_df = filtered_df[filtered_df["EDW"] == False]

    if filter_hs == "Hot Standby Only":
        filtered_df = filtered_df[filtered_df["Hot Standby"] == True]
    elif filter_hs == "Exclude Hot Standby":
        filtered_df = filtered_df[filtered_df["Hot Standby"] == False]

    # Sort
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=False if sort_by in ["Frequency", "TAFB Hours", "Duty Days"] else True)

    st.dataframe(filtered_df, hide_index=True, width="stretch")
    st.caption(f"Showing {len(filtered_df)} of {len(df_trips)} pairings")

    st.divider()

    # === DOWNLOAD SECTION ===
    st.header("⬇️ Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        # Excel
        xlsx = out_dir / f"{dom}_{ac}_Bid{bid}_EDW_Report_Data.xlsx"
        st.download_button(
            "📊 Download Excel Workbook",
            data=xlsx.read_bytes(),
            file_name=xlsx.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel",
        )

    with col2:
        # Report PDF
        report_pdf = res["report_pdf"]
        st.download_button(
            "📄 Download PDF Report",
            data=report_pdf.read_bytes(),
            file_name=report_pdf.name,
            mime="application/pdf",
            key="download_pdf",
        )

    st.divider()
    st.caption("Raw CSV outputs (optional)")
    for fn in [
        "trip_level_edw_flags.csv",
        "trip_length_summary.csv",
        "edw_vs_day_summary.csv",
        "edw_by_length.csv",
        "edw_weighting_summary.csv",
        "edw_trip_ids.csv",
    ]:
        fp = out_dir / fn
        if fp.exists():
            st.download_button(
                f"Download {fn}",
                data=fp.read_bytes(),
                file_name=fp.name,
                mime="text/csv",
                key=f"download_{fn}",
            )

st.caption(
    "Notes: EDW = any duty day touches 02:30–05:00 local (inclusive). "
    "Local hour comes from the number in parentheses ( ), minutes from the following Z time."
)
