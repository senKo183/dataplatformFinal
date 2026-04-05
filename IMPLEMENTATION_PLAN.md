# VN Market Intelligence — Implementation Plan

> **Cập nhật lần cuối:** 03/04/2026 (tin vnstock `short_description` + đường dẫn `storage`/`resources` tại thư mục gốc)  
> **Trạng thái tổng thể:** 🟡 Đang triển khai — Phase 0–1 hoàn thành, Phase 2–5 đang chờ  
> **Xem chi tiết thay đổi:** [`CHANGE_LOG.md`](./CHANGE_LOG.md)  
> **Báo cáo giữa kỳ (ý tưởng + demo):** [`MID_TERM_REPORT.txt`](./MID_TERM_REPORT.txt)

---

## Hai giai đoạn triển khai

Dự án được chia thành **hai đường thời gian** để vừa có bản demo cho giữa kỳ, vừa có bản hoàn chỉnh cho cuối kỳ.

| Giai đoạn | Mục tiêu | Phạm vi | Hạn mục thời gian (mục tiêu) |
|---|---|---|---|
| **A — Giữa kỳ (Pilot / Demo)** | Chạy thử một vài luồng thật, chứng minh ý tưởng & cách làm | Agent 1 chạy end-to-end; 1–2 luồng LLM minh họa (prompt skills + `llm_caller`); Streamlit xem được dữ liệu mẫu hoặc output thật từng phần; trình bày kiến trúc + DAG + ý tưởng điều khiển agent | **Trước 05/03/2026** (theo yêu cầu báo cáo; chỉnh lại nếu lịch lớp khác) |
| **B — Cuối kỳ (Hoàn thiện)** | Pipeline đầy đủ 4 agent, lưu trữ, báo cáo, dashboard nối dữ liệu thật, Docker/Airflow ổn định | Hoàn thành Phase 2–8 trong bảng tiến độ; integration test; tùy chọn deploy | Theo timeline tổng (đến ~12/05/2026 trong kế hoạch gốc) |

**Phạm vi giai đoạn A (đủ để demo giáo viên):**

- [x] Tài liệu kiến trúc, prompt skills, DAG skeleton, dashboard skeleton  
- [x] Agent 1: thu thập giá, tin, cổ tức, chỉ báo kỹ thuật, PDF  
- [x] **Tối thiểu:** chạy `agent1_crawler/main.py --tickers VCB,FPT,VIC` (hoặc script `scripts/demo_midterm.py`), output trong `storage/raw/`  
- [x] **Tối thiểu:** demo LLM skill `technical_interpret` qua `common/llm_providers.py` — **Gemini Flash / DeepSeek / Claude** (chọn `--provider`)  
- [x] **Tối thiểu:** Streamlit đọc `reports/{ngày}/market_report_*.md` và `storage/alerts_*.json` sau khi chạy demo  

**Phạm vi giai đoạn B (cuối kỳ):** toàn bộ hạng mục “Chưa làm” và các task ⬜ trong Phase 2–8; không lặp lại trong bảng trên.

**Tính năng có thể ưu tiên hoàn thiện trong các phiên làm việc ngắn (hướng tới giai đoạn B):**  
`requirements.txt` + `Dockerfile` Agent 1; `schema.sql` + prototype `history_logger`; các module Agent 2 (`bctc_parse`, `ratio_calc`, …); orchestrator Agent 3; `pdf_generator` / `alert_writer` Agent 4; dashboard nối dữ liệu thật; `docker compose` end-to-end; integration test (Phase 7–8).

---

## Tóm tắt Tiến độ

| Phase | Nội dung | Trạng thái | Hoàn thành |
|---|---|---|---|
| **Phase 0** | Thiết kế hệ thống & Tài liệu | ✅ Xong | 100% |
| **Phase 1** | Agent 1 — Data Ingestion | ✅ Xong | 100% |
| **Phase 2** | Agent 2 — Financial Reader | 🟡 Một phần | 50% |
| **Phase 3** | Agent 3 — Analyst | 🟡 Một phần | 45% |
| **Phase 4** | Agent 4 — Reporter | 🟡 Một phần | 40% |
| **Phase 5** | Streamlit Dashboard | 🟡 Một phần | 50% |
| **Phase 6** | Airflow & Docker | 🟡 Một phần | 45% |
| **Phase 7** | Integration & Testing | ⬜ Chưa bắt đầu | 0% |
| **Phase 8** | Production Deployment | ⬜ Chưa bắt đầu | 0% |

---

## Đã làm được những gì?

### ✅ Hoàn thành

#### Tài liệu & Thiết kế
- [x] `vn_stock_intelligence_README.md` — README đầy đủ: kiến trúc, skills, Airflow/Docker, Streamlit
- [x] `IMPLEMENTATION_PLAN.md` — File kế hoạch này

#### Cấu trúc thư mục & Skeleton
- [x] Toàn bộ cấu trúc thư mục: `agent1~4/`, `dashboard/`, `airflow/`, `config/`, `storage/`
- [x] `config/settings.yaml` — Cấu hình toàn hệ thống
- [x] `config/watchlist.yaml` — Danh sách 20 mã theo dõi (VN30 + custom)
- [x] `docker-compose.yml` — Định nghĩa toàn bộ services
- [x] `.env.example` — Template biến môi trường

#### Agent 1 — Data Ingestion (Code hoàn chỉnh)
- [x] `agent1_crawler/price_fetch.py` — Kéo giá OHLCV từ vnstock
- [x] `agent1_crawler/news_crawl.py` — CafeF RSS + vnstock `company.news()`; trường `summary` lấy ưu tiên `short_description` (xem [mẫu Vnstock News](https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc)); tùy chọn `VNSTOCK_API_KEY` trong `.env`
- [x] `agent1_crawler/dividend_fetch.py` — Lịch cổ tức 30 ngày tới
- [x] `agent1_crawler/technical_calc.py` — MA20/50, RSI(14), MACD, Bollinger
- [x] `agent1_crawler/doc_downloader.py` — Tải PDF tài liệu từ HOSE/SSI
- [x] `agent1_crawler/main.py` — Entry point chạy tuần tự 5 modules

#### Prompt Skills — Agent 2 (4 files)
- [x] `agent2_financial_reader/prompts/bctc_summary.txt`
- [x] `agent2_financial_reader/prompts/pdf_doc_extract.txt`
- [x] `agent2_financial_reader/prompts/anomaly_explain.txt`
- [x] `agent2_financial_reader/prompts/ratio_interpret.txt`

#### Prompt Skills — Agent 3 (5 files)
- [x] `agent3_analyst/prompts/technical_interpret.txt`
- [x] `agent3_analyst/prompts/news_sentiment.txt`
- [x] `agent3_analyst/prompts/dividend_impact.txt`
- [x] `agent3_analyst/prompts/cause_classify.txt`
- [x] `agent3_analyst/prompts/market_summary.txt`

#### Prompt Skills — Agent 4 (4 files)
- [x] `agent4_reporter/prompts/report_narrative.txt`
- [x] `agent4_reporter/prompts/stock_highlight.txt`
- [x] `agent4_reporter/prompts/alert_message.txt`
- [x] `agent4_reporter/prompts/weekly_digest.txt`

#### Bảo mật & LLM Caller
- [x] `.env` — CLAUDE_API_KEY đã được cấu hình (bảo vệ bởi `.gitignore`)
- [x] `.gitignore` — Loại trừ `.env`, `storage/`, `reports/` khỏi git
- [x] `agent2_financial_reader/llm_caller.py` — Wrapper Claude API: load prompt + retry
- [x] `agent3_analyst/llm_caller.py` — Wrapper Claude API (max_tokens=1500)
- [x] `agent4_reporter/llm_caller.py` — Wrapper Claude API (max_tokens=2000)

#### Airflow DAG
- [x] `airflow/dags/market_intelligence_dag.py` — DAG đầy đủ với dependency graph

#### Streamlit Dashboard (4 trang)
- [x] `dashboard/app.py` — Entry point multi-page
- [x] `dashboard/pages/01_feed.py` — Feed báo cáo + alerts
- [x] `dashboard/pages/02_article.py` — PDF viewer inline
- [x] `dashboard/pages/03_alerts.py` — Bảng alert có filter
- [x] `dashboard/pages/04_history.py` — Lịch sử + Plotly chart

---

### ⬜ Chưa làm

- Python code xử lý chính cho Agent 2, 3, 4 (`main.py`, các module parse/orchestrator/generator — `llm_caller.py` đã có)
- `Dockerfile` cho từng agent và dashboard
- `requirements.txt` cho từng agent
- Schema SQLite (`history.sqlite`)
- Integration testing toàn pipeline
- Deploy production

---

## Implementation Plan Chi Tiết

---

### Phase 0 — Thiết kế hệ thống ✅ XONG

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| Viết README đầy đủ | `vn_stock_intelligence_README.md` | 3h | ✅ |
| Thiết kế prompt skills cho Agent 2/3/4 | `*/prompts/*.txt` | 2h | ✅ |
| Tạo toàn bộ cấu trúc thư mục | — | 30m | ✅ |
| Cấu hình `settings.yaml` + `watchlist.yaml` | `config/` | 30m | ✅ |
| `docker-compose.yml` skeleton | `docker-compose.yml` | 1h | ✅ |
| Airflow DAG skeleton | `airflow/dags/market_intelligence_dag.py` | 1h | ✅ |

**Tổng Phase 0:** ~8 giờ | **Deadline:** ✅ 02/04/2026

---

### Phase 1 — Agent 1: Data Ingestion ✅ XONG

> Agent 1 không dùng LLM — chỉ gồm các Python modules thu thập dữ liệu.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| Module kéo giá OHLCV | `price_fetch.py` | 2h | ✅ |
| Module cào tin tức | `news_crawl.py` | 2h | ✅ |
| Module lịch cổ tức | `dividend_fetch.py` | 1.5h | ✅ |
| Module tính kỹ thuật (MA/RSI/MACD) | `technical_calc.py` | 2h | ✅ |
| Module tải PDF tài liệu | `doc_downloader.py` | 2h | ✅ |
| Entry point `main.py` | `main.py` | 30m | ✅ |
| `Dockerfile` | `agent1_crawler/Dockerfile` | 30m | ⬜ |
| `requirements.txt` | `agent1_crawler/requirements.txt` | 15m | ⬜ |
| Unit test thu thập 3 mã mẫu | — | 1h | ⬜ |

**Tổng Phase 1:** ~12 giờ | **Deadline:** 05/04/2026

---

### Phase 2 — Agent 2: Financial Reader 🟡 ĐANG LÀM

> Prompts đã xong. Cần viết Python code: parse BCTC, đọc PDF, gọi LLM.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| ✅ Prompt: tóm tắt BCTC | `prompts/bctc_summary.txt` | 1h | ✅ |
| ✅ Prompt: trích xuất PDF | `prompts/pdf_doc_extract.txt` | 1h | ✅ |
| ✅ Prompt: giải thích bất thường | `prompts/anomaly_explain.txt` | 1h | ✅ |
| ✅ Prompt: nhận định chỉ số | `prompts/ratio_interpret.txt` | 1h | ✅ |
| Module fetch & parse BCTC | `bctc_parse.py` | 2h | ⬜ |
| Module đọc nội dung PDF | `pdf_doc_reader.py` | 1.5h | ⬜ |
| Module tính chỉ số tài chính | `ratio_calc.py` | 2h | ⬜ |
| Module phát hiện bất thường | `anomaly_detect.py` | 1.5h | ⬜ |
| Module so sánh các kỳ | `quarter_compare.py` | 1h | ⬜ |
| ✅ LLM caller với prompt loader | `llm_caller.py` | 2h | ✅ |
| Entry point `main.py` | `main.py` | 1h | ⬜ |
| `Dockerfile` + `requirements.txt` | — | 30m | ⬜ |
| Test với 2 mã mẫu (VCB, FPT) | — | 1.5h | ⬜ |

**Tổng Phase 2:** ~18 giờ | **Deadline:** 10/04/2026

---

### Phase 3 — Agent 3: Analyst 🟡 ĐANG LÀM

> Prompts đã xong. Cần viết rule-based logic, LLM pipeline 4 bước, orchestrator.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| ✅ Prompt: diễn giải kỹ thuật | `prompts/technical_interpret.txt` | 1h | ✅ |
| ✅ Prompt: sentiment tin tức | `prompts/news_sentiment.txt` | 1h | ✅ |
| ✅ Prompt: tác động cổ tức | `prompts/dividend_impact.txt` | 1h | ✅ |
| ✅ Prompt: phân loại nguyên nhân | `prompts/cause_classify.txt` | 1h | ✅ |
| ✅ Prompt: tổng hợp thị trường | `prompts/market_summary.txt` | 1h | ✅ |
| Rule-based: tính tín hiệu kỹ thuật | `ta_rules.py` | 2h | ⬜ |
| ✅ LLM caller với prompt loader | `llm_caller.py` | 1h | ✅ |
| Orchestrator chạy 4 skills tuần tự | `main.py` | 3h | ⬜ |
| Parser JSON response từ Claude | `response_parser.py` | 1.5h | ⬜ |
| `Dockerfile` + `requirements.txt` | — | 30m | ⬜ |
| Test pipeline đầy đủ cho 5 mã | — | 2h | ⬜ |
| Tinh chỉnh prompt dựa trên kết quả test | `prompts/*.txt` | 2h | ⬜ |

**Tổng Phase 3:** ~18 giờ | **Deadline:** 17/04/2026

---

### Phase 4 — Agent 4: Reporter 🟡 ĐANG LÀM

> Prompts đã xong. Cần viết PDF generator, history logger, và save alerts cho dashboard.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| ✅ Prompt: mở đầu báo cáo | `prompts/report_narrative.txt` | 1h | ✅ |
| ✅ Prompt: mục từng mã nổi bật | `prompts/stock_highlight.txt` | 1h | ✅ |
| ✅ Prompt: soạn thông báo alert | `prompts/alert_message.txt` | 1h | ✅ |
| ✅ Prompt: tổng hợp tuần | `prompts/weekly_digest.txt` | 1h | ✅ |
| ✅ LLM caller | `llm_caller.py` | 30m | ✅ |
| PDF generator với template | `pdf_generator.py` | 3h | ⬜ |
| History logger → SQLite | `history_logger.py` | 2h | ⬜ |
| Alert writer → JSON file | `alert_writer.py` | 1h | ⬜ |
| Markdown report writer | `md_writer.py` | 1h | ⬜ |
| Entry point `main.py` | `main.py` | 1.5h | ⬜ |
| Schema SQLite (`history.sqlite`) | `schema.sql` | 1h | ⬜ |
| `Dockerfile` + `requirements.txt` | — | 30m | ⬜ |
| Test xuất báo cáo 1 ngày hoàn chỉnh | — | 2h | ⬜ |

**Tổng Phase 4:** ~17 giờ | **Deadline:** 22/04/2026

---

### Phase 5 — Streamlit Dashboard 🟡 ĐANG LÀM

> 4 trang đã có skeleton. Cần kết nối dữ liệu thực và hoàn thiện UI.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| ✅ `app.py` entry point | `dashboard/app.py` | 30m | ✅ |
| ✅ Page 1: Feed báo cáo + alerts | `pages/01_feed.py` | 2h | ✅ |
| ✅ Page 2: Article + PDF viewer | `pages/02_article.py` | 2h | ✅ |
| ✅ Page 3: Bảng alert có filter | `pages/03_alerts.py` | 1.5h | ✅ |
| ✅ Page 4: Lịch sử + Plotly | `pages/04_history.py` | 2h | ✅ |
| Kết nối dữ liệu thực (test với mock data) | — | 2h | ⬜ |
| Candlestick chart (thay line chart) | `pages/04_history.py` | 2h | ⬜ |
| Component: stock_chart.py | `components/stock_chart.py` | 1.5h | ⬜ |
| Component: alert_table.py | `components/alert_table.py` | 1h | ⬜ |
| `Dockerfile` + `requirements.txt` | — | 30m | ⬜ |
| Test giao diện end-to-end | — | 2h | ⬜ |

**Tổng Phase 5:** ~17 giờ | **Deadline:** 26/04/2026

---

### Phase 6 — Airflow & Docker 🟡 ĐANG LÀM

> DAG skeleton đã xong. Cần Dockerfiles, bổ sung error handling và monitoring.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| ✅ Airflow DAG chính | `airflow/dags/market_intelligence_dag.py` | 2h | ✅ |
| ✅ `docker-compose.yml` skeleton | `docker-compose.yml` | 1h | ✅ |
| `Dockerfile` Agent 1 | `agent1_crawler/Dockerfile` | 30m | ⬜ |
| `Dockerfile` Agent 2 | `agent2_financial_reader/Dockerfile` | 30m | ⬜ |
| `Dockerfile` Agent 3 | `agent3_analyst/Dockerfile` | 30m | ⬜ |
| `Dockerfile` Agent 4 | `agent4_reporter/Dockerfile` | 30m | ⬜ |
| `Dockerfile` Dashboard | `dashboard/Dockerfile` | 30m | ⬜ |
| `requirements.txt` từng agent | `*/requirements.txt` | 1h | ⬜ |
| Test `docker compose up` end-to-end | — | 2h | ⬜ |
| Bổ sung error notification trong DAG | `airflow/dags/*.py` | 1h | ⬜ |
| Test trigger DAG thủ công | — | 1h | ⬜ |

**Tổng Phase 6:** ~11 giờ | **Deadline:** 29/04/2026

---

### Phase 7 — Integration Testing ⬜ CHƯA BẮT ĐẦU

> Chạy pipeline end-to-end, so sánh kết quả phân tích với thực tế thị trường.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| Test Agent 1 → Agent 2 data flow | — | 2h | ⬜ |
| Test Agent 2 → Agent 3 data flow | — | 2h | ⬜ |
| Test Agent 3 → Agent 4 data flow | — | 2h | ⬜ |
| Chạy pipeline đầy đủ 1 ngày (backtest) | — | 3h | ⬜ |
| Đánh giá chất lượng phân tích 5 ngày | — | 3h | ⬜ |
| Tinh chỉnh prompts dựa trên kết quả | `*/prompts/*.txt` | 3h | ⬜ |
| Kiểm tra Streamlit hiển thị đúng | — | 2h | ⬜ |
| Đo thời gian chạy toàn pipeline | — | 1h | ⬜ |

**Tổng Phase 7:** ~18 giờ | **Deadline:** 06/05/2026

---

### Phase 8 — Production Deployment ⬜ CHƯA BẮT ĐẦU

> Deploy lên server/cloud, kích hoạt Airflow scheduler chạy tự động.

| Task | File | Ước tính | Trạng thái |
|---|---|---|---|
| Chọn môi trường deploy (local server / VPS / GCP) | — | 2h | ⬜ |
| Setup server + Docker | — | 2h | ⬜ |
| `git clone` + `docker compose up` trên server | — | 1h | ⬜ |
| Cấu hình `.env` production | `.env` | 30m | ⬜ |
| Kích hoạt Airflow DAG scheduler | — | 30m | ⬜ |
| Theo dõi pipeline chạy thật ngày đầu tiên | — | 2h | ⬜ |
| Kiểm tra Streamlit truy cập được từ xa | — | 1h | ⬜ |
| Cài đặt backup tự động `storage/` + `reports/` | — | 1h | ⬜ |

**Tổng Phase 8:** ~10 giờ | **Deadline:** 12/05/2026

---

## Tổng quan Timeline

```
Tháng 4/2026
─────────────────────────────────────────────────────────────────────
W1 (01–05/04)  [Phase 0 ✅][Phase 1 ✅]
                Hoàn thiện Dockerfile + requirements.txt Agent 1

W2 (06–10/04)  [Phase 2]
                Agent 2 code: bctc_parse, pdf_reader, ratio_calc, llm_caller

W3 (11–17/04)  [Phase 3]
                Agent 3 code: ta_rules, orchestrator 4 skills, response_parser

W4 (18–22/04)  [Phase 4]
                Agent 4 code: pdf_generator, history_logger, alert_writer

Tháng 5/2026
─────────────────────────────────────────────────────────────────────
W1 (23–26/04)  [Phase 5]
                Dashboard: kết nối dữ liệu thực, candlestick chart

W2 (27–29/04)  [Phase 6]
                Dockerfiles, requirements.txt, test docker compose

W3 (30/04–06/05) [Phase 7]
                Integration testing, đánh giá chất lượng, tinh chỉnh prompts

W4 (07–12/05)  [Phase 8]
                Production deployment, kích hoạt scheduler
```

---

## Kiến trúc Tổng thể (nhắc lại nhanh)

```
Airflow DAG (15:15 ICT)
│
├── Agent 1 (không LLM)        → storage/raw/
│   price_fetch, news_crawl,
│   dividend_fetch, technical_calc, doc_downloader
│
├── Agent 2 (LLM — 4 prompts)  → storage/processed/
│   bctc_parse + pdf_reader + ratio_calc
│   → Claude: bctc_summary, pdf_doc_extract, anomaly_explain, ratio_interpret
│
├── Agent 3 (LLM — 5 prompts)  → storage/processed/
│   ta_rules (rule-based) +
│   → Claude: technical_interpret, news_sentiment, dividend_impact
│   → Claude: cause_classify, market_summary
│
└── Agent 4 (LLM — 4 prompts)  → reports/{date}/ + storage/alerts_{date}.json
    pdf_generator + history_logger + alert_writer
    → Claude: report_narrative, stock_highlight, alert_message
    → Claude: weekly_digest (chỉ thứ Sáu)

Streamlit Dashboard (localhost:8501)
└── Đọc reports/ và storage/ → hiển thị bài báo + PDF viewer + bảng alert
```

---

## Bước tiếp theo ngay bây giờ

**Cho giai đoạn A (demo giữa kỳ):**

1. Cấu hình `.env`: `CLAUDE_API_KEY`, `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, tùy chọn `GEMINI_MODEL`, `DEMO_LLM_PROVIDER`  
2. Cài dependency: `pip install -r requirements.txt`  
3. Chạy một lệnh: `python scripts/demo_midterm.py` (mặc định Gemini + 3 mã VCB,FPT,VIC) — hoặc `--provider deepseek` / `claude`, `--skip-ingest` nếu đã có JSON; **`--sample-data`** nếu Agent 1 / vnstock chưa chạy được (vẫn demo LLM + Streamlit)  
4. Mở dashboard từ thư mục gốc: `streamlit run dashboard/app.py` → trang **Feed báo cáo**  

**Cho giai đoạn B (cuối kỳ):**

1. **Tạo `requirements.txt` + `Dockerfile` cho Agent 1** (đóng Phase 1 về mặt triển khai)  
2. **Viết `bctc_parse.py` và `ratio_calc.py`** cho Agent 2 (không cần LLM trước, dễ test)  
3. **Orchestrator Agent 3 + parser JSON** — nối các prompt đã có thành pipeline  
4. **Agent 4:** `history_logger`, `alert_writer`, schema SQLite — để dashboard và báo cáo đồng bộ  
5. **Docker Compose end-to-end + Phase 7–8** theo timeline tổng  

---

*File này được cập nhật theo tiến độ dự án.*
