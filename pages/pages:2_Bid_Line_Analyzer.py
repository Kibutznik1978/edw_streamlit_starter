import re
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import pdfplumber
from io import BytesIO

st.title("ONT 757 Bid Packet Line Analyzer")

uploaded_file = st.file_uploader("Upload bid packet PDF", type=["pdf"])

def parse_lines(text: str):
    pattern = r"ONT\s+(\d+)\s+CT:\s(\d+):(\d+)\s+BT:\s(\d+):(\d+)\s+DO:\s(\d+)\s+DD:\s(\d+)"
    matches = re.findall(pattern, text)

    data = []
    for m in matches:
        line = int(m[0])
        ct = int(m[1]) + int(m[2]) / 60
        bt = int(m[3]) + int(m[4]) / 60
        do = int(m[5])
        dd = int(m[6])
        data.append({"Line": line, "CT": ct, "BT": bt, "DO": do, "DD": dd})
    return pd.DataFrame(data)

if uploaded_file:
    # Extract text from PDF
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    df = parse_lines(text)

    if df.empty:
        st.error("⚠️ Could not find line data in this PDF. Check formatting.")
    else:
        # Summary stats
        buy_up_lines = df[df["CT"] < 75].shape[0]
        summary = {
            "Metric": ["Credit Hours (CT)", "Block Hours (BT)", "Days Off (DO)"],
            "Min": [round(df["CT"].min(),1), round(df["BT"].min(),1), round(df["DO"].min(),1)],
            "Max": [round(df["CT"].max(),1), round(df["BT"].max(),1), round(df["DO"].max(),1)],
            "Average": [round(df["CT"].mean(),1), round(df["BT"].mean(),1), round(df["DO"].mean(),1)],
            "Median": [round(df["CT"].median(),1), round(df["BT"].median(),1), round(df["DO"].median(),1)],
            "Std Dev": [round(df["CT"].std(),1), round(df["BT"].std(),1), round(df["DO"].std(),1)],
        }
        summary_df = pd.DataFrame(summary)

        # Buy-up table
        buyup_df = pd.DataFrame({
            "Category": ["Buy-up (<75 CT)", "Non Buy-up (≥75 CT)"],
            "Count": [buy_up_lines, len(df) - buy_up_lines],
            "Percent": [round(buy_up_lines/len(df)*100,1), round((len(df)-buy_up_lines)/len(df)*100,1)]
        })

        # Display
        st.subheader("📊 Summary Statistics")
        st.dataframe(summary_df)

        st.subheader("📌 Buy-up vs Non Buy-up")
        st.dataframe(buyup_df)

        # Charts
        st.subheader("📈 Charts")
        st.bar_chart(df.set_index("Line")["CT"])
        st.bar_chart(df.set_index("Line")["BT"])
        st.bar_chart(df.set_index("Line")["DO"])

        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary_df.to_excel(writer, sheet_name="Summary Stats", index=False)
            buyup_df.to_excel(writer, sheet_name="Buy-up vs Non Buy-up", index=False)
            df.to_excel(writer, sheet_name="Line Data", index=False)

        st.download_button(
            label="📥 Download Full Excel Report",
            data=output.getvalue(),
            file_name="Bid_Packet_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
