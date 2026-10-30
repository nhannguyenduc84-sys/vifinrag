# Trạng thái dự án (STATUS.md)

*Cập nhật lần cuối: 2026-10-30*

## 1. Giai đoạn hiện tại
- **Tuần 3 - Thu thập dữ liệu (crawl)**
- Mục tiêu giai đoạn: 100-300 PDF báo cáo tài chính/thường niên của 30-60 công ty niêm yết Việt Nam, đa ngành, 2-3 năm gần nhất (2022-2024), ưu tiên có text layer.

## 2. Việc đã hoàn thành
- Khởi tạo khung dự án theo `README.md` và `CLAUDE.md`.
- Thiết lập `.gitignore` loại trừ `data/`, `.venv/`, cache và checkpoints.
- Chuẩn hóa quy ước dùng `uv` qua `pyproject.toml` (chuẩn PEP 621) và `uv.lock`; ghi nhận quyết định kiến trúc tại `docs/decisions/001-su-dung-pyproject-toml-va-uv.md`.
- Khởi tạo `configs/sources.yaml` với 20 công ty đại diện các ngành trọng điểm và cấu hình crawler an toàn (delay 1.5s, User-Agent rõ ràng).
- Khởi tạo hệ thống tài liệu: `docs/STATUS.md`, `docs/worklog/TEMPLATE.md`, `docs/decisions/TEMPLATE.md`, `docs/data/sources.md`.
- Tạo cấu trúc thư mục code `src/` (crawl, preprocess, pipelines, benchmark, eval) và cấu trúc thư mục dữ liệu `data/`.

## 3. Việc tiếp theo
1. Khảo sát điều khoản sử dụng & `robots.txt` của các nguồn (IR từng công ty, CafeF, Vietstock, HOSE), cập nhật vào `docs/data/sources.md`.
2. Viết crawler thử nghiệm cho 5-10 công ty đầu tiên trong `src/crawl/`.
3. Kiểm tra tính hợp lệ của file tải về (mở được, đếm trang, text layer, sha256), ghi log vào `data/crawl_log.csv` và `data/metadata.csv`.
4. Viết module tiền xử lý `src/preprocess/` tách trang thành ảnh PNG và trích text thô.

## 4. Vấn đề & Rủi ro cần theo dõi
- Một số website IR của doanh nghiệp có thể áp dụng chống bot hoặc cấu trúc động; cần khảo sát từng trang trước khi viết crawler.
- Cần xác nhận VRAM của GPU cá nhân để định hình kích thước model cho các giai đoạn sau (ColPali, Qwen-VL).
