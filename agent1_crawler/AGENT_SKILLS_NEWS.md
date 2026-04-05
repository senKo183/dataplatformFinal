# Agent 1 — Quy tắc & skill thu thập tin tức / tài liệu (vnstock)

Tham chiếu nội bộ: `instructions.md` (hệ sinh thái vnstock) và tài liệu Vnstock News:
[Mẫu chương trình cập nhật tin tức](https://vnstocks.com/docs/vnstock-news/mau-chuong-trinh-cap-nhat-tin-tuc).

## Mục tiêu

- Lưu tin theo ngày vào `{thư mục gốc dự án}/storage/raw/news_{date}.json` và bản phục vụ phân tích vào `{thư mục gốc dự án}/resources/news/news_{date}.json` (khi chạy từ `agent1_crawler/`, đường dẫn vẫn trỏ về gốc `Final_Demo/`).
- Trường `summary` phải ưu tiên lấy từ **mô tả ngắn** do API trả về (ví dụ `short_description`), trước khi fallback sang cột khác.

## Cấu hình

- `VNSTOCK_API_KEY` trong `.env` (không commit): tăng hạn mức theo tài liệu vnstock ecosystem; đọc từ môi trường khi chạy Agent 1 / `demo_midterm.py`.

## Gói tùy chọn (sponsored / nâng cao)

- Thư viện **`vnstock_news`**: crawler RSS/sitemap chuẩn hóa — cài khi cần: `pip install vnstock-news` (tên gói có thể thay đổi theo PyPI; xem docs Vnstock).
- Code hiện tại: **vnstock** `stock.company.news()` theo từng mã + CafeF RSS; `vnstock_news` có thể bổ sung sau trong pipeline riêng.

## Agent 2 / 3

- Agent 2: đọc PDF/BCTC từ `resources/docs/{date}/` và manifest `resources/docs/docs_manifest_{date}.json`.
- Agent 3: skill `news_sentiment` nhận danh sách tin đã chuẩn hóa từ JSON trên.
- Demo giữa kỳ (`scripts/demo_midterm.py`): mặc định dùng `stock_feed_integrated.txt` + `stock_detail_integrated.txt` — đọc `storage/raw/news_{date}.json`, lọc theo `ticker`, truyền `news_block` (title + mô tả ngắn).
