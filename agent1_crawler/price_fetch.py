"""
Agent 1 — Module: price_fetch.py
Thu thập giá OHLCV và thông tin cơ bản từ vnstock.
"""

from vnstock import Vnstock
import pandas as pd
import json
from datetime import date as dt
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fetch_prices(tickers: list[str], date: str, save_dir: str | None = None) -> dict:
    """
    Kéo giá đóng cửa, khối lượng và thông tin cơ bản cho danh sách mã.
    Trả về dict {ticker: {ohlcv, change_pct, volume_ratio}} và lưu JSON.
    """
    if save_dir is None:
        save_dir = str(_project_root() / "storage" / "raw")
    results = {}

    for ticker in tickers:
        try:
            stock = Vnstock().stock(symbol=ticker, source="VCI")

            # Lịch sử giá 60 ngày để tính volume ratio
            df = stock.quote.history(start="2024-01-01", end=date, interval="1D")
            if df.empty:
                print(f"[SKIP] {ticker}: Không có dữ liệu giá")
                continue

            latest = df.iloc[-1]
            prev   = df.iloc[-2] if len(df) >= 2 else latest

            change_pct    = (latest["close"] - prev["close"]) / prev["close"] * 100
            avg_vol_20    = df["volume"].tail(21).iloc[:-1].mean()
            volume_ratio  = latest["volume"] / avg_vol_20 if avg_vol_20 > 0 else 1.0

            results[ticker] = {
                "close":        float(latest["close"]),
                "open":         float(latest["open"]),
                "high":         float(latest["high"]),
                "low":          float(latest["low"]),
                "volume":       int(latest["volume"]),
                "change_pct":   round(change_pct, 2),
                "volume_ratio": round(volume_ratio, 2),
            }
            print(f"[✓] {ticker}: {latest['close']:,.0f} VND ({change_pct:+.1f}%) | KL: {int(latest['volume']):,} ({volume_ratio:.1f}x TB20)")

        except Exception as e:
            print(f"[ERR] {ticker}: {e}")

    # Lưu ra JSON
    out_dir = Path(save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"prices_{date}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Lưu → {out_path}")

    # Lưu thêm vào resources để Agent 2/3 dùng ngữ cảnh thị trường theo ngày
    resource_dir = _project_root() / "resources" / "prices"
    resource_dir.mkdir(parents=True, exist_ok=True)
    resource_path = resource_dir / f"prices_{date}.json"
    resource_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Resource → {resource_path}")

    return results


if __name__ == "__main__":
    import argparse, yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(dt.today()))
    args = parser.parse_args()

    watchlist = yaml.safe_load(open("../config/watchlist.yaml"))
    tickers = watchlist["watchlist"]["vn30"] + watchlist["watchlist"].get("custom", [])

    fetch_prices(tickers, args.date)
