"""
Dashboard Page 3: Bảng Alert toàn bộ
Hiển thị tất cả thông báo biến động lớn với filter theo ngày và mức độ.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="Bảng Alert | VN Market Intel", layout="wide")
st.title("🔔 Bảng Thông báo Biến động")

# ── Filter ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    days_back = st.selectbox("Khoảng thời gian", [1, 7, 14, 30], index=1, format_func=lambda x: f"{x} ngày gần đây")
with col2:
    level_filter = st.multiselect("Mức độ", ["HIGH", "MEDIUM", "INFO"], default=["HIGH", "MEDIUM"])
with col3:
    ticker_filter = st.text_input("Lọc theo mã", placeholder="VCB, FPT, ...")

# ── Thu thập alerts từ nhiều ngày ──────────────────────────────────────────────
all_alerts = []
for i in range(days_back):
    d = str(date.today() - timedelta(days=i))
    alert_file = Path(f"storage/alerts_{d}.json")
    if alert_file.exists():
        try:
            alerts = json.loads(alert_file.read_text(encoding="utf-8"))
            for a in alerts:
                a["date"] = d
            all_alerts.extend(alerts)
        except Exception:
            pass

if not all_alerts:
    st.info("Không có dữ liệu alert trong khoảng thời gian đã chọn.")
    st.stop()

# ── Áp dụng filter ─────────────────────────────────────────────────────────────
df = pd.DataFrame(all_alerts)

if level_filter:
    df = df[df["level"].isin(level_filter)]

if ticker_filter:
    tickers = [t.strip().upper() for t in ticker_filter.split(",") if t.strip()]
    if tickers:
        df = df[df["ticker"].isin(tickers)]

df = df.sort_values(["date", "change_pct"], key=lambda x: x if x.dtype != object else x.str.upper(), ascending=[False, True])

# ── Hiển thị bảng ─────────────────────────────────────────────────────────────
st.markdown(f"**{len(df)} thông báo** trong {days_back} ngày gần đây")

for _, row in df.iterrows():
    icon   = row.get("icon", "🔵")
    level  = row.get("level", "INFO")
    change = row.get("change_pct", 0)
    ticker = row.get("ticker", "")
    body   = row.get("body", "")
    cause  = row.get("cause", "")
    d      = row.get("date", "")

    content = f"{icon} **{ticker}** {change:+.1f}% — {cause}  \n{body}  \n*{d}*"

    if level == "HIGH":
        st.error(content)
    elif level == "MEDIUM":
        st.warning(content)
    else:
        st.info(content)
