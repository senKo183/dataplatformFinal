"""
Agent 1 — Module: technical_calc.py
Tính chỉ số kỹ thuật: MA20/50, RSI(14), MACD, Bollinger Bands từ lịch sử giá.
"""

import json
import pandas as pd
from datetime import date as dt
from pathlib import Path
from vnstock import Vnstock


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _rsi_wilder(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_g = gain.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    avg_l = loss.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    rs = avg_g / avg_l.replace(0, 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    sig = line.ewm(span=9, adjust=False).mean()
    return line, sig


def _bollinger(close: pd.Series, length: int = 20, mult: float = 2.0) -> tuple[pd.Series, pd.Series]:
    mid = close.rolling(length).mean()
    sd = close.rolling(length).std()
    upper = mid + mult * sd
    lower = mid - mult * sd
    return upper, lower


def calc_technicals(tickers: list[str], period: int = 60,
                    save_dir: str | None = None,
                    output_date: str | None = None) -> dict:
    """
    Tính chỉ số kỹ thuật cho danh sách mã dựa trên `period` phiên giao dịch gần nhất.
    Trả về dict {ticker: {ma20, ma50, rsi, macd, signal, bb_upper, bb_lower, ...}}
    """
    from datetime import timedelta
    end_date   = str(dt.today())
    start_date = str(dt.today() - timedelta(days=period * 2))  # lấy nhiều hơn để đủ data

    results = {}

    for ticker in tickers:
        try:
            stock = Vnstock().stock(symbol=ticker, source="VCI")
            df = stock.quote.history(start=start_date, end=end_date, interval="1D")

            if df is None or len(df) < 20:
                print(f"[SKIP] {ticker}: Không đủ dữ liệu ({len(df) if df is not None else 0} phiên)")
                continue

            df = df.tail(period).reset_index(drop=True)

            # Moving Averages
            df["ma20"] = df["close"].rolling(20).mean()
            df["ma50"] = df["close"].rolling(50).mean() if len(df) >= 50 else None

            df["rsi"] = _rsi_wilder(df["close"], 14)
            macd_line, macd_sig = _macd(df["close"])
            df["macd"] = macd_line
            df["signal"] = macd_sig
            bb_u, bb_l = _bollinger(df["close"], 20, 2.0)
            df["bb_upper"] = bb_u
            df["bb_lower"] = bb_l

            latest = df.iloc[-1]

            results[ticker] = {
                "close":    float(latest["close"]),
                "ma20":     round(float(latest["ma20"]), 2) if pd.notna(latest.get("ma20")) else None,
                "ma50":     round(float(latest["ma50"]), 2) if latest.get("ma50") is not None and pd.notna(latest.get("ma50")) else None,
                "rsi":      round(float(latest["rsi"]), 1)  if pd.notna(latest.get("rsi"))  else None,
                "macd":     round(float(latest["macd"]), 4) if pd.notna(latest.get("macd")) else None,
                "signal":   round(float(latest["signal"]), 4) if pd.notna(latest.get("signal")) else None,
                "bb_upper": round(float(latest["bb_upper"]), 2) if pd.notna(latest.get("bb_upper")) else None,
                "bb_lower": round(float(latest["bb_lower"]), 2) if pd.notna(latest.get("bb_lower")) else None,
                # Tín hiệu phân tích nhanh
                "above_ma20": float(latest["close"]) > float(latest["ma20"]) if pd.notna(latest.get("ma20")) else None,
                "rsi_zone":   "overbought" if (latest.get("rsi") or 50) > 70 else ("oversold" if (latest.get("rsi") or 50) < 30 else "neutral"),
            }
            m20 = results[ticker]["ma20"]
            m20s = f"{m20:,.0f}" if m20 is not None else "N/A"
            print(f"[✓] {ticker}: MA20={m20s} | RSI={results[ticker]['rsi']} | MACD={results[ticker]['macd']}")

        except Exception as e:
            print(f"[ERR] technical {ticker}: {e}")

    date_str = output_date if output_date else str(dt.today())
    if save_dir is None:
        save_dir = str(_project_root() / "storage" / "raw")
    out_dir = Path(save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"technicals_{date_str}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Lưu → {out_path}")

    resource_dir = _project_root() / "resources" / "technicals"
    resource_dir.mkdir(parents=True, exist_ok=True)
    resource_path = resource_dir / f"technicals_{date_str}.json"
    resource_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Resource → {resource_path}")

    return results


if __name__ == "__main__":
    import argparse, yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=int, default=60)
    args = parser.parse_args()

    watchlist = yaml.safe_load(open("../config/watchlist.yaml"))
    tickers = watchlist["watchlist"]["vn30"] + watchlist["watchlist"].get("custom", [])

    calc_technicals(tickers, period=args.period)
