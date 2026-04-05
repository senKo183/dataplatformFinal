# VN Market Intelligence — Change Log

> Mỗi lần thêm hoặc sửa file, một entry mới sẽ được ghi vào đây.  
> Format: `[YYYY-MM-DD] | Loại | File(s) | Mô tả`

---

## [03/04/2026] — Demo: báo cáo tích hợp kỹ thuật + tin (Agent 3)

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | CREATE | `agent3_analyst/prompts/stock_detail_integrated.txt` | Báo cáo chi tiết: kỹ thuật + tin (title/mô tả ngắn), kịch bản có điều kiện, không BCTC |
| 03/04/2026 | CREATE | `agent3_analyst/prompts/stock_feed_integrated.txt` | Đoạn tổng quan ngắn (kỹ thuật + tin) |
| 03/04/2026 | UPDATE | `scripts/demo_midterm.py` | Đọc `storage/raw/news_{date}.json`, `build_news_block` theo ticker; mặc định dùng prompt tích hợp; `--legacy-technical-only` để giữ prompt cũ chỉ kỹ thuật |

---

## [03/04/2026] — Tin vnstock: summary + đường dẫn lưu chuẩn

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | UPDATE | `agent1_crawler/news_crawl.py` | Map `summary` ưu tiên cột `short_description` (và alias sapo/teaser/…) từ `company.news()`; thêm trường `short_description` trong JSON; load `VNSTOCK_API_KEY` từ `Final_Demo/.env` |
| 03/04/2026 | UPDATE | `agent1_crawler/*.py` (price, news, technical, dividend, doc) | Mặc định ghi `storage/raw/` và `resources/` dưới **thư mục gốc dự án** (`Final_Demo/`), không còn nhầm với `agent1_crawler/storage` khi chạy `main.py` từ `agent1_crawler/` — khớp `scripts/demo_midterm.py` |
| 03/04/2026 | UPDATE | `.env.example` | Thêm placeholder `VNSTOCK_API_KEY=` |
| 03/04/2026 | UPDATE | `IMPLEMENTATION_PLAN.md`, `vn_stock_intelligence_README.md`, `Gki_Report.md` | Ghi nhận cấu hình vnstock + link tài liệu Vnstock News / `instructions.md` / `AGENT_SKILLS_NEWS.md` |

> **Bảo mật:** Nếu đã dán API key vnstock ở kênh không an toàn, nên **đổi key** trên cổng quản lý vnstock và chỉ lưu key trong `.env` (đã gitignore).

---

## [03/04/2026] — Agent 1 lưu thêm vào resources/

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | UPDATE | `agent1_crawler/news_crawl.py` | Lưu thêm `resources/news/news_{date}.json` song song với `storage/raw` |
| 03/04/2026 | UPDATE | `agent1_crawler/doc_downloader.py` | Lưu thêm PDF vào `resources/docs/{date}/` và manifest `resources/docs/docs_manifest_{date}.json` |
| 03/04/2026 | UPDATE | `agent1_crawler/dividend_fetch.py` | Lưu thêm `resources/dividends/dividends_{date}.json` |
| 03/04/2026 | UPDATE | `agent1_crawler/price_fetch.py` | Lưu thêm `resources/prices/prices_{date}.json` |
| 03/04/2026 | UPDATE | `agent1_crawler/technical_calc.py` | Lưu thêm `resources/technicals/technicals_{date}.json` |
| 03/04/2026 | UPDATE | `agent1_crawler/main.py` | Bổ sung log output để chỉ rõ `resources/` dùng cho Agent 2/3 |

---

## [03/04/2026] — Báo cáo giữa kỳ tổng hợp

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | CREATE | `Gki_Report.md` | Báo cáo tiến độ hiện tại: những gì đã làm, kết quả `scripts/demo_midterm.py`, và kế hoạch giữa kỳ ưu tiên Agent 1 + News + Agent 2/3; Airflow để cuối kỳ |

---

## [03/04/2026] — Feed vs chi tiết: hai file MD + dashboard

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | UPDATE | `scripts/demo_midterm.py` | Sinh **hai** file: `market_report_{date}.md` (prompt `technical_interpret_feed`) và `market_report_detail_{date}.md` (prompt `technical_interpret_detail`); thêm `--max-tokens-feed` |
| 03/04/2026 | UPDATE | `dashboard/pages/01_feed.py` | Feed đọc `market_report_{date}.md` (tổng quan) |
| 03/04/2026 | UPDATE | `dashboard/pages/02_article.py` | Chi tiết đọc `market_report_detail_{date}.md` + PDF `market_report_detail_{date}.pdf` nếu có |

---

## [03/04/2026] — Demo giữa kỳ: LLM đa provider + script tự động

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | UPDATE | `.env` / `.env.example` | Thêm `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_MODEL`, `DEMO_LLM_PROVIDER` |
| 03/04/2026 | CREATE | `common/llm_providers.py` | Gọi LLM: **gemini** (Google AI Studio), **deepseek** (API OpenAI-compatible), **claude** (Anthropic) |
| 03/04/2026 | CREATE | `common/prompt_utils.py` | `load_prompt_template()` — thay `{key}` trong file prompt |
| 03/04/2026 | CREATE | `scripts/demo_midterm.py` | Pipeline demo: Agent 1 (`--tickers`) → LLM `technical_interpret` → `reports/…/market_report_*.md` + `storage/alerts_*.json` |
| 03/04/2026 | CREATE | `requirements.txt` | Dependencies: anthropic, google-generativeai, httpx, dotenv, vnstock, streamlit, … |
| 03/04/2026 | UPDATE | `agent1_crawler/main.py` | Tham số `--tickers CSV` để chạy subset mã (demo nhanh) |
| 03/04/2026 | UPDATE | `agent1_crawler/technical_calc.py` | Tham số `output_date` để tên file `technicals_{date}.json` khớp `--date` của Agent 1 |
| 03/04/2026 | UPDATE | `agent3_analyst/prompts/technical_interpret.txt` | Chuẩn hóa placeholder `{key}` (tương thích `prompt_utils`) |
| 03/04/2026 | UPDATE | `IMPLEMENTATION_PLAN.md` | Đánh dấu hoàn thành mục tối thiểu giai đoạn A + hướng dẫn chạy `demo_midterm.py` |
| 03/04/2026 | UPDATE | `agent1_crawler/technical_calc.py` | RSI/MACD/Bollinger bằng **pandas thuần** (bỏ `pandas-ta`, tương thích Python 3.11 khi PyPI chỉ còn bản yêu cầu 3.12+) |
| 03/04/2026 | UPDATE | `agent1_crawler/price_fetch.py`, `news_crawl.py`, `technical_calc.py` | `mkdir(parents=True)` trước khi ghi JSON |
| 03/04/2026 | UPDATE | `scripts/demo_midterm.py` | `--sample-data` (JSON mẫu + LLM); `PYTHONIOENCODING=utf-8` cho subprocess Agent 1 |
| 03/04/2026 | UPDATE | `requirements.txt` | Ghim `numpy>=1.26,<2` (tránh xung đột numpy 2 với matplotlib/tensorflow trên một số máy) |

> **Bảo mật:** Nếu API key từng dán lộ ở chat công khai, nên **rotate** key trên console DeepSeek / Google AI Studio và cập nhật `.env`.

---

## [03/04/2026] — Chia giai đoạn giữa kỳ / cuối kỳ + báo cáo giữa kỳ

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 03/04/2026 | UPDATE | `IMPLEMENTATION_PLAN.md` | Thêm mục **Hai giai đoạn triển khai**: (A) Pilot/demo giữa kỳ — phạm vi tối thiểu; (B) Hoàn thiện cuối kỳ — Phase 2–8. Cập nhật “Bước tiếp theo” tách hành động cho A và B; liên kết `MID_TERM_REPORT.txt` |
| 03/04/2026 | CREATE | `MID_TERM_REPORT.txt` | Báo cáo giữa kỳ dạng `.txt`: ý tưởng, sơ đồ kiến trúc ASCII, công cụ, cách điều khiển agent bằng prompt, mục có thể demo cho giáo viên; mốc báo cáo tham chiếu **05/03/2026** (có ghi chú chỉnh theo lịch lớp) |
| 03/04/2026 | UPDATE | `IMPLEMENTATION_PLAN.md` | Sửa mục “Chưa làm”: không còn liệt kê `llm_caller.py` (đã triển khai) |

---

## [02/04/2026] — Session khởi tạo dự án

### 📋 v0.1 — Thiết kế & Tài liệu hệ thống

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 14:00 | CREATE | `vn_stock_intelligence_README.md` | README đầy đủ: kiến trúc, skills, Airflow/Docker, Streamlit Dashboard |
| 02/04/2026 14:30 | UPDATE | `vn_stock_intelligence_README.md` | Chỉnh lại: Skills = prompt templates, Web = Streamlit (bỏ FastAPI+React) |
| 02/04/2026 15:00 | CREATE | `IMPLEMENTATION_PLAN.md` | Kế hoạch triển khai 8 phase, timeline đến 12/05/2026 |
| 02/04/2026 15:05 | CREATE | `CHANGE_LOG.md` | File này — bắt đầu theo dõi thay đổi |

---

### 🏗️ v0.2 — Tạo cấu trúc thư mục & Config

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:10 | CREATE | `config/settings.yaml` | Cấu hình toàn hệ thống: Claude model, ngưỡng cảnh báo, đường dẫn storage |
| 02/04/2026 15:10 | CREATE | `config/watchlist.yaml` | 20 mã theo dõi: VN30 (15 mã) + Custom (5 mã) |
| 02/04/2026 15:10 | CREATE | `docker-compose.yml` | Định nghĩa services: airflow, agent1–4, dashboard |
| 02/04/2026 15:10 | CREATE | `.env.example` | Template biến môi trường (không chứa key thực) |
| 02/04/2026 15:10 | CREATE | `.env` | File biến môi trường thực — CLAUDE_API_KEY đã được cấu hình |
| 02/04/2026 15:10 | CREATE | `.gitignore` | Bảo vệ `.env`, `storage/`, `reports/` khỏi git |
| 02/04/2026 15:10 | CREATE | `airflow/dags/market_intelligence_dag.py` | DAG Airflow đầy đủ: 8 tasks, dependency graph, cron 15:15 ICT |

---

### 🤖 v0.3 — Agent 1: Data Ingestion (Code hoàn chỉnh)

> Agent 1 không dùng LLM — chỉ gồm Python modules thu thập dữ liệu.

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:20 | CREATE | `agent1_crawler/price_fetch.py` | Kéo giá OHLCV, tính change_pct và volume_ratio từ vnstock |
| 02/04/2026 15:20 | CREATE | `agent1_crawler/news_crawl.py` | Cào tin CafeF RSS + vnstock company news |
| 02/04/2026 15:20 | CREATE | `agent1_crawler/dividend_fetch.py` | Lấy lịch cổ tức trong `lookahead_days` ngày tới |
| 02/04/2026 15:20 | CREATE | `agent1_crawler/technical_calc.py` | Tính MA20/50, RSI(14), MACD, Bollinger Bands bằng pandas-ta |
| 02/04/2026 15:20 | CREATE | `agent1_crawler/doc_downloader.py` | Tải PDF tài liệu công bố thông tin từ HOSE/SSI |
| 02/04/2026 15:20 | CREATE | `agent1_crawler/main.py` | Entry point: chạy tuần tự 5 modules, gọi bởi Airflow |

---

### 📝 v0.4 — Prompt Skills cho Agent 2, 3, 4

> Skills = file `.txt` định nghĩa nhiệm vụ LLM cho từng tình huống cụ thể.

**Agent 2 — Financial Reader (4 prompts)**

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:30 | CREATE | `agent2_financial_reader/prompts/bctc_summary.txt` | Skill: Tóm tắt & nhận xét kết quả kinh doanh theo quý |
| 02/04/2026 15:30 | CREATE | `agent2_financial_reader/prompts/pdf_doc_extract.txt` | Skill: Trích xuất thông tin từ văn bản PDF tài liệu |
| 02/04/2026 15:30 | CREATE | `agent2_financial_reader/prompts/anomaly_explain.txt` | Skill: Giải thích nguyên nhân chỉ số tài chính bất thường |
| 02/04/2026 15:30 | CREATE | `agent2_financial_reader/prompts/ratio_interpret.txt` | Skill: Nhận định EPS/P/E/ROE/D/E theo bối cảnh ngành |

**Agent 3 — Analyst (5 prompts)**

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:35 | CREATE | `agent3_analyst/prompts/technical_interpret.txt` | Skill: Diễn giải tín hiệu RSI/MA/MACD/volume |
| 02/04/2026 15:35 | CREATE | `agent3_analyst/prompts/news_sentiment.txt` | Skill: Phân loại cảm xúc + mức độ tác động từng tin tức |
| 02/04/2026 15:35 | CREATE | `agent3_analyst/prompts/dividend_impact.txt` | Skill: Xác nhận/bác bỏ giả thuyết điều chỉnh giá cổ tức |
| 02/04/2026 15:35 | CREATE | `agent3_analyst/prompts/cause_classify.txt` | Skill: Tổng hợp → phân loại nguyên nhân biến động chính |
| 02/04/2026 15:35 | CREATE | `agent3_analyst/prompts/market_summary.txt` | Skill: Bình luận toàn cảnh thị trường cuối phiên |

**Agent 4 — Reporter (4 prompts)**

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:40 | CREATE | `agent4_reporter/prompts/report_narrative.txt` | Skill: Viết mở đầu báo cáo dạng bài báo tài chính |
| 02/04/2026 15:40 | CREATE | `agent4_reporter/prompts/stock_highlight.txt` | Skill: Viết mục từng mã nổi bật trong ngày |
| 02/04/2026 15:40 | CREATE | `agent4_reporter/prompts/alert_message.txt` | Skill: Soạn thông báo alert cho Streamlit Dashboard |
| 02/04/2026 15:40 | CREATE | `agent4_reporter/prompts/weekly_digest.txt` | Skill: Tổng hợp xu hướng cả tuần (chạy thứ Sáu) |

---

### 🖥️ v0.5 — Streamlit Dashboard (4 trang skeleton)

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 15:45 | CREATE | `dashboard/app.py` | Entry point multi-page Streamlit app |
| 02/04/2026 15:45 | CREATE | `dashboard/pages/01_feed.py` | Trang feed báo cáo hàng ngày + bảng alert bên phải |
| 02/04/2026 15:45 | CREATE | `dashboard/pages/02_article.py` | Xem bài báo chi tiết + PDF viewer inline (base64 iframe) |
| 02/04/2026 15:45 | CREATE | `dashboard/pages/03_alerts.py` | Bảng alert có filter theo ngày, mức độ, mã cổ phiếu |
| 02/04/2026 15:45 | CREATE | `dashboard/pages/04_history.py` | Lịch sử 30/60/90 ngày + Plotly chart + bảng nguyên nhân |

---

### 🔑 v0.6 — Bảo mật API Key & LLM Caller

| Thời gian | Loại | File | Mô tả |
|---|---|---|---|
| 02/04/2026 16:00 | CREATE | `.env` | CLAUDE_API_KEY được cấu hình (không commit vào git) |
| 02/04/2026 16:00 | CREATE | `.gitignore` | Bảo vệ `.env`, `storage/`, `reports/` |
| 02/04/2026 16:00 | UPDATE | `config/settings.yaml` | Bỏ hardcode placeholder, chú thích rõ đọc từ env |
| 02/04/2026 16:00 | CREATE | `agent2_financial_reader/llm_caller.py` | Wrapper gọi Claude: load prompt template + retry tự động |
| 02/04/2026 16:00 | CREATE | `agent3_analyst/llm_caller.py` | Wrapper gọi Claude (max_tokens=1500 cho output JSON dài) |
| 02/04/2026 16:00 | CREATE | `agent4_reporter/llm_caller.py` | Wrapper gọi Claude (max_tokens=2000 cho viết báo cáo) |

---

## Thống kê

| Hạng mục | Số lượng |
|---|---|
| Tổng file đã tạo | 33 files |
| Prompt templates (.txt) | 13 files |
| Python modules | 12 files |
| Config / YAML | 3 files |
| Dashboard pages | 5 files |
| DAG / Infrastructure | 4 files |
| Tài liệu (.md) | 3 files |

---

## Còn thiếu (cần làm tiếp)

| Ưu tiên | File cần tạo | Phase |
|---|---|---|
| 🔴 Cao | `agent1_crawler/Dockerfile` + `requirements.txt` | Phase 1 |
| 🔴 Cao | `agent2_financial_reader/bctc_parse.py` | Phase 2 |
| 🔴 Cao | `agent2_financial_reader/pdf_doc_reader.py` | Phase 2 |
| 🔴 Cao | `agent2_financial_reader/ratio_calc.py` | Phase 2 |
| 🔴 Cao | `agent2_financial_reader/main.py` | Phase 2 |
| 🟡 Trung bình | `agent3_analyst/ta_rules.py` | Phase 3 |
| 🟡 Trung bình | `agent3_analyst/main.py` | Phase 3 |
| 🟡 Trung bình | `agent4_reporter/pdf_generator.py` | Phase 4 |
| 🟡 Trung bình | `agent4_reporter/history_logger.py` | Phase 4 |
| 🟡 Trung bình | `agent4_reporter/main.py` | Phase 4 |
| ⬜ Thấp | `Dockerfile` cho agent2, agent3, agent4, dashboard | Phase 6 |
| ⬜ Thấp | `requirements.txt` cho từng agent | Phase 6 |
