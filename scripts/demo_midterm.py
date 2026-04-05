#!/usr/bin/env python3
"""
Demo giai đoạn giữa kỳ:
1) Chạy Agent 1 với subset mã (--tickers).
2) Gọi LLM (gemini / deepseek / claude) với prompt tích hợp kỹ thuật + tin (stock_feed_integrated / stock_detail_integrated).
3) Sinh reports/{date}/market_report_{date}.md (tổng quan), market_report_detail_{date}.md (phân tích sâu),
   và storage/alerts_{date}.json cho Streamlit.

Đọc tin từ storage/raw/news_{date}.json (Agent 1); lọc theo ticker, ghép title + mô tả ngắn. Không BCTC.

Chạy từ thư mục gốc dự án:
  python scripts/demo_midterm.py
  python scripts/demo_midterm.py --provider deepseek --tickers VCB,FPT
  python scripts/demo_midterm.py --skip-ingest
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Thư mục gốc dự án (Final_Demo)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Windows console UTF-8 (tránh lỗi in tiếng Việt)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_agent1(date: str, tickers_csv: str) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "agent1_crawler" / "main.py"),
        "--date",
        date,
        "--tickers",
        tickers_csv,
    ]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.check_call(cmd, cwd=str(ROOT / "agent1_crawler"), env=env)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_technical_variables(
    ticker: str,
    date: str,
    price: dict,
    tech: dict,
) -> dict[str, str]:
    close = float(price.get("close", 0))
    chg = float(price.get("change_pct", 0))
    vol = int(price.get("volume", 0))
    vr = float(price.get("volume_ratio", 1))

    ma20 = tech.get("ma20")
    ma50 = tech.get("ma50")
    rsi = tech.get("rsi")
    macd = tech.get("macd")
    sig = tech.get("signal")
    bb_u = tech.get("bb_upper")
    bb_l = tech.get("bb_lower")
    above = tech.get("above_ma20")
    rsi_zone = tech.get("rsi_zone", "neutral")

    ma20_s = f"{ma20:,.0f}" if ma20 is not None else "N/A"
    ma50_s = f"{ma50:,.0f}" if ma50 is not None else "N/A"
    rsi_s = f"{rsi:.1f}" if rsi is not None else "N/A"
    macd_s = f"{macd:.4f}" if macd is not None else "N/A"
    sig_s = f"{sig:.4f}" if sig is not None else "N/A"
    bb_u_s = f"{bb_u:,.0f}" if bb_u is not None else "N/A"
    bb_l_s = f"{bb_l:,.0f}" if bb_l is not None else "N/A"

    if macd is not None and sig is not None:
        macd_cross = "Bullish" if macd > sig else "Bearish"
    else:
        macd_cross = "N/A"

    if above is True:
        ma20_pos = "TRÊN"
    elif above is False:
        ma20_pos = "DƯỚI"
    else:
        ma20_pos = "N/A"

    return {
        "ticker": ticker,
        "date": date,
        "price_change": f"{chg:+.2f}",
        "close": f"{close:,.0f}",
        "ma20": ma20_s,
        "ma50": ma50_s,
        "ma20_position": ma20_pos,
        "rsi": rsi_s,
        "rsi_zone": str(rsi_zone),
        "macd": macd_s,
        "signal": sig_s,
        "macd_cross": macd_cross,
        "bb_upper": bb_u_s,
        "bb_lower": bb_l_s,
        "volume": f"{vol:,}",
        "volume_ratio": f"{vr:.2f}",
    }


def build_alerts(
    prices: dict,
    thresholds: dict,
) -> list[dict]:
    alerts: list[dict] = []
    high_t = float(thresholds.get("price_change_alert", 5))
    med_t = float(thresholds.get("price_change_medium", 3))

    for ticker, p in prices.items():
        chg = abs(float(p.get("change_pct", 0)))
        raw = float(p.get("change_pct", 0))
        if chg >= high_t:
            level = "HIGH"
            icon = "🔴"
        elif chg >= med_t:
            level = "MEDIUM"
            icon = "🟠"
        else:
            continue
        alerts.append({
            "ticker": ticker,
            "level": level,
            "icon": icon,
            "change_pct": round(raw, 2),
            "body": f"Biến động giá {raw:+.2f}% so với phiên trước (demo giữa kỳ).",
        })
    return alerts


EMPTY_NEWS_BLOCK = "(Không có tin gắn mã trong tập dữ liệu.)"


def load_news_items(news_path: Path) -> list[dict]:
    if not news_path.exists():
        return []
    try:
        data = json.loads(news_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def filter_news_for_ticker(
    items: list[dict],
    ticker: str,
    max_items: int = 15,
) -> list[dict]:
    """Tin có ticker khớp; tin không có ticker (vd. RSS) nếu title gợi ý mã."""
    t = ticker.upper()
    matched: list[dict] = []
    for it in items:
        it_t = str(it.get("ticker") or "").strip().upper()
        if it_t == t:
            matched.append(it)
            continue
        if not it_t:
            title_u = str(it.get("title") or "").upper()
            if title_u.startswith(f"{t}:") or title_u.startswith(f"{t} "):
                matched.append(it)

    def _pub_key(x: dict) -> int:
        p = x.get("published") or ""
        try:
            return int(str(p)[:16])
        except ValueError:
            return 0

    matched.sort(key=_pub_key, reverse=True)
    out: list[dict] = []
    seen: set[str] = set()
    for it in matched:
        tit = str(it.get("title") or "").strip()
        if not tit or tit in seen:
            continue
        seen.add(tit)
        out.append(it)
        if len(out) >= max_items:
            break
    return out


def build_news_block(items: list[dict], ticker: str, max_items: int = 15) -> str:
    filtered = filter_news_for_ticker(items, ticker, max_items=max_items)
    if not filtered:
        return EMPTY_NEWS_BLOCK
    lines: list[str] = []
    for it in filtered:
        src = str(it.get("source") or "unknown")
        title = str(it.get("title") or "").strip()
        desc = (it.get("short_description") or it.get("summary") or "").strip()
        if len(desc) > 400:
            desc = desc[:397] + "..."
        lines.append(f"- [{src}] {title} · {desc}")
    return "\n".join(lines)


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Demo giữa kỳ — Agent 1 + LLM + báo cáo MD")
    parser.add_argument("--date", default="", help="YYYY-MM-DD (mặc định: hôm nay)")
    parser.add_argument("--tickers", default="VCB,FPT,VIC", help="CSV mã cổ phiếu")
    parser.add_argument(
        "--provider",
        choices=["gemini", "deepseek", "claude"],
        default=os.environ.get("DEMO_LLM_PROVIDER", "gemini"),
        help="Nhà cung cấp LLM (prompt tích hợp kỹ thuật + tin)",
    )
    parser.add_argument(
        "--legacy-technical-only",
        action="store_true",
        help="Dùng prompt chỉ kỹ thuật (technical_interpret_feed/detail), bỏ tin",
    )
    parser.add_argument("--skip-ingest", action="store_true", help="Bỏ qua Agent 1 (đã có JSON)")
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Bỏ Agent 1; ghi JSON giá + chỉ báo mẫu vào storage/raw (khi vnstock/API lỗi)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1536,
        help="Giới hạn output cho báo cáo phân tích chi tiết (detail)",
    )
    parser.add_argument(
        "--max-tokens-feed",
        type=int,
        default=384,
        help="Giới hạn output cho báo cáo thị trường tổng quan (feed, ngắn)",
    )
    args = parser.parse_args()

    from datetime import date as dt_date

    date_str = args.date or str(dt_date.today())
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    os.chdir(ROOT)
    (ROOT / "storage" / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "storage" / "raw" / "docs").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / date_str).mkdir(parents=True, exist_ok=True)

    if args.sample_data:
        raw_dir = ROOT / "storage" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        demo_prices = {}
        demo_tech = {}
        for t in tickers:
            demo_prices[t] = {
                "close": 92_500.0,
                "open": 91_000.0,
                "high": 93_000.0,
                "low": 90_500.0,
                "volume": 8_500_000,
                "change_pct": 2.35,
                "volume_ratio": 1.85,
            }
            demo_tech[t] = {
                "close": 92_500.0,
                "ma20": 90_200.0,
                "ma50": 88_000.0,
                "rsi": 58.2,
                "macd": 0.0125,
                "signal": 0.0088,
                "bb_upper": 94_000.0,
                "bb_lower": 87_500.0,
                "above_ma20": True,
                "rsi_zone": "neutral",
            }
        (raw_dir / f"prices_{date_str}.json").write_text(
            json.dumps(demo_prices, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (raw_dir / f"technicals_{date_str}.json").write_text(
            json.dumps(demo_tech, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[demo] Đã ghi dữ liệu mẫu → storage/raw/prices_{date_str}.json & technicals_*.json")
    elif not args.skip_ingest:
        print(f"[demo] Chạy Agent 1 — ngày {date_str}, mã: {tickers}")
        run_agent1(date_str, args.tickers)

    prices_path = ROOT / "storage" / "raw" / f"prices_{date_str}.json"
    tech_path = ROOT / "storage" / "raw" / f"technicals_{date_str}.json"
    if not prices_path.exists():
        print(f"[ERR] Thiếu {prices_path}. Bỏ --skip-ingest hoặc chạy Agent 1 trước.")
        sys.exit(1)

    prices = json.loads(prices_path.read_text(encoding="utf-8"))
    technicals = {}
    if tech_path.exists():
        technicals = json.loads(tech_path.read_text(encoding="utf-8"))

    settings = load_yaml(ROOT / "config" / "settings.yaml")
    th = settings.get("thresholds", {})
    alerts = build_alerts(prices, th)
    alert_file = ROOT / "storage" / f"alerts_{date_str}.json"
    alert_file.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[demo] Đã ghi {alert_file} ({len(alerts)} alert)")

    from common.llm_providers import complete_chat
    from common.prompt_utils import load_prompt_template

    news_path = ROOT / "storage" / "raw" / f"news_{date_str}.json"
    news_items = load_news_items(news_path)
    if news_items:
        print(f"[demo] Đã tải {len(news_items)} tin từ {news_path.name} (lọc theo từng mã).")
    elif not args.legacy_technical_only:
        print(f"[demo] Không có tin trong {news_path.name} — news_block = thông báo trống.")

    if args.legacy_technical_only:
        prompt_feed = ROOT / "agent3_analyst" / "prompts" / "technical_interpret_feed.txt"
        prompt_detail = ROOT / "agent3_analyst" / "prompts" / "technical_interpret_detail.txt"
        feed_name = "technical_interpret_feed"
        detail_name = "technical_interpret_detail"
    else:
        prompt_feed = ROOT / "agent3_analyst" / "prompts" / "stock_feed_integrated.txt"
        prompt_detail = ROOT / "agent3_analyst" / "prompts" / "stock_detail_integrated.txt"
        feed_name = "stock_feed_integrated"
        detail_name = "stock_detail_integrated"

    sections_feed: list[str] = [
        f"# Báo cáo thị trường (tổng quan)\n",
        f"**Ngày:** {date_str}  \n",
        f"**LLM:** `{args.provider}` — prompt `{feed_name}`  \n",
        f"**Mã:** {', '.join(tickers)}  \n",
        "_Kỹ thuật + tin (title/mô tả ngắn) từ Agent 1 khi có `storage/raw/news_*.json`. Không BCTC._\n",
        "\n---\n",
    ]
    sections_detail: list[str] = [
        f"# Báo cáo phân tích chi tiết\n",
        f"**Ngày:** {date_str}  \n",
        f"**LLM:** `{args.provider}` — prompt `{detail_name}`  \n",
        f"**Mã:** {', '.join(tickers)}  \n",
        "_Phân tích tích hợp kỹ thuật và tin theo mã; Agent 2 (BCTC) có thể bổ sung sau._\n",
        "\n---\n",
    ]

    for t in tickers:
        if t not in prices:
            miss = f"\n## {t}\n_Không có dữ liệu giá trong prices_{date_str}.json._\n"
            sections_feed.append(miss)
            sections_detail.append(miss)
            continue
        tech = technicals.get(t) or {}
        vars_ = build_technical_variables(t, date_str, prices[t], tech)
        if not args.legacy_technical_only:
            vars_["news_block"] = build_news_block(news_items, t)

        user_feed = load_prompt_template(prompt_feed, vars_)
        user_detail = load_prompt_template(prompt_detail, vars_)

        print(f"[demo] Gọi LLM feed ({args.provider}) — {t}...")
        try:
            interp_feed = complete_chat(
                args.provider,
                user_feed,
                max_tokens=args.max_tokens_feed,
            )
        except Exception as e:
            interp_feed = f"_(Lỗi gọi LLM: {e})_"

        print(f"[demo] Gọi LLM detail ({args.provider}) — {t}...")
        try:
            interp_detail = complete_chat(
                args.provider,
                user_detail,
                max_tokens=args.max_tokens,
            )
        except Exception as e:
            interp_detail = f"_(Lỗi gọi LLM: {e})_"

        sections_feed.append(f"\n## {t}\n\n{interp_feed}\n")
        sections_detail.append(f"\n## {t}\n\n{interp_detail}\n")

    report_feed_path = ROOT / "reports" / date_str / f"market_report_{date_str}.md"
    report_detail_path = ROOT / "reports" / date_str / f"market_report_detail_{date_str}.md"
    report_feed_path.write_text("".join(sections_feed), encoding="utf-8")
    report_detail_path.write_text("".join(sections_detail), encoding="utf-8")
    print(f"[demo] Đã ghi {report_feed_path}")
    print(f"[demo] Đã ghi {report_detail_path}")
    print("\n[✓] Xong. Chạy dashboard từ thư mục gốc:")
    print(f"    cd \"{ROOT}\" && streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
