# Pilot Scheduling Tools

A multi-page Streamlit app for analyzing airline bid packet data.

## 📂 Pages

### 1. EDW Pairing Analyzer (app.py)
- Upload a **pairings PDF**.
- Outputs:
  - Trip length breakdown
  - EDW vs Day trip percentages
  - Weighted summaries
  - Charts (bar + pie)
- Downloads:
  - Excel with trip-level + summary data
  - PDF report with charts

### 2. ONT 757 Bid Packet Line Analyzer (pages/2_Bid_Line_Analyzer.py)
- Upload a **line bid packet PDF**.
- Parses each line for:
  - Credit Time (CT)
  - Block Time (BT)
  - Days Off (DO)
  - Duty Days (DD)
- Outputs:
  - Summary statistics (min, max, avg, median, std dev)
  - Buy-up vs Non Buy-up table
  - Charts of CT, BT, DO by line
- Downloads:
  - Excel report with all stats and raw line data

---

## 🚀 Running Locally
1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
