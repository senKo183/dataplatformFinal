"""
Streamlit Dashboard — VN Market Intelligence
Entry point: multi-page app.
Chạy: streamlit run app.py
Truy cập: http://localhost:8501
"""

import streamlit as st

st.set_page_config(
    page_title="VN Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.title("📊 VN Market Intel")
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Menu:**
- 📰 Feed Báo cáo
- 🔔 Bảng Alert
- 📈 Lịch sử Phân tích
""")

# ── Trang chủ ──────────────────────────────────────────────────────────────────
st.title("VN Market Intelligence Dashboard")
st.markdown("Hệ thống phân tích thị trường chứng khoán Việt Nam — cập nhật mỗi ngày lúc 15:15 ICT")
st.markdown("---")

# Gợi ý dùng multi-page: xem thư mục pages/
col1, col2, col3 = st.columns(3)
with col1:
    st.info("📰 **Feed Báo cáo**\nDanh sách báo cáo phân tích theo ngày + PDF viewer inline")
with col2:
    st.warning("🔔 **Bảng Alert**\nThông báo biến động lớn có badge mức độ (HIGH / MEDIUM / INFO)")
with col3:
    st.success("📈 **Lịch sử**\nBiểu đồ giá và BCTC trong 30/60/90 ngày")
