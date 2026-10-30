# 001-Sử dụng pyproject.toml và uv để quản lý dependencies

- **Ngày:** 2026-10-30
- **Trạng thái:** Đã duyệt
- **Tác giả:** Claude & Sinh viên thực hiện

## 1. Ngữ cảnh & Đặt vấn đề
Đồ án tốt nghiệp ViFinRAG bao gồm nhiều giai đoạn phức tạp:
- Giai đoạn 1: Crawl dữ liệu và tiền xử lý PDF.
- Giai đoạn 2-3: Pipeline text và vision-native RAG (Docling, ColPali, PyTorch, vLLM, Qdrant).
- Giai đoạn 4-6: Benchmark, Finetuning và Đánh giá.

Hệ thống sẽ chạy trên cả máy cá nhân (Windows) và server/máy trạm có GPU để huấn luyện và chạy inference. Do đó, yêu cầu đặt ra là:
1. Đảm bảo môi trường hoàn toàn tái lập được (reproducible), tránh lỗi xung đột phiên bản phụ thuộc con.
2. Tốc độ cài đặt và giải quyết gói (dependency resolution) nhanh để tiết kiệm thời gian thí nghiệm.
3. Tuân thủ chuẩn đóng gói hiện đại của hệ sinh thái Python (PEP 621, PEP 735).

## 2. Các phương án cân nhắc

### Phương án 1: `requirements.txt` truyền thống kết hợp `pip`
- **Ưu điểm:** Quen thuộc, đơn giản.
- **Nhược điểm:** Không khóa được dependency dạng cây phân tầng sâu trừ khi freeze toàn bộ; tốc độ `pip` chậm; khó tách bạch dependencies môi trường phát triển (dev/test) và chạy thật.

### Phương án 2: `Poetry` với `pyproject.toml`
- **Ưu điểm:** Quản lý lockfile tốt, chuẩn hóa.
- **Nhược điểm:** Tốc độ giải quyết dependency chậm khi gặp các thư viện deep learning lớn (`torch`, `transformers`); đôi khi xung đột với CUDA wheel.

### Phương án 3: `pyproject.toml` (PEP 621) kết hợp `uv`
- **Ưu điểm:**
  - Tốc độ giải quyết dependency và cài đặt nhanh gấp 10-100 lần so với pip/poetry (viết bằng Rust).
  - Chuẩn PEP 621 tiêu chuẩn, không bị khóa vào vendor cụ thể.
  - File `uv.lock` khóa chính xác 100% phiên bản kèm SHA-256 cho đa nền tảng (Windows/Linux/macOS).
  - Tích hợp sẵn `uv run`, `uv sync`, `uv add`.
- **Nhược điểm:** Công cụ mới hơn `pip`, người dùng cần làm quen với vài lệnh cơ bản (`uv sync`, `uv run`).

## 3. Quyết định được chọn
Áp dụng **Phương án 3**: Khởi tạo `pyproject.toml` làm nguồn quản lý dependencies duy nhất cho toàn bộ dự án, sử dụng `uv` làm package manager chính, và commit `uv.lock` lên Git.

## 4. Lý do kỹ thuật & Biện luận
- Đồ án sẽ cài đặt các thư viện nặng (`torch`, `docling`, `transformers`, `colpali-engine`). Tốc độ cache và tải song song của `uv` giúp giảm thiểu đáng kể thời gian cài đặt.
- `uv.lock` đảm bảo khi hội đồng chấm hoặc người phản biện clone repo về, họ chỉ cần chạy `uv sync` là tái hiện chính xác 100% môi trường thí nghiệm của sinh viên mà không gặp bất kỳ lỗi xung đột thư viện nào.

## 5. Hệ quả & Đánh đổi
- **Hệ quả tích cực:**
  - Quản lý phụ thuộc sạch sẽ, phân tách nhóm `dev` (`ruff`, `pytest`) và phụ thuộc chính.
  - Thao tác nhanh với `uv run python -m src.crawl...` mà không cần kích hoạt virtualenv thủ công nếu không muốn.
- **Quy ước tuân thủ:**
  - Không sửa trực tiếp file `uv.lock` bằng tay.
  - Dùng `uv add <package>` khi cài thêm thư viện mới.
