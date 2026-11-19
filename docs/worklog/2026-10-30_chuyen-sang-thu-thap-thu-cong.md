# Nhật ký phiên làm việc: 2026-10-30 - Chuyển đổi chiến lược sang Thu thập BCTN thủ công có kiểm định

> **Quy tắc ghi chép (theo CLAUDE.md):**
> - Chỉ ghi điều đã thực sự làm và chạy được. Việc chưa kiểm tra ghi vào mục "Vấn đề và chưa chắc chắn".
> - Số liệu lấy từ lệnh hoặc file thật (đếm file, đọc log), không ước lượng.
> - Ghi cả lỗi và thất bại, kèm cách đã thử.
> - Không sửa nhật ký cũ; muốn đính chính thì ghi ở phiên mới.
> - Mỗi nhật ký có lệnh chạy lại được kết quả và danh sách việc tiếp theo.

## 1. Mục tiêu phiên
- Xây dựng và kiểm thử crawler cho kênh IR (`ir_crawler.py`) và kênh HOSE (`hose_crawler.py`) trên 9 công ty Batch 1.
- Đánh giá tính phù hợp giữa Báo cáo thường niên (BCTN) và Báo cáo tài chính (BCTC) đối với bài toán RAG đa phương thức.
- Tinh chỉnh chiến lược thu thập dữ liệu để tối ưu hóa thời gian và nguồn lực cho đồ án tốt nghiệp.

## 2. Việc đã thực hiện & Kết quả
- **Kiểm nghiệm cào web thực tế trên Batch 1**:
  - Chạy `ir_crawler.py`: Kết quả 14 lượt tải thành công (FPT, HPG, GMD, VNM, GAS), 13 lượt thất bại/không tìm thấy (VCB, TCB, MWG, VHM, GAS-2023).
  - Phân tích nguyên nhân: VCB dùng Angular SPA, TCB dùng Adobe AEM nạp động qua GraphQL, MWG render động client-side, VHM chặn bot bằng Cloudflare WAF (HTTP 403).
  - Nhận diện rủi ro: Web crawler tự động dễ bị nhầm file ngắn (1-2 trang công bố thông tin của GAS) hoặc nhầm năm do timestamp trong URL hash (VNM 2024).
- **Phân tích học thuật: BCTN vs BCTC**:
  - Khẳng định BCTN là lựa chọn vượt trội và phù hợp nhất cho đề tài Multimodal RAG (ColPali/Docling/VLM) vì chứa hệ thống phong phú biểu đồ cột, biểu đồ tròn, infographic, layout 2-3 cột phức tạp, đồng thời phần cuối BCTN đã bao gồm toàn bộ BCTC kiểm toán.
- **Thông qua Quyết định kiến trúc [002-chuyen-sang-thu-thap-du-lieu-thu-cong](docs/decisions/002-chuyen-sang-thu-thap-du-lieu-thu-cong.md)**:
  - Dừng việc mở rộng các web crawler tự động cho 60 website khác nhau để tránh sa đà vào bài toán phụ.
  - Người thực hiện chuyển sang tải trực tiếp BCTN toàn văn từ website IR chính thức của từng doanh nghiệp về `data/raw/pdf/`, đặt tên `<MA_CK>_BCTN_<nam>.pdf`.
- **Cập nhật đồng bộ hệ thống tài liệu**:
  - `docs/ROADMAP.md`: Điều chỉnh bước 1 Giai đoạn 2 sang thu thập thủ công có kiểm định.
  - `CLAUDE.md`: Cập nhật quy tắc quản lý tài liệu và quy trình phiên làm việc.
  - `README.md`: Cập nhật phương thức thu thập, schema metadata và tiêu chí hoàn thành.
  - `docs/STATUS.md`: Ghi đè phản ánh trạng thái mới nhất.
- **Xây dựng module xác thực Ingestion tự động (`src/crawl/ingest.py`)**:
  - Quét toàn bộ thư mục `data/raw/pdf/`, mở PDF bằng PyMuPDF, đếm số trang, kiểm tra text layer, tính SHA-256 khử trùng lặp và tự động cập nhật `data/metadata.csv`.

## 3. Lỗi / Vấn đề gặp phải & Cách xử lý
- **Lỗi nhận nhầm BCTN 2024 của Vinamilk**: Do đường dẫn Cloudfront chứa timestamp epoch `1398182024_...`, crawler nhận nhầm số `2024`. Đã xử lý bằng cách viết lại bộ lọc trong `ir_crawler.py` để ưu tiên bóc tách từ microsite chuyên biệt `/bao-cao/2024/`.
- **Lỗi tải nhầm công văn ngắn của GAS**: File tải về chỉ có 1-2 trang thông báo phát hành. Đã làm rõ lý do cần người dùng tự kiểm tra khi tải để lấy đúng cuốn BCTN dày 100-250 trang.

## 4. Vấn đề và chưa chắc chắn
- BCTN 2025 của một số doanh nghiệp có thể chưa công bố vào thời điểm hiện tại; cần kiểm tra trực tiếp từng công ty khi tải.

## 5. Lệnh tái lập kết quả
```bash
# Kiểm tra ingestion và đồng bộ metadata cho các file hiện có
.venv\Scripts\python.exe -m src.crawl.ingest --help
.venv\Scripts\python.exe -m src.crawl.ingest
```

## 6. Kế hoạch phiên tiếp theo
- [ ] Người dùng tải BCTN các công ty trong danh mục tham chiếu `configs/sources.yaml` vào `data/raw/pdf/`.
- [ ] Chạy `python -m src.crawl.ingest` để xác thực toàn bộ đạt mốc 100+ PDF BCTN.
- [ ] Xây dựng module tiền xử lý trong `src/preprocess/` (tách PDF thành ảnh trang DPI 150-200 và text thô từng trang).
