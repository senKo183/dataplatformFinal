"""
Agent 1 — Module: news_crawl.py
Thu thập tin tức từ CafeF RSS và vnstock news theo từng mã cổ phiếu.

Tài liệu Vnstock News (crawler nâng cao / CLI): https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc
"""

import os
import feedparser
import json
from datetime import date as dt, timedelta
from pathlib import Path

# Load .env từ thư mục gốc dự án (Final_Demo/.env) khi chạy trực tiếp agent1
try:
    from dotenv import load_dotenv

    _ROOT = Path(__file__).resolve().parents[1]  # Final_Demo/
    load_dotenv(_ROOT / ".env")
except Exception:
    pass

# API key vnstock (hạn mức cao hơn khi có key — theo docs ecosystem)
_k = os.environ.get("VNSTOCK_API_KEY", "").strip()
if _k:
    os.environ.setdefault("VNSTOCK_API_KEY", _k)

from vnstock import Vnstock


CAFEF_RSS = "https://cafef.vn/rss/chung-khoan.rss"


def crawl_cafef(limit: int = 50) -> list[dict]:
    """Lấy tin tức từ CafeF RSS feed."""
    feed = feedparser.parse(CAFEF_RSS)
    news = []
    for entry in feed.entries[:limit]:
        news.append({
            "source":    "cafef",
            "title":     entry.get("title", ""),
            "summary":   entry.get("summary", ""),
            "link":      entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return news


def crawl_vnstock_news(tickers: list[str]) -> list[dict]:
    """Lấy tin tức công ty từ vnstock theo từng mã."""

    def pick(row, *keys: str) -> str:
        for k in keys:
            if k in row.index and row.get(k) is not None:
                v = str(row.get(k)).strip()
                if v and v.lower() != "nan":
                    return v
        return ""

    def summary_from_row(row) -> str:
        """Ưu tiên mô tả ngắn (short_description) như tài liệu VCI/vnstock thường trả về."""
        s = pick(
            row,
            "short_description",
            "short_description_en",
            "short_description_vn",
            "sapo",
            "teaser",
            "lead",
            "abstract",
            "summary",
            "description",
            "content",
            "short_content",
            "body",
        )
        if s:
            return s
        # Fallback: cột có tên chứa short/desc/sapo (schema khác nhau theo phiên bản)
        for col in row.index:
            cl = str(col).lower()
            if any(x in cl for x in ("short", "desc", "sapo", "teaser", "lead", "abstract")):
                v = str(row.get(col, "")).strip()
                if v and v.lower() != "nan":
                    return v
        return ""

    news = []
    for ticker in tickers:
        try:
            stock = Vnstock().stock(symbol=ticker, source="VCI")
            items = stock.company.news()
            if items is None or (hasattr(items, "empty") and items.empty):
                continue
            for _, row in items.iterrows():
                summ = summary_from_row(row)
                title = pick(row, "title", "news_title", "headline", "subject")
                link = pick(row, "url", "link", "news_url", "href")
                pub = pick(
                    row,
                    "publish_date",
                    "published_at",
                    "time",
                    "date",
                    "public_date",
                )
                short_desc = pick(
                    row,
                    "short_description",
                    "short_description_vn",
                    "short_description_en",
                )
                item = {
                    "source": "vnstock",
                    "ticker": ticker,
                    "title": title,
                    # summary = nội dung mô tả ngắn dùng cho Agent 2/3 (ưu tiên short_description)
                    "summary": summ or short_desc,
                    "short_description": short_desc or summ,
                    "link": link,
                    "published": pub,
                }
                if item["title"] or item["summary"] or item["link"]:
                    news.append(item)
        except Exception as e:
            print(f"[ERR] news {ticker}: {e}")
    return news


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def crawl_news(tickers: list[str], date: str, save_dir: str | None = None) -> list[dict]:
    """Tổng hợp tin tức từ tất cả nguồn và lưu JSON."""
    if save_dir is None:
        save_dir = str(_project_root() / "storage" / "raw")
    print("[→] Thu thập tin CafeF RSS...")
    cafef_news = crawl_cafef()

    print(f"[→] Thu thập tin vnstock cho {len(tickers)} mã...")
    vnstock_news = crawl_vnstock_news(tickers)

    all_news = cafef_news + vnstock_news
    print(f"[✓] Tổng: {len(all_news)} tin tức")

    out_dir = Path(save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"news_{date}.json"
    out_path.write_text(json.dumps(all_news, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Lưu → {out_path}")

    # Lưu thêm bản resource để Agent 2/3 dùng trực tiếp (thư mục gốc dự án)
    resource_dir = _project_root() / "resources" / "news"
    resource_dir.mkdir(parents=True, exist_ok=True)
    resource_path = resource_dir / f"news_{date}.json"
    resource_path.write_text(json.dumps(all_news, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Resource → {resource_path}")

    return all_news


if __name__ == "__main__":
    import argparse, yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(dt.today()))
    args = parser.parse_args()

    watchlist = yaml.safe_load(open("../config/watchlist.yaml"))
    tickers = watchlist["watchlist"]["vn30"] + watchlist["watchlist"].get("custom", [])

    crawl_news(tickers, args.date)
