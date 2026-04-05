# VN Market Intelligence — Hệ thống Phân tích Biến động Chứng khoán Việt Nam

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![vnstock](https://img.shields.io/badge/vnstock-3.x-green.svg)](https://github.com/thinh-vu/vnstock)
[![Claude API](https://img.shields.io/badge/Claude-API-orange.svg)](https://www.anthropic.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Local_DB-blue.svg)](https://www.sqlite.org/)
[![Apache Airflow](https://img.shields.io/badge/Airflow-2.x-017CEE.svg)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)

Hệ thống **multi-agent tự động** phân tích biến động thị trường chứng khoán Việt Nam hàng ngày — thu thập giá cổ phiếu HOSE/HNX, đọc tài liệu PDF và BCTC, phân tích nguyên nhân bằng LLM với **prompt templates riêng cho từng nhiệm vụ**, và xuất báo cáo lên **Streamlit Dashboard** dưới dạng bài báo kèm PDF viewer. Toàn bộ pipeline được điều phối bởi **Apache Airflow** và đóng gói bằng **Docker**.

---

## Mục lục

- [Tổng quan](#tổng-quan)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Thiết kế Skills cho từng Agent](#thiết-kế-skills-cho-từng-agent)
- [Data Ingestion — Airflow & Docker](#data-ingestion--airflow--docker)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
- [Chạy từng Agent](#chạy-từng-agent)
- [Nguồn dữ liệu](#nguồn-dữ-liệu)
- [Đầu ra & Web News Portal](#đầu-ra--web-news-portal)
- [Monitoring & Alert](#monitoring--alert)

---

## Tổng quan

Project này xây dựng pipeline tự động gồm **4 AI Agents chuyên biệt**, mỗi agent được trang bị **bộ skills riêng** phù hợp với nhiệm vụ của mình. Toàn bộ pipeline chạy hàng ngày sau khi phiên giao dịch đóng cửa (15:00 ICT), được điều phối bởi **Apache Airflow** và đóng gói trong **Docker**:

| Vấn đề hiện tại | Giải pháp |
|---|---|
| Phải xem giá thủ công trên nhiều trang | Agent 1 tự động kéo giá, tài liệu, BCTC qua Airflow DAG |
| Mất hàng giờ đọc tài liệu và BCTC rải rác | Agent 2 đọc & phân tích BCTC, parse PDF tài liệu tự động |
| Không biết biến động do kỹ thuật hay tin tức | Agent 3 phân loại nguyên nhân với skills LLM chuyên biệt |
| Không có nơi xem báo cáo tổng hợp trực quan | Agent 4 xuất báo cáo PDF + đăng lên **Web News Portal** |

**Thị trường được hỗ trợ:** HOSE · HNX · UPCOM  
**Danh sách theo dõi:** Tùy chỉnh (mặc định: VN30 + các mã tự chọn)  
**Lịch chạy:** Tự động sau 15:00 ICT mỗi ngày giao dịch (Airflow DAG)  
**Xem kết quả:** Streamlit Dashboard — báo cáo PDF hiển thị dưới dạng bài báo, kèm bảng alert động

---

## Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────────────────────┐
│               VN Market Intelligence System  (Docker Compose)                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ╔══════════════════════════════════════════════════════════════════╗        │
│   ║          Apache Airflow — DAG Orchestrator (15:15 ICT)          ║        │
│   ╚══════════╤═══════════════╤══════════════╤═══════════════════════╝        │
│              │               │              │                                │
│              ▼               ▼              ▼                                │
│  ┌───────────────────┐  ┌──────────────────────┐                            │
│  │  [Docker] Agent 1 │  │  [Docker] Agent 2    │                            │
│  │  Data Ingestion   │  │  Financial Reader    │                            │
│  ├───────────────────┤  ├──────────────────────┤                            │
│  │ Skills riêng:     │  │ Skills riêng:        │                            │
│  │ • price_fetch     │  │ • bctc_parse         │                            │
│  │ • news_crawl      │──▶ • pdf_doc_reader     │                            │
│  │ • dividend_fetch  │  │ • ratio_calculator   │                            │
│  │ • technical_calc  │  │ • quarter_comparator │                            │
│  │ • doc_downloader  │  │ • anomaly_detector   │                            │
│  └───────────────────┘  └──────────┬───────────┘                            │
│           │                        │                                         │
│           └────────────┬───────────┘                                         │
│                        ▼                                                     │
│             ┌──────────────────────┐                                         │
│             │    Staging Layer     │                                         │
│             │  SQLite + JSON/PDF   │                                         │
│             │  (Shared Volume)     │                                         │
│             └──────────┬───────────┘                                         │
│                        │                                                     │
│          ┌─────────────┼─────────────┐                                       │
│          ▼             ▼             ▼                                       │
│  ┌─────────────┐ ┌───────────┐ ┌───────────┐                                │
│  │[Docker]     │ │[Docker]   │ │[Docker]   │                                │
│  │ Agent 3     │ │ Agent 3   │ │ Agent 3   │                                │
│  │ (Kỹ thuật)  │ │ (Tin tức) │ │ (Cổ tức)  │                               │
│  │ Skills:     │ │ Skills:   │ │ Skills:   │                                │
│  │ • ta_skill  │ │ • sentiment│ │ •dividend │                               │
│  │ • pattern   │ │ • llm_call │ │  _impact  │                               │
│  └──────┬──────┘ └─────┬─────┘ └─────┬─────┘                               │
│         └──────────────┼─────────────┘                                      │
│                        ▼                                                     │
│             ┌──────────────────────┐                                         │
│             │  [Docker] Agent 4   │                                         │
│             │  Report Writer      │                                         │
│             ├──────────────────────┤                                         │
│             │ Skills riêng:       │                                         │
│             │ • pdf_generator     │                                         │
│             │ • news_publisher    │                                         │
│             │ • history_logger    │                                         │
│             └──────────┬───────────┘                                         │
│                        │                                                     │
│          ┌─────────────┴─────────────┐                                       │
│          ▼                           ▼                                       │
│  ┌───────────────┐       ┌───────────────────────┐                          │
│  │  SQLite DB    │       │  Streamlit Dashboard  │                          │
│  │  (Lịch sử)   │       │  (localhost:8501)     │                          │
│  └───────────────┘       ├───────────────────────┤                          │
│                          │ • Feed bài báo + Alert │                          │
│                          │ • PDF viewer inline    │                          │
│                          │ • Biểu đồ giá động     │                          │
│                          │ • http://localhost:8501│                          │
│                          └───────────────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Thiết kế Skills cho từng Agent

**Skills = Prompt templates** — mỗi skill là một file `.txt` định nghĩa rõ nhiệm vụ, ngữ cảnh đầu vào và định dạng đầu ra cho LLM. Agent nạp đúng template, điền biến, rồi gọi Claude API. Nhờ vậy có thể chỉnh hành vi của từng agent mà **không cần sửa code** — chỉ cần chỉnh file prompt.

> **Agent 1** (thu thập dữ liệu) không dùng LLM → không có prompt templates, chỉ có Python modules.  
> **Agent 2, 3, 4** (đọc tài liệu, phân tích, báo cáo) đều dùng LLM → mỗi agent có thư mục `prompts/` riêng.

---

### Agent 2 — Financial Reader Prompts

Agent 2 dùng LLM để **diễn giải nội dung BCTC và tài liệu PDF**, không phải tính toán (tính toán đã làm bằng pandas). Mỗi prompt hướng LLM vào một loại tài liệu cụ thể:

| Skill (Prompt) | File | LLM được yêu cầu làm gì |
|---|---|---|
| `bctc_summary` | `prompts/bctc_summary.txt` | Tóm tắt kết quả kinh doanh quý, nhận xét xu hướng so kỳ trước |
| `pdf_doc_extract` | `prompts/pdf_doc_extract.txt` | Trích xuất thông tin quan trọng từ văn bản công bố thông tin PDF |
| `anomaly_explain` | `prompts/anomaly_explain.txt` | Giải thích tại sao chỉ số tài chính thay đổi bất thường |
| `ratio_interpret` | `prompts/ratio_interpret.txt` | Nhận định ý nghĩa của EPS/ROE/D/E trong bối cảnh ngành |

**Ví dụ `prompts/bctc_summary.txt`:**

```
Bạn là chuyên gia phân tích tài chính doanh nghiệp Việt Nam.

Dưới đây là dữ liệu BCTC của {ticker} — Quý {quarter}/{year}:

Kết quả kinh doanh:
- Doanh thu thuần: {revenue:,} tỷ VND ({revenue_change:+.1f}% so Q{prev_quarter})
- Lợi nhuận gộp: {gross_profit:,} tỷ VND | Biên gộp: {gross_margin:.1f}%
- LNST: {net_profit:,} tỷ VND ({net_change:+.1f}% so Q{prev_quarter})
- EPS: {eps:,} đồng/cp

Cân đối kế toán:
- Tổng tài sản: {total_assets:,} tỷ | Nợ/Vốn (D/E): {de_ratio:.2f}
- Tiền & tương đương tiền: {cash:,} tỷ

Hãy viết nhận xét ngắn gọn (4–6 câu) theo cấu trúc:
1. Kết quả kinh doanh quý này tốt hay xấu so kỳ trước?
2. Yếu tố nào đóng góp chính vào sự thay đổi?
3. Sức khỏe tài chính (thanh khoản, nợ) có đáng lo không?
4. Điểm cần chú ý cho nhà đầu tư.

Trả lời bằng tiếng Việt, ngắn gọn, không dùng thuật ngữ phức tạp.
```

---

### Agent 3 — Analyst Prompts

Agent 3 là agent phân tích nặng nhất — mỗi prompt tương ứng một **góc nhìn phân tích khác nhau**, được gọi tuần tự trước khi tổng hợp nguyên nhân:

| Skill (Prompt) | File | LLM được yêu cầu làm gì |
|---|---|---|
| `technical_interpret` | `prompts/technical_interpret.txt` | Giải thích tín hiệu kỹ thuật (RSI, MA cross, volume) bằng ngôn ngữ tự nhiên |
| `news_sentiment` | `prompts/news_sentiment.txt` | Phân loại cảm xúc + mức độ tác động của từng tin tức đến giá |
| `dividend_impact` | `prompts/dividend_impact.txt` | Đánh giá mức độ điều chỉnh giá do cổ tức/quyền mua có hợp lý không |
| `cause_classify` | `prompts/cause_classify.txt` | Tổng hợp tất cả tín hiệu → phân loại nguyên nhân chính xác nhất |
| `market_summary` | `prompts/market_summary.txt` | Tổng hợp toàn thị trường: tâm lý, dòng tiền, nhóm ngành nổi bật |

**Ví dụ `prompts/news_sentiment.txt`:**

```
Bạn là chuyên gia phân tích tin tức thị trường chứng khoán Việt Nam.

Cổ phiếu: {ticker} | Biến động hôm nay: {price_change:+.1f}%

Các tin tức liên quan trong 24 giờ qua:
{news_list}

Với mỗi tin, hãy đánh giá theo JSON:
{{
  "headline": "...",
  "sentiment": "positive | negative | neutral",
  "impact_level": "high | medium | low",
  "reason": "giải thích ngắn tại sao tin này tác động đến giá"
}}

Sau đó kết luận:
- Tổng quan cảm xúc tin tức: Tích cực / Tiêu cực / Trung lập
- Tin nào có khả năng là nguyên nhân chính của biến động hôm nay?
```

**Ví dụ `prompts/cause_classify.txt`:**

```
Bạn là chuyên gia phân tích nguyên nhân biến động cổ phiếu.

Cổ phiếu: {ticker} | Ngày: {date} | Biến động: {price_change:+.1f}%

Kết quả phân tích từng góc độ:
[KỸ THUẬT] {technical_result}
[TIN TỨC]  {news_result}
[CỔ TỨC]   {dividend_result}
[THỊ TRƯỜNG] VN-Index {index_change:+.1f}% | Thanh khoản: {liquidity}

Dựa trên tổng hợp trên, hãy:
1. Xác định nguyên nhân CHÍNH: Kỹ thuật / Tin tức / Cổ tức / Thị trường chung / Không xác định
2. Mức độ tin cậy của kết luận: Cao / Trung bình / Thấp
3. Mô tả ngắn 2–3 câu cho báo cáo cuối ngày.

Trả lời theo JSON:
{{"cause": "...", "confidence": "...", "summary": "..."}}
```

---

### Agent 4 — Reporter Prompts

Agent 4 dùng LLM để **viết nội dung báo cáo** và **soạn thông báo alert**:

| Skill (Prompt) | File | LLM được yêu cầu làm gì |
|---|---|---|
| `report_narrative` | `prompts/report_narrative.txt` | Viết phần mở đầu báo cáo cuối ngày theo phong cách bài báo tài chính |
| `stock_highlight` | `prompts/stock_highlight.txt` | Viết mục "biến động đáng chú ý" cho từng mã có kết quả phân tích |
| `alert_message` | `prompts/alert_message.txt` | Soạn thông báo alert ngắn gọn hiển thị trên Streamlit dashboard |
| `weekly_digest` | `prompts/weekly_digest.txt` | Tổng hợp tuần — tóm tắt xu hướng nổi bật từ 5 báo cáo ngày |

---

## Data Ingestion — Airflow & Docker

### Tại sao dùng Airflow?

Toàn bộ quá trình kéo dữ liệu (giá cổ phiếu → tài liệu PDF → BCTC) được điều phối bởi **Apache Airflow** để đảm bảo:
- **Thứ tự chạy đúng**: Agent 1 phải hoàn thành trước khi Agent 2 bắt đầu đọc tài liệu
- **Retry tự động**: Nếu API vnstock hoặc HOSE timeout, Airflow tự thử lại
- **Monitoring**: Theo dõi từng task qua giao diện Airflow Web UI
- **Lịch chạy linh hoạt**: Cron `15 15 * * 1-5` (15:15 ICT, thứ Hai–Sáu)

### DAG Pipeline

```
market_intelligence_dag (chạy mỗi ngày giao dịch lúc 15:15 ICT)
│
├── [Task] fetch_prices          ← Agent 1: price_fetch_skill
│       ↓
├── [Task] fetch_news            ← Agent 1: news_crawl_skill
│       ↓
├── [Task] fetch_dividends       ← Agent 1: dividend_fetch_skill
│       ↓
├── [Task] download_docs         ← Agent 1: doc_downloader_skill
│       ↓
├── [Task] calc_technicals       ← Agent 1: technical_calc_skill
│       ↓
├── [Task] parse_bctc            ← Agent 2: bctc_parse_skill
│       ↓
├── [Task] read_pdf_docs         ← Agent 2: pdf_doc_reader_skill
│       ↓
├── [Task] calc_ratios           ← Agent 2: ratio_calc_skill + anomaly_detect_skill
│       ↓
├── [Task] run_analysis          ← Agent 3: technical + sentiment + cause_classify
│       ↓
└── [Task] generate_report       ← Agent 4: pdf_generate + news_publish + alert_push
```

```python
# airflow/dags/market_intelligence_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "vn-market-intel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="market_intelligence_dag",
    default_args=default_args,
    schedule_interval="15 15 * * 1-5",   # 15:15 ICT, thứ Hai–Sáu
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stock", "ai-agent"],
) as dag:

    t1 = PythonOperator(task_id="fetch_prices",    python_callable=run_agent1_prices)
    t2 = PythonOperator(task_id="fetch_news",      python_callable=run_agent1_news)
    t3 = PythonOperator(task_id="download_docs",   python_callable=run_agent1_docs)
    t4 = PythonOperator(task_id="parse_bctc",      python_callable=run_agent2_bctc)
    t5 = PythonOperator(task_id="read_pdf_docs",   python_callable=run_agent2_pdf)
    t6 = PythonOperator(task_id="run_analysis",    python_callable=run_agent3)
    t7 = PythonOperator(task_id="generate_report", python_callable=run_agent4)

    [t1, t2, t3] >> t4 >> t5 >> t6 >> t7
```

### Tại sao dùng Docker?

Mỗi agent chạy trong **Docker container riêng biệt** để:
- Cô lập dependencies (tránh xung đột thư viện)
- Dễ deploy lên server hoặc cloud (GCP Cloud Run, AWS ECS...)
- Scale từng agent độc lập khi cần

```yaml
# docker-compose.yml
version: "3.9"
services:
  airflow:
    image: apache/airflow:2.9.0
    ports: ["8081:8080"]
    volumes:
      - ./airflow/dags:/opt/airflow/dags
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor

  agent1:
    build: ./agent1_crawler
    volumes:
      - ./storage:/app/storage
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}

  agent2:
    build: ./agent2_financial_reader
    volumes:
      - ./storage:/app/storage

  agent3:
    build: ./agent3_analyst
    volumes:
      - ./storage:/app/storage
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}

  agent4:
    build: ./agent4_reporter
    volumes:
      - ./storage:/app/storage
      - ./reports:/app/reports

  dashboard:
    build: ./dashboard
    ports: ["8501:8501"]
    volumes:
      - ./reports:/app/reports
      - ./storage:/app/storage
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

---

## Cấu trúc thư mục

```
vn-market-intelligence/
│
├── agent1_crawler/                  # [Docker] Agent thu thập dữ liệu (không dùng LLM)
│   ├── main.py                      # Entry point — gọi các modules tuần tự
│   ├── price_fetch.py               # Kéo giá OHLCV qua vnstock
│   ├── news_crawl.py                # Cào tin CafeF RSS + vnstock news
│   ├── dividend_fetch.py            # Lấy lịch cổ tức, ngày GDKHQ
│   ├── technical_calc.py            # Tính MA/RSI/MACD từ lịch sử giá
│   ├── doc_downloader.py            # Tải PDF tài liệu từ HOSE/SSI
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent2_financial_reader/         # [Docker] Agent đọc tài liệu & BCTC (có LLM)
│   ├── main.py
│   ├── bctc_parse.py                # Lấy & parse BCTC quý từ vnstock (IS, BS, CF)
│   ├── pdf_doc_reader.py            # Đọc nội dung PDF bằng pdfplumber
│   ├── ratio_calc.py                # Tính EPS, P/E, ROE, D/E (pandas)
│   ├── llm_caller.py                # Wrapper gọi Claude API dùng chung
│   ├── prompts/                     # ← Bộ Skills: prompt templates của Agent 2
│   │   ├── bctc_summary.txt         # Skill: Tóm tắt & nhận xét kết quả kinh doanh
│   │   ├── pdf_doc_extract.txt      # Skill: Trích xuất thông tin từ PDF tài liệu
│   │   ├── anomaly_explain.txt      # Skill: Giải thích chỉ số tài chính bất thường
│   │   └── ratio_interpret.txt      # Skill: Nhận định EPS/ROE/D/E theo ngữ cảnh ngành
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent3_analyst/                  # [Docker] Agent phân tích nguyên nhân (LLM nặng)
│   ├── main.py
│   ├── ta_rules.py                  # Rule-based: tính signal kỹ thuật (không LLM)
│   ├── llm_caller.py                # Wrapper gọi Claude API dùng chung
│   ├── prompts/                     # ← Bộ Skills: prompt templates của Agent 3
│   │   ├── technical_interpret.txt  # Skill: Giải thích tín hiệu RSI/MA/volume
│   │   ├── news_sentiment.txt       # Skill: Phân loại cảm xúc & tác động tin tức
│   │   ├── dividend_impact.txt      # Skill: Đánh giá điều chỉnh giá do cổ tức
│   │   ├── cause_classify.txt       # Skill: Tổng hợp → phân loại nguyên nhân chính
│   │   └── market_summary.txt       # Skill: Tổng hợp toàn thị trường cuối ngày
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent4_reporter/                 # [Docker] Agent xuất báo cáo & ghi lên dashboard
│   ├── main.py
│   ├── pdf_generator.py             # Tạo báo cáo PDF từ template (fpdf2)
│   ├── history_logger.py            # Lưu kết quả vào SQLite
│   ├── llm_caller.py                # Wrapper gọi Claude API dùng chung
│   ├── prompts/                     # ← Bộ Skills: prompt templates của Agent 4
│   │   ├── report_narrative.txt     # Skill: Viết mở đầu báo cáo dạng bài báo tài chính
│   │   ├── stock_highlight.txt      # Skill: Viết mục "biến động đáng chú ý" từng mã
│   │   ├── alert_message.txt        # Skill: Soạn thông báo alert ngắn cho dashboard
│   │   └── weekly_digest.txt        # Skill: Tổng hợp xu hướng nổi bật cả tuần
│   ├── Dockerfile
│   └── requirements.txt
│
├── dashboard/                       # [Docker] Streamlit Dashboard
│   ├── app.py                       # Entry point — multi-page Streamlit app
│   ├── pages/
│   │   ├── 01_feed.py               # Trang chủ: feed báo cáo theo ngày + alert
│   │   ├── 02_article.py            # Xem bài báo chi tiết + PDF viewer inline
│   │   ├── 03_alerts.py             # Bảng thông báo biến động lớn (có filter)
│   │   └── 04_history.py            # Lịch sử phân tích 30/60/90 ngày
│   ├── components/
│   │   ├── pdf_viewer.py            # Component hiển thị PDF trong trang Streamlit
│   │   ├── stock_chart.py           # Biểu đồ nến + volume (Plotly)
│   │   └── alert_table.py           # Bảng alert có màu theo mức độ
│   ├── Dockerfile
│   └── requirements.txt
│
├── airflow/                         # Apache Airflow orchestration
│   ├── dags/
│   │   └── market_intelligence_dag.py   # DAG chính — chạy 15:15 ICT mỗi ngày GD
│   └── plugins/                    # Custom Airflow plugins (nếu cần)
│
├── storage/                         # Shared volume — dữ liệu dùng chung giữa agents
│   ├── raw/                         # Dữ liệu thô từ Agent 1 & 2
│   │   ├── prices_{date}.json
│   │   ├── news_{date}.json
│   │   ├── docs_{ticker}_{date}.pdf # PDF tài liệu gốc đã tải
│   │   └── bctc_{ticker}_{quarter}.json
│   ├── processed/                   # Kết quả phân tích từ Agent 3
│   │   └── analysis_{date}.json
│   └── history.sqlite               # Toàn bộ lịch sử theo ngày
│
├── reports/                         # Báo cáo PDF xuất ra (shared với news_portal)
│   └── {date}/
│       ├── market_report_{date}.pdf
│       └── market_report_{date}.md
│
├── config/
│   ├── settings.yaml                # Cấu hình chung (API keys, ngưỡng cảnh báo)
│   └── watchlist.yaml               # Danh sách mã theo dõi
│
├── notebooks/                       # Jupyter notebooks thử nghiệm
│   ├── 01_vnstock_demo.ipynb
│   ├── 02_technical_analysis.ipynb
│   └── 03_llm_analysis_demo.ipynb
│
├── docker-compose.yml               # Khởi động toàn bộ hệ thống
├── .env                             # API keys (không commit)
├── requirements.txt                 # Tổng hợp dependencies
└── README.md
```

---

## Yêu cầu hệ thống

### Phần cứng
- **RAM:** 8GB tối thiểu (16GB khuyến nghị khi chạy Airflow + Docker)
- **Storage:** 10GB+ (tùy theo lịch sử lưu trữ và PDF tài liệu)
- **OS:** Windows / macOS / Linux

### Phần mềm
- **Docker Desktop** 24.x+ (bắt buộc — chạy toàn bộ hệ thống)
- **Docker Compose** v2.x+
- **Python:** 3.10+ (chỉ cần nếu chạy local không dùng Docker)
- **Claude API Key** (dùng cho Agent 3 — phân tích nguyên nhân)

### Chi phí ước tính
| Thành phần | Chi phí |
|---|---|
| vnstock (dữ liệu giá, BCTC, tài liệu) | Miễn phí |
| CafeF RSS (tin tức) | Miễn phí |
| PDF tài liệu từ HOSE/SSI | Miễn phí |
| Claude API (Agent 3 phân tích) | ~$0.01–0.05 / ngày |
| Apache Airflow (self-hosted Docker) | Miễn phí |
| Web News Portal (self-hosted Docker) | Miễn phí |
| Hosting server (nếu muốn truy cập từ xa) | ~$5–10/tháng (VPS nhỏ) hoặc chạy local |

---

## Hướng dẫn cài đặt

### 1. Clone repository

```bash
git clone https://github.com/your-username/vn-market-intelligence.git
cd vn-market-intelligence
```

### 2. Cấu hình biến môi trường

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
CLAUDE_API_KEY=sk-ant-...
NEWS_PORTAL_SECRET=your-secret-key
AIRFLOW_UID=50000
```

### 3. Khởi động toàn bộ hệ thống bằng Docker Compose

```bash
# Build và khởi động tất cả services
docker compose up -d --build

# Kiểm tra trạng thái
docker compose ps
```

Sau khi khởi động:
- **Airflow Web UI:** http://localhost:8081 (admin / admin)
- **Streamlit Dashboard:** http://localhost:8501

### 4. Cài đặt thư viện (nếu chạy local, không dùng Docker)

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

**Biến môi trường vnstock (tùy chọn):** Sao chép `.env.example` → `.env` và điền `VNSTOCK_API_KEY` nếu có (hạn mức / tính năng ecosystem — không commit giá trị thật). Agent 1 đọc key khi thu thập tin qua `vnstock`. Tài liệu tham chiếu: [Mẫu chương trình cập nhật tin tức (Vnstock News)](https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc), `instructions.md` (hệ sinh thái vnstock), `agent1_crawler/AGENT_SKILLS_NEWS.md` (quy tắc map `summary` ← `short_description`).

Các thư viện chính:

```
vnstock>=3.2.0          # Dữ liệu chứng khoán Việt Nam
pandas>=2.0.0           # Xử lý dữ liệu
pandas-ta>=0.3.14b      # Chỉ số kỹ thuật (RSI, MACD, MA...)
anthropic>=0.20.0       # Claude API (Agent 2/3/4 — gọi LLM)
feedparser>=6.0.0       # Đọc RSS CafeF
pdfplumber>=0.10.0      # Đọc nội dung PDF tài liệu (Agent 2)
fpdf2>=2.7.0            # Xuất báo cáo PDF (Agent 4)
streamlit>=1.35.0       # Dashboard web động
plotly>=5.20.0          # Biểu đồ nến + volume trên Streamlit
apache-airflow>=2.9.0   # Orchestration (chạy qua Docker)
```

### 5. Cấu hình

Tạo file `config/settings.yaml`:

```yaml
# API Keys
claude_api_key: "${CLAUDE_API_KEY}"

# Thị trường
market:
  exchanges: ["HOSE", "HNX"]
  session_close: "15:00"
  timezone: "Asia/Ho_Chi_Minh"

# Ngưỡng cảnh báo biến động
thresholds:
  price_change_alert: 5.0      # % biến động để flag
  volume_spike_multiplier: 2.0 # Khối lượng gấp X lần TB20
  rsi_overbought: 70
  rsi_oversold: 30

# Lưu trữ
storage:
  raw_data_path: "storage/raw/"
  processed_path: "storage/processed/"
  db_path: "storage/history.sqlite"
  report_path: "reports/"

# Streamlit Dashboard
dashboard:
  base_url: "http://localhost:8501"
  reports_path: "reports/"
```

Tạo file `config/watchlist.yaml`:

```yaml
# Danh sách mã cổ phiếu theo dõi
watchlist:
  vn30:
    - VCB    # Vietcombank
    - VIC    # Vingroup
    - VHM    # Vinhomes
    - FPT    # FPT Corp
    - MWG    # Thế Giới Di Động
    - TCB    # Techcombank
    - HPG    # Hòa Phát
    - MSN    # Masan Group

  custom:
    - VNM    # Vinamilk
    - DGC    # Hóa chất Đức Giang
    - PNJ    # Phú Nhuận Jewelry

# Chỉ số thị trường
indices:
  - VNINDEX
  - VN30
  - HNX-INDEX
  - UPCOM-INDEX
```

---

## Chạy từng Agent

### Agent 1 — Data Ingestion (Thu thập dữ liệu + Tài liệu)

Agent 1 **không dùng LLM** — chỉ gồm các Python modules thu thập dữ liệu. Airflow gọi từng module theo thứ tự:

```bash
# Chạy qua Docker (production)
docker compose run --rm agent1 python main.py --date today

# Chạy từng module riêng lẻ (để test/debug)
cd agent1_crawler
python price_fetch.py --date today
# [✓] VCB: 89,500 VND (+1.2%) | KL: 2,340,000 (2.1x TB20)
# [✓] Lưu → storage/raw/prices_2024-01-15.json

python news_crawl.py --date today
# [✓] 47 tin tức → storage/raw/news_2024-01-15.json (thư mục gốc dự án; song song resources/news/)

python doc_downloader.py --tickers VCB,FPT --date today
# [✓] Tải 3 file PDF → storage/raw/docs/

python technical_calc.py --period 60
# [✓] Tính MA20/50, RSI(14), MACD cho toàn bộ watchlist
```

**Ví dụ `doc_downloader.py`:**

```python
import requests, pdfplumber

def download_docs(ticker: str, date: str, save_dir: str) -> list:
    """Tải PDF công bố thông tin từ SSI/HOSE vào storage/raw/docs/"""
    docs = fetch_document_list(ticker, date)   # gọi API SSI
    saved = []
    for doc in docs:
        path = f"{save_dir}/{ticker}_{doc['date']}_{doc['type']}.pdf"
        with open(path, 'wb') as f:
            f.write(requests.get(doc['url']).content)
        saved.append(path)
    return saved
```

---

### Agent 2 — Financial Reader (Đọc BCTC + Prompt Skills)

Agent 2 làm 2 việc: (1) **tính toán chỉ số** bằng pandas, (2) **diễn giải bằng LLM** dùng prompt templates. Mỗi prompt trong `prompts/` là một "skill" độc lập:

```bash
docker compose run --rm agent2 python main.py --date today
```

**Luồng xử lý bên trong:**

```python
# agent2_financial_reader/main.py
from bctc_parse import fetch_bctc
from pdf_doc_reader import read_pdf
from ratio_calc import calc_ratios
from llm_caller import call_claude

def run(ticker, date):
    # Bước 1: Lấy & tính toán (pandas, không LLM)
    bctc = fetch_bctc(ticker)
    ratios = calc_ratios(bctc)
    pdf_text = read_pdf(f"storage/raw/docs/{ticker}_{date}.pdf")

    # Bước 2: Diễn giải bằng LLM — nạp đúng prompt template (skill)
    summary = call_claude(
        prompt_file="prompts/bctc_summary.txt",
        variables={"ticker": ticker, **ratios}
    )
    doc_insight = call_claude(
        prompt_file="prompts/pdf_doc_extract.txt",
        variables={"ticker": ticker, "doc_text": pdf_text}
    )
    return {"summary": summary, "doc_insight": doc_insight, "ratios": ratios}
```

**Các chỉ số tính bằng pandas (không LLM):**

| Chỉ số | Mô tả | Ngưỡng cảnh báo |
|---|---|---|
| EPS | Lợi nhuận trên mỗi cổ phiếu | Giảm >20% so kỳ trước |
| P/E | Giá / Lợi nhuận | Cao hơn 2x trung bình ngành |
| ROE | Lợi nhuận / Vốn chủ sở hữu | < 10% |
| D/E | Nợ / Vốn chủ sở hữu | > 2.0 |
| Biên lợi nhuận | Net Profit Margin | Giảm >5pp so kỳ trước |

---

### Agent 3 — Analyst (Phân tích nguyên nhân — LLM nặng)

Agent 3 chạy **4 prompt skills liên tiếp** — mỗi prompt nhìn từ một góc độ khác nhau, kết quả được tổng hợp vào `cause_classify.txt`:

```bash
docker compose run --rm agent3 python main.py --date today
```

**Luồng gọi prompt skills:**

```python
# agent3_analyst/main.py
from ta_rules import calc_signals      # rule-based, không LLM
from llm_caller import call_claude

def run(ticker, date, data):
    # Bước 1: Tín hiệu kỹ thuật (rule-based)
    ta_signals = calc_signals(data["ohlcv"])

    # Bước 2: Gọi lần lượt từng skill (prompt template)
    tech_text = call_claude("prompts/technical_interpret.txt",
                            {**ta_signals, "ticker": ticker})

    news_text = call_claude("prompts/news_sentiment.txt",
                            {"ticker": ticker, "news_list": data["news"],
                             "price_change": data["change_pct"]})

    div_text  = call_claude("prompts/dividend_impact.txt",
                            {"ticker": ticker, **data["dividend"]})

    # Bước 3: Tổng hợp tất cả → phân loại nguyên nhân (skill cuối)
    result = call_claude("prompts/cause_classify.txt", {
        "ticker": ticker, "date": date,
        "technical_result": tech_text,
        "news_result": news_text,
        "dividend_result": div_text,
        "index_change": data["index_change"],
    })
    return result   # {"cause": "...", "confidence": "...", "summary": "..."}
```

**Logic phân loại nguyên nhân:**

```
Biến động giá cổ phiếu
        │
        ├── Có sự kiện cổ tức / GDKHQ hôm nay?
        │       └── YES → Nguyên nhân: CỔ TỨC / ĐIỀU CHỈNH GIÁ
        │
        ├── Có tin tức tiêu cực / tích cực được công bố?
        │       └── YES → Nguyên nhân: TIN TỨC (Claude phân tích sentiment)
        │
        ├── RSI quá mua (>70) hoặc quá bán (<30)?
        │       └── YES → Nguyên nhân: KỸ THUẬT (điều chỉnh tự nhiên)
        │
        ├── Toàn thị trường cùng chiều biến động?
        │       └── YES → Nguyên nhân: THỊ TRƯỜNG CHUNG
        │
        └── Không xác định được → Nguyên nhân: CẦN THEO DÕI THÊM
```

**Ví dụ prompt gọi Claude API:**

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

prompt = f"""
Bạn là chuyên gia phân tích chứng khoán Việt Nam.

Dữ liệu cổ phiếu {ticker} ngày {date}:
- Giá đóng cửa: {close_price} VND ({price_change:+.1f}%)
- Khối lượng: {volume:,} cp ({volume_ratio:.1f}x trung bình 20 phiên)
- RSI(14): {rsi:.1f}
- MA20: {ma20:,} | MA50: {ma50:,}

Tin tức liên quan trong ngày:
{news_text}

Hãy phân tích ngắn gọn (3-5 câu):
1. Nguyên nhân chính của biến động hôm nay là gì?
2. Yếu tố kỹ thuật, tin tức, hay yếu tố bên ngoài?
3. Mức độ đáng lo ngại: Bình thường / Cần chú ý / Cảnh báo
"""

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{"role": "user", "content": prompt}]
)
```

---

### Agent 4 — Report Writer (Viết báo cáo bằng Prompt Skills + Streamlit)

Agent 4 dùng prompt skills để **viết nội dung** báo cáo, sau đó tạo PDF và lưu kết quả để Streamlit dashboard đọc hiển thị:

```bash
docker compose run --rm agent4 python main.py --date today
```

**Luồng tạo báo cáo:**

```python
# agent4_reporter/main.py
from pdf_generator import build_pdf
from history_logger import save_to_db
from llm_caller import call_claude

def run(date, analysis_results):
    # Bước 1: Dùng prompt skills để viết nội dung
    intro = call_claude("prompts/report_narrative.txt",
                        {"date": date, "market": analysis_results["market"]})

    highlights = []
    for ticker, result in analysis_results["stocks"].items():
        text = call_claude("prompts/stock_highlight.txt",
                           {"ticker": ticker, **result})
        highlights.append(text)

        # Tạo thông báo alert cho dashboard (nếu biến động lớn)
        if abs(result["change_pct"]) >= 5:
            alert = call_claude("prompts/alert_message.txt",
                                {"ticker": ticker, **result})
            save_alert(date, ticker, alert)   # → storage/alerts_{date}.json

    # Bước 2: Dựng PDF + lưu vào SQLite
    build_pdf(date, intro, highlights, path=f"reports/{date}/")
    save_to_db(date, analysis_results)
    # Dashboard Streamlit tự động đọc reports/ và storage/ để hiển thị
```

---

## Chạy toàn bộ pipeline tự động

Pipeline được điều phối bởi **Apache Airflow**. Sau khi `docker compose up -d`, DAG tự động chạy lúc 15:15 ICT mỗi ngày giao dịch.

```bash
# Kích hoạt DAG trên Airflow UI: http://localhost:8081
# Hoặc trigger thủ công qua CLI:
docker compose exec airflow airflow dags trigger market_intelligence_dag

# Theo dõi tiến trình
docker compose exec airflow airflow dags list-runs -d market_intelligence_dag
```

**Thời gian chạy ước tính mỗi ngày:**

| Task (Airflow) | Agent | Skill sử dụng | Thời gian |
|---|---|---|---|
| fetch_prices + fetch_news | Agent 1 | price_fetch, news_crawl | ~2 phút |
| fetch_dividends + download_docs | Agent 1 | dividend_fetch, doc_downloader | ~3 phút |
| calc_technicals | Agent 1 | technical_calc | ~1 phút |
| parse_bctc + read_pdf_docs | Agent 2 | bctc_parse, pdf_doc_reader | ~4 phút |
| calc_ratios | Agent 2 | ratio_calc, anomaly_detect | ~1 phút |
| run_analysis | Agent 3 | ta_analysis, sentiment, llm_call | ~3 phút |
| generate_report | Agent 4 | pdf_generate, news_publish, alert_push | ~2 phút |
| **Tổng cộng** | | | **~16 phút** |

---

## Nguồn dữ liệu

| Dữ liệu | Nguồn | Thư viện / Phương thức | Chi phí |
|---|---|---|---|
| Giá cổ phiếu HOSE/HNX | SSI / VCI (qua vnstock) | `vnstock` | Miễn phí |
| Giá realtime trong phiên | SSI / VCI | `vnstock` | Miễn phí |
| Lịch sử giá (hàng năm) | SSI / TCBS | `vnstock` | Miễn phí |
| Báo cáo tài chính theo quý | Vietstock / SSI | `vnstock` | Miễn phí |
| Lịch chia cổ tức | SSI | `vnstock` | Miễn phí |
| Tin tức thị trường | CafeF | RSS Feed + `feedparser` | Miễn phí |
| Công bố thông tin DN | SSI | `vnstock` | Miễn phí |
| Phân tích nguyên nhân | Claude API (Anthropic) | `anthropic` | ~$0.01–0.05/ngày |
| Chỉ số kỹ thuật | Tính từ giá lịch sử | `pandas-ta` | Miễn phí |

---

## Đầu ra & Web News Portal

### Cấu trúc báo cáo PDF cuối ngày

```
📄 market_report_2024-01-15.pdf
│
├── 1. Tổng quan thị trường
│   ├── VN-Index: 1,235.6 điểm (-0.8%)
│   ├── HNX-Index: 234.5 điểm (+0.2%)
│   ├── Thanh khoản HOSE: 18,234 tỷ VND
│   └── Tâm lý thị trường: Thận trọng
│
├── 2. Biến động đáng chú ý
│   ├── [TĂNG MẠNH] FPT +4.2%: Do tin tức ký hợp đồng AI mới
│   ├── [GIẢM MẠNH] VHM -3.1%: Điều chỉnh sau chuỗi tăng kỹ thuật
│   └── [ĐIỀU CHỈNH GIÁ] VCB -2.0%: Ngày GDKHQ cổ tức 1,500đ/cp
│
├── 3. Phân tích từng mã
│   ├── VCB: [chi tiết phân tích + trích dẫn từ tài liệu PDF gốc]
│   ├── FPT: [chi tiết phân tích]
│   └── ...
│
├── 4. Lịch sự kiện sắp tới (7 ngày)
│   ├── 2024-01-18: MWG — Ngày ĐKCC cổ tức
│   └── 2024-01-20: HPG — Công bố BCTC Q4/2023
│
└── 5. Khuyến nghị theo dõi
    └── [Tổng hợp từ Claude API]
```

### Streamlit Dashboard — Thay thế Telegram

Thay vì gửi thông báo Telegram, toàn bộ kết quả phân tích được hiển thị trên **Streamlit Dashboard** tại `http://localhost:8501`. Dashboard đọc trực tiếp từ `reports/` và `storage/` — không cần API trung gian.

```bash
# Khởi động (đã bao gồm trong docker compose up)
docker compose up dashboard -d

# Hoặc chạy local khi dev
streamlit run dashboard/app.py
```

**Các trang trong Dashboard:**

| Trang | URL path | Nội dung |
|---|---|---|
| Feed báo cáo | `/` (`01_feed.py`) | Danh sách báo cáo theo ngày + bảng alert có màu mức độ |
| Xem bài báo | `/article` (`02_article.py`) | Nội dung phân tích dạng bài báo + PDF viewer inline |
| Bảng alert | `/alerts` (`03_alerts.py`) | Tất cả mã có biến động lớn, filter theo ngày/mức độ |
| Lịch sử | `/history` (`04_history.py`) | Biểu đồ giá + BCTC theo 30/60/90 ngày |

**Ví dụ `pages/01_feed.py` (Streamlit):**

```python
import streamlit as st
import json, sqlite3
from pathlib import Path

st.set_page_config(page_title="VN Market Intelligence", layout="wide")
st.title("VN Market Intelligence Dashboard")

# Chọn ngày
date = st.date_input("Chọn ngày", value="today")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Báo cáo phân tích")
    report_path = Path(f"reports/{date}/market_report_{date}.md")
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.info("Chưa có báo cáo cho ngày này.")

with col2:
    st.subheader("Thông báo biến động")
    alerts = json.loads(Path(f"storage/alerts_{date}.json").read_text())
    for alert in alerts:
        color = "🔴" if alert["level"] == "high" else ("🟡" if alert["level"] == "medium" else "🔵")
        st.markdown(f"{color} **{alert['ticker']}** {alert['change_pct']:+.1f}%")
        st.caption(alert["reason"])
        st.divider()
```

**Ví dụ `pages/02_article.py` — PDF Viewer inline:**

```python
import streamlit as st
import base64
from pathlib import Path

date = st.query_params.get("date", "")
pdf_path = Path(f"reports/{date}/market_report_{date}.pdf")

if pdf_path.exists():
    # Hiển thị nội dung bài báo (từ LLM, đã lưu .md)
    st.markdown(Path(f"reports/{date}/market_report_{date}.md").read_text())

    st.divider()
    st.subheader("Báo cáo PDF đầy đủ")
    # Embed PDF trực tiếp trong trang Streamlit
    pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{pdf_b64}" '
        f'width="100%" height="800px"></iframe>',
        unsafe_allow_html=True
    )
```

**Giao diện Dashboard (mô tả):**

```
┌─────────────────────────────────────────────────────────────────┐
│  VN Market Intelligence          [Chọn ngày: 15/01/2024]  ▼    │
├──────────────────────────────────┬──────────────────────────────┤
│  📰 BÁO CÁO PHÂN TÍCH HÔM NAY   │  🔔 THÔNG BÁO BIẾN ĐỘNG     │
│                                  │                              │
│  VN-Index giảm nhẹ 0.8% trong   │  🔴 FPT  +4.2%              │
│  phiên giao dịch 15/01/2024 với  │  Ký hợp đồng AI Nhật Bản    │
│  thanh khoản 18,234 tỷ VND...    │  ──────────────────────────  │
│                                  │  🔴 VHM  -3.1%              │
│  ▸ FPT tăng mạnh 4.2% nhờ...     │  RSI 72 — điều chỉnh KT     │
│  ▸ VHM điều chỉnh kỹ thuật...    │  ──────────────────────────  │
│  ▸ VCB ngày GDKHQ cổ tức...      │  🔵 VCB  -2.0%              │
│                                  │  GDKHQ cổ tức 1,500đ/cp     │
│  [Xem báo cáo đầy đủ + PDF ▶]   │                              │
├──────────────────────────────────┴──────────────────────────────┤
│  📄 PDF VIEWER (market_report_2024-01-15.pdf)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   [Nội dung trang 1 PDF hiển thị trực tiếp trong web]   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Monitoring & Alert

### Ngưỡng cảnh báo tự động (Web News Portal)

Thay vì gửi Telegram, toàn bộ alert được hiển thị trên **Web News Portal** tại `http://localhost:8080/alerts`:

| Điều kiện | Mức độ | Hành động trên Portal |
|---|---|---|
| Cổ phiếu tăng/giảm > 5% | 🔴 Cao | Badge đỏ — hiển thị ngay trên feed alert |
| Khối lượng > 3x trung bình 20 phiên | 🟡 Trung bình | Badge vàng — đưa vào bảng thông báo |
| RSI > 75 hoặc < 25 | 🟡 Trung bình | Ghi chú kỹ thuật trong bài báo |
| BCTC có chỉ số thay đổi > 30% so kỳ trước | 🔴 Cao | Alert nổi bật + mục riêng trong bài |
| Sự kiện cổ tức trong 3 ngày tới | 🔵 Thông tin | Hiển thị lịch sự kiện trên Portal |

### Kiểm tra pipeline & các services

```bash
# Kiểm tra trạng thái toàn bộ Docker services
docker compose ps

# Xem log từng agent
docker compose logs agent1 --tail=50 -f
docker compose logs agent3 --tail=50 -f
docker compose logs dashboard --tail=50 -f

# Kiểm tra dữ liệu đã thu thập
python -c "
import json, os
date = '2024-01-15'
checks = {
    'Giá cổ phiếu': f'storage/raw/prices_{date}.json',
    'Tin tức':       f'storage/raw/news_{date}.json',
    'Kết quả phân tích': f'storage/processed/analysis_{date}.json',
    'Alert':         f'storage/alerts_{date}.json',
    'Báo cáo PDF':   f'reports/{date}/market_report_{date}.pdf',
}
for name, path in checks.items():
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f'[{\"OK\" if size > 0 else \"MISSING\"}] {name}: {size} bytes')
"

# Trigger Airflow DAG thủ công
docker compose exec airflow airflow dags trigger market_intelligence_dag

# Xem lịch sử DAG runs
docker compose exec airflow airflow dags list-runs -d market_intelligence_dag
```

### Monitoring Airflow

Truy cập **Airflow Web UI** tại `http://localhost:8081` để:
- Theo dõi tiến trình từng Task trong DAG theo dạng cây
- Xem log chi tiết từng bước (kể cả nội dung prompt đã gửi LLM)
- Retry thủ công nếu một task bị lỗi (ví dụ API vnstock timeout)
- Xem lịch sử run và thời gian thực thi các ngày trước

---

## Lộ trình phát triển

**Hoàn thành:**
- [x] Agent 1: Modules thu thập giá, tin tức, tài liệu PDF, cổ tức (không LLM)
- [x] Agent 2: Prompt skills diễn giải BCTC + PDF tài liệu bằng Claude
- [x] Agent 3: Prompt skills phân tích đa góc độ → phân loại nguyên nhân
- [x] Agent 4: Prompt skills viết báo cáo dạng bài báo → xuất PDF
- [x] Airflow DAG: Điều phối toàn bộ pipeline 15:15 ICT hàng ngày
- [x] Docker Compose: Đóng gói từng agent + dashboard + airflow
- [x] Streamlit Dashboard: Feed báo cáo, PDF viewer inline, bảng alert

**Đang phát triển:**
- [ ] Dashboard: Thêm biểu đồ nến (Plotly candlestick) trang lịch sử
- [ ] Agent 3: Tối ưu prompt `cause_classify.txt` qua few-shot examples
- [ ] Agent 4: Thêm `weekly_digest` skill — tổng hợp xu hướng cả tuần
- [ ] Backtesting: Đánh giá độ chính xác phân loại nguyên nhân theo lịch sử

**Kế hoạch:**
- [ ] Mở rộng danh sách theo dõi lên toàn bộ VN100
- [ ] Deploy lên VPS (Streamlit chạy public, Airflow nội bộ)
- [ ] Export dữ liệu ra Google Sheets / BigQuery

---

## Tài liệu tham khảo

- [vnstock Documentation](https://vnstocks.com/docs)
- [Vnstock News — mẫu cập nhật tin (vnstock_news / CLI)](https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc)
- [vnstock GitHub](https://github.com/thinh-vu/vnstock)
- [Claude API Documentation](https://docs.anthropic.com)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io)
- [pdfplumber — Đọc PDF Python](https://github.com/jsvine/pdfplumber)
- [CafeF — Tin tức chứng khoán](https://cafef.vn)
- [Vietstock — Dữ liệu tài chính](https://vietstock.vn)
- [SSI Research](https://www.ssi.com.vn/en/research)
- [pandas-ta Documentation](https://github.com/twopirllc/pandas-ta)
