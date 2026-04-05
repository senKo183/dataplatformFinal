"""
Agent 1 — Module: dividend_fetch.py
Lấy lịch chia cổ tức và ngày GDKHQ từ vnstock.
"""

import json
from datetime import date as dt, timedelta
from pathlib import Path
from vnstock import Vnstock


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fetch_dividends(tickers: list[str], lookahead_days: int = 30,
                    save_dir: str | None = None) -> list[dict]:
    """
    Lấy lịch cổ tức cho danh sách mã trong vòng `lookahead_days` ngày tới.
    Lưu kết quả vào storage/raw/dividends_{date}.json.
    """
    if save_dir is None:
        save_dir = str(_project_root() / "storage" / "raw")
    today = dt.today()
    cutoff = today + timedelta(days=lookahead_days)
    results = []

    missing_method_count = 0
    for ticker in tickers:
        try:
            stock = Vnstock().stock(symbol=ticker, source="VCI")

            # Một số phiên bản vnstock không có company.dividends()
            if not hasattr(stock.company, "dividends"):
                missing_method_count += 1
                print(f"[WARN] dividend {ticker}: vnstock không hỗ trợ stock.company.dividends()")
                continue

            divs = stock.company.dividends()
            if divs is None or (hasattr(divs, "empty") and divs.empty):
                continue

            for _, row in divs.iterrows():
                # Lấy các sự kiện sắp tới trong khoảng lookahead
                ex_date_str = str(row.get("ex_date", ""))
                try:
                    ex_date = dt.fromisoformat(ex_date_str[:10])
                    if today <= ex_date <= cutoff:
                        results.append({
                            "ticker":        ticker,
                            "ex_date":       ex_date_str[:10],
                            "record_date":   str(row.get("record_date", "")),
                            "payment_date":  str(row.get("payment_date", "")),
                            "dividend_type": str(row.get("dividend_type", "")),
                            "value":         str(row.get("value", "")),
                        })
                        print(f"[✓] {ticker} — GDKHQ: {ex_date_str[:10]} | {row.get('dividend_type','')} {row.get('value','')}")
                except ValueError:
                    pass

        except Exception as e:
            print(f"[ERR] dividend {ticker}: {e}")

    date_str = str(today)
    out_path = Path(save_dir) / f"dividends_{date_str}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] {len(results)} sự kiện cổ tức → {out_path}")

    # Lưu thêm vào resources cho các agent phân tích
    resource_dir = _project_root() / "resources" / "dividends"
    resource_dir.mkdir(parents=True, exist_ok=True)
    resource_path = resource_dir / f"dividends_{date_str}.json"
    resource_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Resource → {resource_path}")
    if missing_method_count:
        print(
            f"[INFO] Bỏ qua cổ tức cho {missing_method_count} mã vì phiên bản vnstock hiện tại "
            "không có company.dividends()."
        )

    return results


if __name__ == "__main__":
    import argparse, yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--lookahead", type=int, default=30)
    args = parser.parse_args()

    watchlist = yaml.safe_load(open("../config/watchlist.yaml"))
    tickers = watchlist["watchlist"]["vn30"] + watchlist["watchlist"].get("custom", [])

    fetch_dividends(tickers, lookahead_days=args.lookahead)
