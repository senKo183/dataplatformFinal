"""
Dashboard Page 4: Lịch sử Phân tích
Biểu đồ giá + nguyên nhân biến động trong 30/60/90 ngày.
"""

import streamlit as st
import json
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="Lịch sử | VN Market Intel", layout="wide")
st.title("📈 Lịch sử Phân tích")

# ── Chọn mã và khoảng thời gian ────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("Mã cổ phiếu", value="VCB").upper()
with col2:
    period = st.selectbox("Khoảng thời gian", [30, 60, 90], format_func=lambda x: f"{x} ngày")

if not ticker:
    st.stop()

# ── Đọc dữ liệu từ SQLite ─────────────────────────────────────────────────────
db_path = "storage/history.sqlite"
if not Path(db_path).exists():
    st.warning("Chưa có dữ liệu lịch sử. Hãy chạy pipeline ít nhất 1 lần.")
    st.stop()

try:
    conn = sqlite3.connect(db_path)
    end_date   = date.today()
    start_date = end_date - timedelta(days=period)

    # Lấy lịch sử giá + nguyên nhân
    df = pd.read_sql_query("""
        SELECT date, close, change_pct, volume, cause, cause_label, confidence
        FROM daily_analysis
        WHERE ticker = ? AND date >= ? AND date <= ?
        ORDER BY date
    """, conn, params=[ticker, str(start_date), str(end_date)])
    conn.close()

    if df.empty:
        st.warning(f"Không có dữ liệu cho mã {ticker} trong {period} ngày qua.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"])

    # ── Biểu đồ giá + volume ──────────────────────────────────────────────────
    fig = go.Figure()

    # Candlestick (cần thêm open/high/low — placeholder dùng close)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["close"],
        mode="lines+markers",
        name=f"{ticker} — Giá đóng cửa",
        line=dict(color="#1f77b4", width=2),
        hovertemplate="%{x|%d/%m/%Y}<br>Giá: %{y:,.0f} VND<extra></extra>",
    ))

    # Tô màu điểm theo nguyên nhân
    cause_colors = {
        "KY_THUAT": "#ff7f0e",
        "TIN_TUC":  "#2ca02c",
        "CO_TUC":   "#9467bd",
        "THI_TRUONG": "#8c564b",
        "HON_HOP":  "#e377c2",
        "KHONG_XAC_DINH": "#7f7f7f",
    }

    for cause_code, color in cause_colors.items():
        subset = df[df["cause"] == cause_code]
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset["date"], y=subset["close"],
                mode="markers",
                name=subset["cause_label"].iloc[0] if "cause_label" in subset else cause_code,
                marker=dict(color=color, size=8, symbol="circle"),
            ))

    fig.update_layout(
        title=f"{ticker} — Giá đóng cửa {period} ngày qua",
        xaxis_title="Ngày",
        yaxis_title="Giá (VND)",
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Bảng lịch sử phân tích ─────────────────────────────────────────────────
    st.subheader("Chi tiết phân tích từng ngày")
    display_df = df[["date", "close", "change_pct", "cause_label", "confidence"]].copy()
    display_df["date"]       = display_df["date"].dt.strftime("%d/%m/%Y")
    display_df["close"]      = display_df["close"].apply(lambda x: f"{x:,.0f}")
    display_df["change_pct"] = display_df["change_pct"].apply(lambda x: f"{x:+.1f}%")
    display_df.columns = ["Ngày", "Giá đóng cửa", "Biến động", "Nguyên nhân chính", "Độ tin cậy"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Lỗi đọc dữ liệu: {e}")
