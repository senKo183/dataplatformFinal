"""
Agent 1 — Module: doc_downloader.py
Tải file PDF tài liệu công bố thông tin từ HOSE/SSI về local.
"""

import requests
import json
from datetime import date as dt
from pathlib import Path
from vnstock import Vnstock


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def download_docs(tickers: list[str], date: str,
                  save_dir: str | None = None) -> list[dict]:
    """
    Tải các văn bản công bố thông tin (PDF) của từng mã về thư mục save_dir.
    Trả về danh sách {ticker, filename, path, doc_type, date}.
    """
    if save_dir is None:
        save_dir = str(_project_root() / "storage" / "raw" / "docs")
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    resource_docs_dir = _project_root() / "resources" / "docs" / date
    resource_docs_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for ticker in tickers:
        try:
            stock = Vnstock().stock(symbol=ticker, source="VCI")

            # Thử lấy danh sách tài liệu qua company events hoặc news
            # (vnstock v3 chưa có API riêng cho documents — dùng news làm fallback)
            news = stock.company.news()
            if news is None or (hasattr(news, "empty") and news.empty):
                continue

            # Lọc các tin có đính kèm file (url kết thúc .pdf)
            for _, row in news.iterrows():
                url = str(row.get("url", ""))
                if url.lower().endswith(".pdf"):
                    filename = f"{ticker}_{date}_{Path(url).name}"
                    out_path = Path(save_dir) / filename
                    resource_pdf_path = resource_docs_dir / filename

                    if out_path.exists():
                        print(f"[SKIP] {filename} đã tồn tại")
                        continue

                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        out_path.write_bytes(response.content)
                        resource_pdf_path.write_bytes(response.content)
                        saved.append({
                            "ticker":    ticker,
                            "filename":  filename,
                            "path":      str(out_path),
                            "resource_path": str(resource_pdf_path),
                            "doc_type":  "disclosure",
                            "date":      date,
                            "source_url": url,
                        })
                        print(f"[✓] Tải → {out_path}")

        except Exception as e:
            print(f"[ERR] doc_download {ticker}: {e}")

    # Lưu manifest
    manifest_dir = _project_root() / "storage" / "raw"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"docs_manifest_{date}.json"
    manifest_path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] {len(saved)} file PDF → {manifest_path}")

    resource_manifest_dir = _project_root() / "resources" / "docs"
    resource_manifest_dir.mkdir(parents=True, exist_ok=True)
    resource_manifest = resource_manifest_dir / f"docs_manifest_{date}.json"
    resource_manifest.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Resource manifest → {resource_manifest}")

    return saved


if __name__ == "__main__":
    import argparse, yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(dt.today()))
    args = parser.parse_args()

    watchlist = yaml.safe_load(open("../config/watchlist.yaml"))
    tickers = watchlist["watchlist"]["vn30"] + watchlist["watchlist"].get("custom", [])

    download_docs(tickers, args.date)
