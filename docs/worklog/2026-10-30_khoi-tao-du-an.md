# Nhật ký phiên làm việc: 2026-10-30 - Khởi tạo khung dự án & Cấu hình môi trường

## 1. Mục tiêu phiên
- Đọc kỹ `CLAUDE.md` và `README.md` để nắm rõ bài toán đồ án tốt nghiệp, yêu cầu hệ thống và các quy tắc làm việc.
- Cập nhật quy ước quản lý thư viện và môi trường ảo bằng `uv` vào `CLAUDE.md` và `README.md`.
- Khởi tạo toàn bộ cấu trúc thư mục và file ban đầu phục vụ giai đoạn thu thập dữ liệu (crawl).

## 2. Việc đã thực hiện & Kết quả
- **Cập nhật quy ước `uv` và chuyển sang `pyproject.toml`**:
  - Khởi tạo [pyproject.toml](file:///d:/Project/vifinrag/pyproject.toml) chuẩn PEP 621 quản lý dependencies chính và dev group (`ruff`, `pytest`).
  - Ghi nhận quyết định kiến trúc tại [docs/decisions/001-su-dung-pyproject-toml-va-uv.md](file:///d:/Project/vifinrag/docs/decisions/001-su-dung-pyproject-toml-va-uv.md).
  - Cập nhật chỉ dẫn workflow `uv sync`, `uv add`, `uv run` trong [CLAUDE.md](file:///d:/Project/vifinrag/CLAUDE.md) và [README.md](file:///d:/Project/vifinrag/README.md).
- **Khởi tạo file cấu hình & quản lý mã nguồn**:
  - Tạo [.gitignore](file:///d:/Project/vifinrag/.gitignore): loại trừ `data/`, `.venv/`, cache Python (`__pycache__`, `.pytest_cache`, `.ruff_cache`), và checkpoint model (`*.pt`, `*.bin`, `*.safetensors`).
  - Cập nhật [requirements.txt](file:///d:/Project/vifinrag/requirements.txt) làm bản xuất tham khảo phụ.
  - Tạo [configs/sources.yaml](file:///d:/Project/vifinrag/configs/sources.yaml): cấu hình crawler an toàn (delay 1.5s, User-Agent học thuật, max retries 3) kèm danh sách 20 công ty niêm yết thuộc các ngành tiêu biểu (Ngân hàng, Công nghệ, Bán lẻ, Thép, BĐS, Năng lượng, Logistics).
- **Khởi tạo hệ thống tài liệu chuẩn (`docs/`)**:
  - `docs/STATUS.md`: tóm tắt trạng thái hiện tại (giai đoạn 1 - crawl).
  - `docs/worklog/TEMPLATE.md`: biểu mẫu ghi chép nhật ký theo từng phiên.
  - `docs/decisions/TEMPLATE.md`: biểu mẫu ghi nhận quyết định kiến trúc (ADR).
  - `docs/data/sources.md`: bảng theo dõi tình trạng `robots.txt` và ToS các nguồn (IR, HOSE, HNX, CafeF, Vietstock).
- **Khởi tạo cấu trúc module mã nguồn (`src/`)**:
  - `src/__init__.py`
  - `src/crawl/__init__.py`
  - `src/preprocess/__init__.py`
  - `src/pipelines/__init__.py`
  - `src/benchmark/__init__.py`
  - `src/eval/__init__.py`
- **Khởi tạo cấu trúc dữ liệu cục bộ (`data/`)**:
  - `data/raw/pdf/`: thư mục chứa PDF gốc.
  - `data/pages/`: thư mục chứa ảnh PNG từng trang.
  - `data/text/`: thư mục chứa text trích xuất.
  - `data/metadata.csv`: header chuẩn hóa 12 trường (`doc_id,ticker,company,industry,doc_type,year,num_pages,has_text_layer,source_url,source_name,sha256,downloaded_at`).
  - `data/crawl_log.csv`: header chuẩn hóa 9 trường (`timestamp,ticker,doc_type,year,source_url,status,error_reason,file_path,sha256`).

## 3. Lỗi / Vấn đề gặp phải & Cách xử lý
- *Lỗi đánh số dòng khi chỉnh sửa*: Khi dùng tool edit lần đầu, số dòng từ view tool bị dính vào nội dung markdown. Đã phát hiện ngay và sửa lại chính xác nội dung nguyên bản.

## 4. Vấn đề và chưa chắc chắn
- Chưa kiểm tra thực tế `robots.txt` của các domain nguồn (IR doanh nghiệp, CafeF, Vietstock, HOSE) do cần xác nhận đường truyền mạng và sự đồng thuận trước khi gửi request.
- Cần người dùng xác nhận thông số VRAM của GPU cá nhân để chuẩn bị cho giai đoạn triển khai model (ColPali/ColQwen, Qwen-VL).

## 5. Lệnh kiểm tra cấu trúc
```bash
# Kiểm tra cây thư mục
Get-ChildItem -Recurse -Depth 2
```

## 6. Kế hoạch phiên tiếp theo
- [ ] Khảo sát `robots.txt` và điều khoản dịch vụ của nguồn dữ liệu đầu tiên (ví dụ: CafeF hoặc trang IR của FPT/Vinamilk).
- [ ] Xây dựng crawler mẫu trong `src/crawl/` với cơ chế retry, rate limit, kiểm tra sha256 và ghi log.
- [ ] Tải thử nghiệm 5-10 tài liệu PDF đầu tiên và kiểm tra tính hợp lệ.
