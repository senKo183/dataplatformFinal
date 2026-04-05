"""
Dashboard Page 2: Xem Bài báo + PDF Viewer inline
Hiển thị báo cáo phân tích dạng bài báo và nhúng PDF trực tiếp.
"""

import streamlit as st
import base64
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Xem Báo cáo | VN Market Intel", layout="wide")
st.title("📄 Báo cáo Phân tích Chi tiết")

# ── Chọn ngày ──────────────────────────────────────────────────────────────────
selected_date = st.date_input("Ngày báo cáo", value=date.today())
date_str = str(selected_date)

# Báo cáo chi tiết: file riêng (sinh bởi demo_midterm / pipeline Agent 4 sau này)
report_md  = Path(f"reports/{date_str}/market_report_detail_{date_str}.md")
report_pdf = Path(f"reports/{date_str}/market_report_detail_{date_str}.pdf")

if not report_md.exists():
    st.warning(
        f"Chưa có báo cáo phân tích chi tiết cho ngày {date_str}. "
        f"Chạy `python scripts/demo_midterm.py` hoặc pipeline đầy đủ."
    )
    st.stop()

# ── Nội dung bài báo ──────────────────────────────────────────────────────────
st.markdown(report_md.read_text(encoding="utf-8"))

# ── PDF Viewer inline ─────────────────────────────────────────────────────────
if report_pdf.exists():
    st.markdown("---")
    st.subheader("📄 Báo cáo PDF Đầy đủ")

    pdf_bytes = report_pdf.read_bytes()
    pdf_b64   = base64.b64encode(pdf_bytes).decode()

    # Nhúng PDF trực tiếp trong trang bằng iframe
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{pdf_b64}" '
        f'width="100%" height="900px" style="border:1px solid #ddd; border-radius:8px;"></iframe>',
        unsafe_allow_html=True,
    )

    # Nút tải về
    st.download_button(
        label="⬇️ Tải báo cáo PDF",
        data=pdf_bytes,
        file_name=f"market_report_detail_{date_str}.pdf",
        mime="application/pdf",
    )
else:
    st.info("File PDF chưa được tạo cho ngày này.")
