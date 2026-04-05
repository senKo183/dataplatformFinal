"""
Airflow DAG: market_intelligence_dag
Điều phối toàn bộ pipeline VN Market Intelligence.
Chạy tự động lúc 15:15 ICT (08:15 UTC) mỗi ngày giao dịch (thứ Hai–Sáu).
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import subprocess, sys

# ── Cấu hình mặc định ─────────────────────────────────────────────────────────
default_args = {
    "owner":          "vn-market-intel",
    "depends_on_past": False,
    "retries":         2,
    "retry_delay":     timedelta(minutes=5),
    "email_on_failure": False,
}

# ── Hàm wrapper gọi từng agent ────────────────────────────────────────────────
def run_agent1_prices(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent1_crawler/price_fetch.py", "--date", date],
        check=True
    )

def run_agent1_news(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent1_crawler/news_crawl.py", "--date", date],
        check=True
    )

def run_agent1_docs(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent1_crawler/doc_downloader.py", "--date", date],
        check=True
    )

def run_agent1_dividends(**ctx):
    subprocess.run(
        [sys.executable, "/app/agent1_crawler/dividend_fetch.py", "--lookahead", "30"],
        check=True
    )

def run_agent1_technicals(**ctx):
    subprocess.run(
        [sys.executable, "/app/agent1_crawler/technical_calc.py", "--period", "60"],
        check=True
    )

def run_agent2(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent2_financial_reader/main.py", "--date", date],
        check=True
    )

def run_agent3(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent3_analyst/main.py", "--date", date],
        check=True
    )

def run_agent4(**ctx):
    date = ctx["ds"]
    subprocess.run(
        [sys.executable, "/app/agent4_reporter/main.py", "--date", date],
        check=True
    )

# ── DAG Definition ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="market_intelligence_dag",
    default_args=default_args,
    description="VN Market Intelligence — Daily pipeline sau phiên đóng cửa",
    schedule_interval="15 8 * * 1-5",   # 15:15 ICT = 08:15 UTC, thứ Hai–Sáu
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stock", "ai-agent", "vn-market"],
) as dag:

    # ── Agent 1 tasks (chạy song song) ────────────────────────────────────────
    t_prices = PythonOperator(
        task_id="fetch_prices",
        python_callable=run_agent1_prices,
        doc="Kéo giá OHLCV từ vnstock cho toàn bộ watchlist"
    )

    t_news = PythonOperator(
        task_id="fetch_news",
        python_callable=run_agent1_news,
        doc="Cào tin tức CafeF RSS + vnstock news"
    )

    t_docs = PythonOperator(
        task_id="download_docs",
        python_callable=run_agent1_docs,
        doc="Tải PDF tài liệu công bố thông tin từ HOSE/SSI"
    )

    t_dividends = PythonOperator(
        task_id="fetch_dividends",
        python_callable=run_agent1_dividends,
        doc="Lấy lịch cổ tức 30 ngày tới"
    )

    t_technicals = PythonOperator(
        task_id="calc_technicals",
        python_callable=run_agent1_technicals,
        doc="Tính MA/RSI/MACD cho toàn bộ watchlist"
    )

    # ── Agent 2 ────────────────────────────────────────────────────────────────
    t_agent2 = PythonOperator(
        task_id="run_financial_reader",
        python_callable=run_agent2,
        doc="Đọc BCTC + PDF tài liệu, diễn giải bằng Claude prompt skills"
    )

    # ── Agent 3 ────────────────────────────────────────────────────────────────
    t_agent3 = PythonOperator(
        task_id="run_analyst",
        python_callable=run_agent3,
        doc="Phân tích nguyên nhân biến động qua 4 prompt skills"
    )

    # ── Agent 4 ────────────────────────────────────────────────────────────────
    t_agent4 = PythonOperator(
        task_id="generate_report",
        python_callable=run_agent4,
        doc="Viết báo cáo PDF + tạo alerts cho Streamlit dashboard"
    )

    # ── Dependency graph ───────────────────────────────────────────────────────
    # Agent 1: fetch prices, news, docs, dividends SONG SONG → sau đó tính kỹ thuật
    [t_prices, t_news, t_docs, t_dividends] >> t_technicals

    # Agent 2 đợi Agent 1 hoàn thành
    t_technicals >> t_agent2

    # Agent 3 đợi Agent 2
    t_agent2 >> t_agent3

    # Agent 4 đợi Agent 3
    t_agent3 >> t_agent4
