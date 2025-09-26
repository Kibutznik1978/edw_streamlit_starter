import streamlit as st
import pandas as pd
import pdfplumber
import re

st.title("Bid Line Analyzer")

uploaded_file = st.file_uploader("Upload a bid roster PDF", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Regex: captures Line ID, Credit, Block, Days Off, Duty Days
    LINE_RE = re.compile(
        r'^(?P<line_id>\d+)\s+'
        r'(?P<ct>\d{2,3}\.\d)\s+'
        r'(?P<bt>\d{2,3}\.\d)\s+'
        r'(?P<do>\d{1,2})\s+'
        r'(?P<dd>\d{1,2})'
    )

    records = []
    for raw_line in text.splitlines():
        m = LINE_RE.search(raw_line.strip())
        if m:
            records.append({
                "Line": int(m.group("line_id")),
                "CT": float(m.group("ct")),
                "BT": float(m.group("bt")),
                "DO": int(m.group("do")),
                "DD": int(m.group("dd")),
            })

    if not records:
        st.warning("⚠️ Could not find line data. Try exporting the PDF as Excel if issue persists.")
    else:
        df = pd.DataFrame(records)
        st.success(f"Parsed {len(df)} lines successfully!")
        st.dataframe(df)

        # Summary stats
        st.subheader("Summary")
        st.write(f"Total lines: {len(df)}")
        st.write(f"Average Credit: {df['CT'].mean():.1f}")
        st.write(f"Average Block: {df['BT'].mean():.1f}")
        st.write(f"Average Days Off: {df['DO'].mean():.1f}")
        st.write(f"Average Duty Days: {df['DD'].mean():.1f}")

        # Buy-up lines (credit < 75)
        buy_up = df[df["CT"] < 75]
        st.write(f"Buy-up lines (<75 CT): {len(buy_up)}")
        if not buy_up.empty:
            st.dataframe(buy_up)

