"""
Dashboard Page 1: Feed Báo cáo
Hiển thị danh sách báo cáo phân tích theo ngày + bảng alert động.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="Feed Báo cáo | VN Market Intel", layout="wide")
st.title("📰 Feed Báo cáo Thị trường")

# ── Chọn ngày ──────────────────────────────────────────────────────────────────
selected_date = st.date_input("Chọn ngày giao dịch", value=date.today())
date_str = str(selected_date)

col_main, col_alert = st.columns([2, 1])

# ── Cột trái: Báo cáo ngày ─────────────────────────────────────────────────────
with col_main:
    st.subheader(f"Báo cáo thị trường (tổng quan) — {date_str}")

    # Feed: tóm tắt — file market_report_{date}.md (khác với phân tích chi tiết)
    report_md  = Path(f"reports/{date_str}/market_report_{date_str}.md")
    report_pdf = Path(f"reports/{date_str}/market_report_{date_str}.pdf")

    if report_md.exists():
        st.markdown(report_md.read_text(encoding="utf-8"))
        st.caption(
            "Trang **Báo cáo phân tích chi tiết** đọc file `market_report_detail_{ngày}.md` (nội dung sâu hơn)."
        )
        if report_pdf.exists():
            st.markdown("---")
            if st.button("📄 Xem báo cáo PDF đầy đủ"):
                st.switch_page("pages/02_article.py")
    else:
        st.info(f"Chưa có báo cáo cho ngày {date_str}. Pipeline chạy lúc 15:15 ICT.")

        # Hiển thị danh sách báo cáo gần đây
        st.subheader("Báo cáo gần đây")
        for i in range(1, 8):
            past_date = str(date.today() - timedelta(days=i))
            past_md = Path(f"reports/{past_date}/market_report_{past_date}.md")
            if past_md.exists():
                if st.button(f"📰 {past_date}", key=f"btn_{past_date}"):
                    st.session_state["selected_date"] = past_date
                    st.rerun()

# ── Cột phải: Bảng Alert ───────────────────────────────────────────────────────
with col_alert:
    st.subheader("🔔 Thông báo Biến động")

    alert_file = Path(f"storage/alerts_{date_str}.json")
    if alert_file.exists():
        alerts = json.loads(alert_file.read_text(encoding="utf-8"))
        if alerts:
            for alert in sorted(alerts, key=lambda x: abs(x.get("change_pct", 0)), reverse=True):
                level = alert.get("level", "INFO")
                icon  = alert.get("icon", "🔵")
                change = alert.get("change_pct", 0)

                if level == "HIGH":
                    st.error(f"{icon} **{alert['ticker']}** {change:+.1f}%\n\n{alert.get('body', '')}")
                elif level == "MEDIUM":
                    st.warning(f"{icon} **{alert['ticker']}** {change:+.1f}%\n\n{alert.get('body', '')}")
                else:
                    st.info(f"{icon} **{alert['ticker']}** {change:+.1f}%\n\n{alert.get('body', '')}")
        else:
            st.success("Không có biến động lớn hôm nay.")
    else:
        st.caption("Chưa có dữ liệu alert.")
