"""
Agent 1 — main.py
Entry point: chạy tuần tự tất cả modules thu thập dữ liệu.
Được gọi bởi Airflow DAG hoặc chạy thủ công.
"""

import argparse
import yaml
from datetime import date as dt
from price_fetch    import fetch_prices
from news_crawl     import crawl_news
from dividend_fetch import fetch_dividends
from technical_calc import calc_technicals
from doc_downloader import download_docs


def load_watchlist(path: str = "../config/watchlist.yaml") -> list[str]:
    cfg = yaml.safe_load(open(path, encoding="utf-8"))
    wl  = cfg.get("watchlist", {})
    return wl.get("vn30", []) + wl.get("custom", [])


def run(date: str, tickers: list[str] | None = None):
    print(f"\n{'='*50}")
    print(f"  Agent 1 — Data Ingestion | Ngày: {date}")
    print(f"{'='*50}\n")

    tickers = tickers if tickers is not None else load_watchlist()
    print(f"[→] Danh sách theo dõi: {', '.join(tickers)}\n")

    print("[1/5] Thu thập giá cổ phiếu...")
    fetch_prices(tickers, date)

    print("\n[2/5] Thu thập tin tức...")
    crawl_news(tickers, date)

    print("\n[3/5] Tải tài liệu PDF công bố thông tin...")
    download_docs(tickers, date)

    print("\n[4/5] Lấy lịch cổ tức (30 ngày tới)...")
    fetch_dividends(tickers, lookahead_days=30)

    print("\n[5/5] Tính chỉ số kỹ thuật...")
    calc_technicals(tickers, period=60, output_date=date)

    print(f"\n[✓] Agent 1 hoàn thành.")
    print("[✓] Dữ liệu pipeline (thư mục gốc dự án): storage/raw/")
    print("[✓] Resource cho Agent 2/3 (thư mục gốc dự án): resources/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 1 — Data Ingestion")
    parser.add_argument("--date", default=str(dt.today()), help="Ngày thu thập (YYYY-MM-DD)")
    parser.add_argument(
        "--tickers",
        default="",
        help="Danh sách mã CSV (vd: VCB,FPT,VIC). Để trống = toàn bộ watchlist.",
    )
    args = parser.parse_args()

    subset = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    run(args.date, tickers=subset if subset else None)
