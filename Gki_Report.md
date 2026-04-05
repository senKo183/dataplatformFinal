# GKI Report - VN Market Intelligence

**Thời điểm cập nhật:** 03/04/2026  
**Mục tiêu tài liệu:** Báo cáo tiến độ hiện tại, kết quả demo, và kế hoạch triển khai phục vụ báo cáo giữa kỳ.

---

## 1) Tổng quan dự án

`VN Market Intelligence` là hệ thống phân tích thị trường chứng khoán Việt Nam theo hướng multi-agent:

- **Agent 1 (Data Ingestion):** lấy dữ liệu giá, chỉ báo kỹ thuật, tin tức, cổ tức, tài liệu công bố.
- **Agent 2 (Financial Reader):** đọc BCTC/tài liệu và diễn giải chỉ số tài chính.
- **Agent 3 (Analyst):** phân tích kỹ thuật + tin tức + nguyên nhân biến động.
- **Agent 4 (Reporter):** tổng hợp báo cáo đầu ra và phục vụ dashboard.
- **Dashboard (Streamlit):** giao diện xem feed, báo cáo chi tiết, alerts, lịch sử.
- **Airflow:** điều phối chạy theo lịch (định hướng cuối kỳ).

---

## 2) Những gì đã làm được đến hiện tại

### 2.1 Hoàn thiện phần nền tảng và cấu trúc
- Đã có khung thư mục đầy đủ cho 4 agents, dashboard, airflow, config, storage, reports.
- Đã có tài liệu kế hoạch triển khai (`IMPLEMENTATION_PLAN.md`) và nhật ký thay đổi (`CHANGE_LOG.md`).
- Đã có cấu hình môi trường và key theo hướng không commit secret.

### 2.2 Agent 1 và dữ liệu đầu vào
- Agent 1 đã có các module:
  - `price_fetch.py`
  - `news_crawl.py`
  - `dividend_fetch.py`
  - `technical_calc.py`
  - `doc_downloader.py`
  - `main.py`
- Đã bổ sung khả năng chạy nhanh theo tập mã nhỏ qua `--tickers`.
- Đã tối ưu `technical_calc.py` để tính chỉ báo bằng pandas thuần (không phụ thuộc `pandas-ta`).
- **Tin vnstock:** `news_crawl.py` chuẩn hóa trường `summary` từ mô tả ngắn API (ưu tiên `short_description`), có thể bật `VNSTOCK_API_KEY` trong `.env`; tham chiếu [Vnstock News — mẫu cập nhật tin](https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc) và `agent1_crawler/AGENT_SKILLS_NEWS.md`.
- **Đường dẫn lưu:** `storage/raw/` và `resources/` mặc định nằm dưới thư mục gốc dự án (khớp `scripts/demo_midterm.py` đọc `storage/raw/prices_*.json`).

### 2.3 LLM đa provider cho demo
- Đã có module dùng chung `common/llm_providers.py`:
  - hỗ trợ `gemini`, `deepseek`, `claude`
  - với Gemini có fallback qua nhiều model khi lỗi quota hoặc model không hỗ trợ.
- Đã có `common/prompt_utils.py` để load template prompt và thay biến.

### 2.4 Tách rõ 2 loại báo cáo trên web
- Đã tách thành 2 đầu ra Markdown:
  - `market_report_[date].md` (báo cáo thị trường tổng quan)
  - `market_report_detail_[date].md` (báo cáo phân tích chi tiết)
- Đã chỉnh dashboard để:
  - Feed đọc file tổng quan
  - Article đọc file chi tiết

### 2.5 Demo giữa kỳ — Agent 3 với tin + kỹ thuật (không BCTC)
- `scripts/demo_midterm.py` mặc định đọc `storage/raw/news_{date}.json`, lọc tin theo `ticker`, ghép `news_block` (tiêu đề + mô tả ngắn).
- Prompt LLM: `stock_feed_integrated.txt` (đoạn tổng quan) và `stock_detail_integrated.txt` (phân tích chi tiết: kỹ thuật + tin, kịch bản có điều kiện).
- Có thể dùng `--legacy-technical-only` để quay lại prompt chỉ kỹ thuật (`technical_interpret_feed` / `technical_interpret_detail`) khi không cần tin.

---

## 3) Kết quả chạy `scripts/demo_midterm.py` tại thời điểm hiện tại

### 3.1 Luồng chạy demo
Script `scripts/demo_midterm.py` hiện chạy theo các bước:
1. Chuẩn bị dữ liệu:
   - chạy Agent 1 thật, hoặc
   - dùng `--sample-data` để tạo dữ liệu mẫu (lúc này không có `news_{date}.json` trừ khi đã có sẵn từ lần chạy trước).
2. Sinh alert JSON theo ngưỡng cấu hình.
3. Đọc `storage/raw/news_{date}.json` (nếu có), lọc tin theo từng mã trong `--tickers`.
4. Gọi LLM để tạo (mặc định):
   - bản tổng quan — prompt `stock_feed_integrated`
   - bản chi tiết — prompt `stock_detail_integrated`
5. Ghi output:
   - `reports/{date}/market_report_{date}.md`
   - `reports/{date}/market_report_detail_{date}.md`
   - `storage/alerts_{date}.json`

### 3.2 Kết quả output đã có
- Đã có file:
  - `reports/2026-04-03/market_report_2026-04-03.md`
  - `reports/2026-04-03/market_report_detail_2026-04-03.md`
- Nội dung bản tổng quan ngắn hơn, bản chi tiết theo cấu trúc tích hợp kỹ thuật + tin (khi có dữ liệu tin cho mã).
- Dashboard đã hiển thị tách bạch 2 mục Feed và Article theo đúng 2 file riêng.

### 3.3 Trạng thái đúng/sai của demo
- **Đúng:** Demo chạy được end-to-end cho phần web hiển thị báo cáo; luồng mặc định đã **tích hợp tin** (title/mô tả ngắn) với chỉ báo kỹ thuật/giá qua prompt Agent 3.
- **Giới hạn hiện tại:** Chưa nối **BCTC / Agent 2** vào `demo_midterm.py`; nếu thiếu file `news_{date}.json` hoặc không có tin gắn mã, phần tin trong prompt sẽ hiển thị thông báo trống và phân tích chủ yếu dựa trên kỹ thuật.

---

## 4) Định hướng triển khai cho giữa kỳ (theo yêu cầu hiện tại)

Bạn yêu cầu giữa kỳ ưu tiên:
- Agent 1 lấy được thông tin mã chứng khoán từ thư viện.
- Agent 1 cào được news liên quan các mã đáng chú ý.
- Dùng Agent 2 và Agent 3 để phân tích trước, viết báo cáo trước.
- Demo trên web trước.
- Airflow để cuối kỳ.

Kế hoạch thực hiện giữa kỳ được chốt như sau:

### 4.1 Scope giữa kỳ (điểm cần đạt)
1. **Agent 1 (bắt buộc):**
   - lấy dữ liệu giá + chỉ báo kỹ thuật theo mã
   - cào tin tức liên quan mã (RSS + nguồn thư viện)
   - lưu dữ liệu chuẩn hóa về `storage/raw/`
2. **Agent 2 (ưu tiên khi có BCTC/tài liệu):**
   - đọc/tóm tắt dữ liệu tài chính hoặc tài liệu đầu vào có sẵn
   - tạo output trung gian để Agent 3 dùng lại (hiện demo giữa kỳ có thể bỏ qua nếu chỉ dùng tin + kỹ thuật)
3. **Agent 3 (bắt buộc):**
   - hợp nhất dữ liệu kỹ thuật + news; (tùy chọn sau) tóm tắt tài chính từ Agent 2
   - tạo 2 lớp nội dung:
     - tổng quan thị trường
     - phân tích chi tiết theo mã
4. **Web demo (bắt buộc):**
   - hiển thị rõ 2 mục khác nhau: tổng quan vs chi tiết
   - có alerts để giáo viên xem tín hiệu cảnh báo

### 4.2 Scope cuối kỳ (để lại sau)
- Tích hợp orchestration hoàn chỉnh vào Airflow (lịch chạy, retry, monitoring).
- Hoàn thiện đóng gói báo cáo PDF, lịch sử SQLite đầy đủ, và deployment.

---

## 5) Kết luận báo cáo giữa kỳ

Dự án đã đi qua giai đoạn dựng nền và đã có demo chạy được trên web.  
Tại thời điểm này, hệ thống đã:
- tạo được báo cáo tổng quan và báo cáo chi tiết thành 2 file riêng (demo mặc định: kỹ thuật + tin từ Agent 1),
- hiển thị được lên dashboard,
- có khung đa mô hình LLM và cơ chế fallback model.

Mục tiêu giữa kỳ tiếp theo là bổ sung **Agent 2 (BCTC/tài liệu)** vào cùng pipeline với **tin + kỹ thuật (Agent 3)** khi có dữ liệu tài chính; đồng thời hoàn thiện scheduling (Airflow) ở cuối kỳ.

python scripts/demo_midterm.py --tickers VCB,FPT,VIC --provider gemini