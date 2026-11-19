# Nhật ký phiên làm việc: 2026-10-30 - Khởi tạo dự án và Thẩm định nguồn dữ liệu Batch 1

> **Quy tắc ghi chép (theo CLAUDE.md):**
> - Chỉ ghi điều đã thực sự làm và chạy được. Việc chưa kiểm tra ghi vào mục "Vấn đề và chưa chắc chắn".
> - Số liệu lấy từ lệnh hoặc file thật (đếm file, đọc log), không ước lượng.
> - Ghi cả lỗi và thất bại, kèm cách đã thử.
> - Không sửa nhật ký cũ; muốn đính chính thì ghi ở phiên mới.
> - Mỗi nhật ký có lệnh chạy lại được kết quả và danh sách việc tiếp theo.

## 1. Mục tiêu phiên
- Khởi tạo toàn bộ cấu trúc thư mục, môi trường dependencies của dự án ViFinRAG.
- Xây dựng cấu hình nguồn dữ liệu `configs/sources.yaml` với danh mục ngành và ~40 công ty niêm yết (HOSE, HNX).
- Thẩm định thực tế trên trình duyệt đường dẫn BCTN của các công ty trong Batch 1.
- Tinh giản quy tắc thu thập dữ liệu trong `CLAUDE.md` và `configs/sources.yaml`.

## 2. Việc đã thực hiện & Kết quả
- **Khởi tạo khung dự án & Môi trường**:
  - Tạo cấu trúc thư mục chuẩn: `src/` (crawl, preprocess, pipelines, benchmark, eval), `configs/`, `data/`, `docs/`, `experiments/`.
  - Cấu hình `pyproject.toml`, `requirements.txt`, `.gitignore`.
  - Quản lý môi trường Python qua `uv` và virtualenv `.venv`.
- **Cấu hình nguồn dữ liệu (`configs/sources.yaml`)**:
  - Thiết lập User-Agent nghiên cứu học thuật có email sinh viên HUST.
  - Chuẩn hóa taxonomy 16 ngành kinh tế.
  - Thiết lập danh sách 39 công ty niêm yết (đầy đủ các ngành trọng điểm).
  - Tinh giản bỏ các trường thủ công `robots_checked` / `terms_checked` ở cấp từng công ty; tuân thủ quy định pháp luật về công bố thông tin đại chúng (Thông tư 96/2020/TT-BTC).
- **Thẩm định thực tế 9 công ty Batch 1**:
  - Đã mở trình duyệt kiểm tra thực tế và lấy URL trực tiếp dẫn tới BCTN cho 9 công ty: VCB, TCB, FPT, MWG, VNM, HPG, VHM, GAS, GMD (đại diện 8 ngành khác nhau).
  - Cập nhật trạng thái `ir_url_verified: true` và `status: "verified"` trong `configs/sources.yaml`.
- **Cập nhật hệ thống tài liệu**:
  - Cập nhật `CLAUDE.md` đồng bộ quy tắc crawl tinh gọn.
  - Cập nhật `docs/STATUS.md` và `docs/data/sources.md` phản ánh chính xác tiến độ.

## 3. Lỗi / Vấn đề gặp phải & Cách xử lý
- **Lỗi syntax nhỏ**: Trong quá trình cập nhật thủ công, mã `HPG` có giá trị `trues` thay vì `true`. Đã được phát hiện và sửa lại thành `true`.
- **Băn khoăn về thời gian phát hành BCTN**: Techcombank công bố BCTN 2025 vào ngày 03/04/2026 (dính quý 1 năm sau). Đã làm rõ đây là ngày phát hành bình thường theo quy định nộp BCTN trong vòng 110 ngày sau kết thúc năm tài chính.

## 4. Vấn đề và chưa chắc chắn
- Cần kiểm tra cấu trúc DOM HTML thực tế của từng trang trong 9 công ty Batch 1 để xem trang nào dùng HTML tĩnh (tải bằng `requests`/`BeautifulSoup`) và trang nào dùng Single Page App (SPA / JavaScript) cần dùng `playwright`.

## 5. Lệnh tái lập kết quả
```bash
# Kiểm tra cú pháp YAML của sources.yaml bằng môi trường venv
.venv\Scripts\python.exe -c "import yaml; data=yaml.safe_load(open('configs/sources.yaml', encoding='utf-8')); print('Companies count:', len(data['companies']))"
```

## 6. Kế hoạch phiên tiếp theo
- [ ] Viết module crawler trong `src/crawl/` để quét và tải PDF BCTN của 9 công ty Batch 1.
- [ ] Tải file về `data/raw/pdf/`, tính mã SHA-256, kiểm tra text layer và số trang.
- [ ] Ghi nhật ký vào `data/metadata.csv` và `data/crawl_log.csv`.
