# 002-chuyen-sang-thu-thap-du-lieu-thu-cong

- **Ngày:** 2026-10-30
- **Trạng thái:** Đã duyệt
- **Tác giả:** Người dùng & Claude

## 1. Ngữ cảnh & Đặt vấn đề
Giai đoạn 2 của đồ án yêu cầu thu thập 100-300 tệp PDF Báo cáo thường niên (BCTN) từ 30-60 công ty niêm yết trên thị trường chứng khoán Việt Nam (HOSE, HNX) cho 2-3 năm gần nhất.

Ban đầu, dự án dự định xây dựng hệ thống tự động cào dữ liệu (`src/crawl/`) từ các trang quan hệ nhà đầu tư (IR) và cổng thông tin HOSE. Tuy nhiên, qua triển khai thực nghiệm trên Batch 1 (9 công ty), nhóm nhận thấy:
- **Đa dạng và phức tạp về công nghệ web:** Mỗi doanh nghiệp sử dụng một nền tảng khác nhau (Angular SPA như Vietcombank, Adobe Experience Manager như Techcombank, React client-side rendering như MWG, hoặc chặn bot bằng Cloudflare WAF như Vinhomes).
- **Rủi ro sai lệch dữ liệu cao:** Quét tự động dễ nhận nhầm file thông báo ngắn (1-2 trang) thay vì toàn văn BCTN (100-200 trang), hoặc nhầm năm do timestamp trong URL hash.
- **Lãng phí thời gian vào bài toán phụ:** Người dùng vẫn phải mở trình duyệt kiểm tra thủ công (thẩm định nguồn) từng URL. Nếu đã mở trình duyệt để thẩm định, việc nhấn nút tải file trực tiếp chỉ mất 2-3 giây nhưng đảm bảo tính chính xác 100%. Đồ án tập trung vào **RAG đa phương thức (Vision-native ColPali vs. Parse-then-retrieve) và Benchmark hỏi đáp tiếng Việt**, không phải đề tài về Web Scraping.

## 2. Các phương án cân nhắc

### Phương án 1: Tiếp tục phát triển và duy trì hệ thống crawler tự động
- **Ưu điểm:** Tự động hóa hoàn toàn sau khi viết xong code.
- **Nhược điểm:** Tốn quá nhiều tuần để xử lý từng trường hợp dị biệt (Headless browser Playwright, vượt Cloudflare, giải mã API nội bộ). Dễ bị gãy khi website doanh nghiệp thay đổi giao diện. Tốn tài nguyên không cần thiết cho mục tiêu chính của đồ án.

### Phương án 2: Chuyển sang thu thập thủ công có kiểm định kết hợp script chuẩn hóa tự động (Được chọn)
- **Ưu điểm:** 
  - Đảm bảo 100% tài liệu tải về là toàn văn Digital PDF chất lượng cao, đúng doanh nghiệp, đúng năm tài chính.
  - Tiết kiệm thời gian, hoàn thành toàn bộ kho 100-150 BCTN chỉ trong 1-2 ngày tải.
  - Giữ vững tiến độ 18 tuần để tập trung tài nguyên vào: Benchmark, Fine-tuning ColQwen, Xây dựng Router và Đánh giá RAG.
- **Nhược điểm:** Cần công sức tải tay ban đầu của người thực hiện (~1-2 buổi).

## 3. Quyết định được chọn
Chính thức dừng việc mở rộng module web crawler tự động (`ir_crawler.py`, `hose_crawler.py`). Chuyển sang quy trình:
1. Người dùng tải trực tiếp tệp BCTN từ website chính thức của doanh nghiệp hoặc sở giao dịch về thư mục `data/raw/pdf/`.
2. Đặt tên tệp theo quy ước chuẩn: `<MA_CK>_BCTN_<nam>.pdf`.
3. Xây dựng script tiện ích ingestion tự động (`src/crawl/ingest.py`): quét toàn bộ thư mục `data/raw/pdf/`, kiểm tra tính hợp lệ của PDF, tính mã băm SHA-256, đếm trang, kiểm tra text layer và đồng bộ vào `data/metadata.csv`.

## 4. Lý do kỹ thuật & Biện luận
- Đồ án tốt nghiệp đại học có thời lượng giới hạn (18 tuần), trọng tâm là so sánh các mô hình RAG đa phương thức và đóng góp bộ benchmark hỏi đáp tiếng Việt.
- Dữ liệu đầu vào cần có chất lượng cao nhất (vector text layer, ảnh biểu đồ rõ nét); tải thủ công cho phép người làm đồ án chủ động lọc bỏ ngay các bản scan mờ hoặc file công bố thông tin ngắn bị tải nhầm.

## 5. Hệ quả & Đánh đổi
- **Hệ quả tích cực:** Rút ngắn thời gian giai đoạn thu thập dữ liệu; loại bỏ hoàn toàn các lỗi cào web khó chịu; kho dữ liệu đạt độ tin cậy tuyệt đối.
- **Rủi ro / Giới hạn chấp nhận:** Không thể khoe tính năng "tự động cào dữ liệu từ 60 website" trong báo cáo đồ án.
- **Kế hoạch ứng phó:** Trình bày rõ trong báo cáo rằng dữ liệu được thu thập có kiểm định chất lượng (curated dataset) theo tiêu chuẩn xây dựng benchmark học thuật.
