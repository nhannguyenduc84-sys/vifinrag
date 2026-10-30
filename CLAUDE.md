# CLAUDE.md

Tệp này cho Claude biết dự án là gì, đang ở đâu và làm việc theo quy tắc nào. Đọc `README.md` để biết chi tiết cấu trúc và lộ trình.

## Dự án

Đồ án tốt nghiệp đại học: hệ thống hỏi đáp RAG đa phương thức trên **báo cáo tài chính / thường niên tiếng Việt** (PDF có bảng, biểu đồ, hình). Đóng góp chính: benchmark hỏi đáp tiếng Việt và so sánh 3 pipeline (parse-then-retrieve, vision-native ColPali/ColQwen, hybrid + router).

- Người dùng là sinh viên, nói tiếng Việt. **Trả lời bằng tiếng Việt**, ngắn gọn, đi thẳng vào việc. Tên biến, tên hàm, comment trong code dùng tiếng Anh.
- Có GPU cá nhân (VRAM chưa ghi; hỏi lại nếu cần quyết định kích thước model).

## Giai đoạn hiện tại

**Thu thập dữ liệu (crawl).** Mục tiêu: 100-300 PDF báo cáo tài chính/thường niên của 30-60 công ty niêm yết Việt Nam, đa ngành, 2-3 năm gần nhất, ưu tiên PDF có text layer.

Việc cần làm, theo thứ tự:

1. Tạo khung dự án: cấu trúc thư mục như trong `README.md`, `requirements.txt`, `.gitignore` (bỏ `data/`, `.venv/`, file model/checkpoint).
2. Viết `configs/sources.yaml`: danh sách công ty (mã CK, tên, ngành) và nguồn cho từng công ty.
3. Với **từng nguồn**: đọc `robots.txt` và điều khoản sử dụng, kiểm tra cấu trúc trang thực tế, rồi mới viết crawler trong `src/crawl/`. Báo cho người dùng nếu một nguồn cấm crawl hoặc cần đăng nhập, không tự tìm cách lách.
4. Chạy crawl thử trên 5-10 công ty trước khi chạy toàn bộ.
5. Sau khi tải: kiểm tra file hợp lệ, đếm trang, kiểm tra text layer, tính `sha256`, ghi `data/metadata.csv` và `data/crawl_log.csv`.
6. Tiền xử lý: tách PDF thành ảnh từng trang (DPI 150-200) và text thô theo trang, mã trang `<doc_id>_p<số trang>`.

Tiêu chí xong của giai đoạn này nằm ở mục "Tiêu chí hoàn thành bước thu thập" trong `README.md`.

## Quy tắc khi crawl

- Chỉ tải tài liệu **công bố công khai**. Tôn trọng `robots.txt` và điều khoản sử dụng. Không vượt đăng nhập, paywall, CAPTCHA.
- Giới hạn tốc độ (khoảng 1-2 giây mỗi request mỗi domain), đặt User-Agent rõ ràng, retry có backoff, tải song song ở mức thấp.
- Idempotent: chạy lại không tải trùng; bỏ qua file đã có, phát hiện trùng bằng `sha256`.
- Mọi kết quả (thành công, lỗi, lý do) ghi vào `data/crawl_log.csv`.
- Không hard-code danh sách công ty hay URL trong code; đưa vào `configs/sources.yaml`.
- Không commit dữ liệu (`data/`) lên Git. Chỉ commit code, cấu hình, danh sách nguồn.
- Quy ước tên file: `<MA_CK>_<loai>_<nam>.pdf`, `loai` là `BCTN` hoặc `BCTC`.

## Quy ước mã nguồn

- Python 3.10+, có type hints cho hàm công khai; format bằng `ruff` hoặc `black`.
- Mỗi script chạy được từ dòng lệnh (`python -m src.crawl.<ten> --help`), có tham số thay vì sửa code.
- Dùng `logging` thay vì `print` ở các script chạy lâu; dùng `tqdm` cho tiến trình.
- Cố định phiên bản trong `requirements.txt` khi đã chạy ổn.
- Mỗi thí nghiệm sau này lưu vào `experiments/<ten>/` gồm config, seed, kết quả thô.

## Quy trình một phiên làm việc và ghi nhật ký

Bạn không nhớ gì giữa các phiên; mọi thứ cần nhớ phải nằm trong file.

**Đầu phiên:**
1. Đọc `CLAUDE.md`, `README.md`, `docs/STATUS.md` và file mới nhất trong `docs/worklog/`.
2. Nhắc lại cho người dùng 2-3 dòng: hiện đang ở đâu, việc tiếp theo là gì, rồi chờ xác nhận trước khi làm việc lớn.

**Trong phiên:**
- Làm từng việc nhỏ có tiêu chí xong rõ; commit nhỏ, mỗi commit một việc, message rõ nghĩa.
- Quyết định thiết kế quan trọng (chọn nguồn, chọn model, đổi cấu trúc dữ liệu) ghi vào `docs/decisions/` theo mẫu `docs/decisions/TEMPLATE.md`.

**Cuối phiên (bắt buộc):**
1. Tạo file nhật ký `docs/worklog/YYYY-MM-DD_<chu-de>.md` theo mẫu `docs/worklog/TEMPLATE.md`.
2. Ghi đè `docs/STATUS.md` cho khớp trạng thái mới (giữ ngắn, tối đa một trang).
3. Cập nhật `docs/data/sources.md` nếu có thêm nguồn dữ liệu hoặc ghi chú điều khoản.

**Cấu trúc docs:**

```
docs/
├── ROADMAP.md         # kế hoạch chi tiết 7 giai đoạn (chỉ sửa khi có quyết định đổi kế hoạch)
├── STATUS.md          # trạng thái hiện tại, ghi đè mỗi cuối phiên
├── worklog/           # mỗi phiên một file: YYYY-MM-DD_<chu-de>.md (không sửa file cũ)
├── decisions/         # NNN-<ten>.md: quyết định và lý do
├── data/sources.md    # nguồn dữ liệu, điều khoản, ngày kiểm tra
└── papers/            # ghi chú đọc paper
```

**Nguyên tắc ghi chép:**
- Chỉ ghi điều đã thực sự làm và chạy được. Việc chưa kiểm tra ghi vào mục "Vấn đề và chưa chắc chắn".
- Số liệu lấy từ lệnh hoặc file thật (đếm file, đọc log), không ước lượng.
- Ghi cả lỗi và thất bại, kèm cách đã thử.
- Không sửa nhật ký cũ; muốn đính chính thì ghi ở phiên mới.
- Mỗi nhật ký có lệnh chạy lại được kết quả và danh sách việc tiếp theo.

## Những điều không được làm

- Không tạo, sửa, hay chạy bất kỳ thứ gì trên **tập test** của benchmark (sẽ có ở giai đoạn 4); tập test chỉ chạy ở giai đoạn 6.
- Không bịa số liệu, kết quả thí nghiệm, hay metadata của tài liệu. Không biết thì để trống hoặc hỏi.
- Không xóa hoặc ghi đè dữ liệu gốc trong `data/raw/` khi chưa hỏi.
- Không chạy lệnh tốn tài nguyên lớn (tải model hàng chục GB, embed toàn bộ kho) khi chưa báo trước ước lượng.

## Cách làm việc với người dùng

- Trước một việc lớn (vài file hoặc vài bước), nêu ngắn gọn kế hoạch rồi làm; hỏi lại khi có lựa chọn ảnh hưởng đến thiết kế (ví dụ nguồn nào, cách đặt tên, chọn model).
- Khi xong một bước, báo kết quả bằng 1-3 câu: đã làm gì, chạy thế nào, còn gì chưa chắc.
- Nếu môi trường không có mạng tới một trang (bị chặn), nói rõ và đưa lệnh để người dùng tự chạy trên máy của họ, đừng thử cách vòng.
- Giải thích ngắn gọn lý do kỹ thuật khi đề xuất, vì người dùng cần hiểu để bảo vệ đồ án.

## Lộ trình toàn dự án

Kế hoạch đầy đủ 7 giai đoạn (mục tiêu, các bước, đầu ra, tiêu chí xong) nằm ở **`docs/ROADMAP.md`**. Giai đoạn đang làm ghi trong `docs/STATUS.md`.

Quy tắc:
- Khi bắt đầu một giai đoạn mới, đọc **đúng phần giai đoạn đó** trong `docs/ROADMAP.md`, nêu kế hoạch cho người dùng duyệt rồi mới làm.
- Không làm trước các giai đoạn sau khi giai đoạn hiện tại chưa đạt "Xong khi".
- Khi giai đoạn hiện tại xong, cập nhật `docs/STATUS.md` và mục "Giai đoạn hiện tại" ở trên cho khớp.
- Nếu kế hoạch cần đổi (trễ tiến độ, đổi hướng), ghi quyết định vào `docs/decisions/` rồi sửa `docs/ROADMAP.md`; không tự ý đổi.

Tóm tắt các giai đoạn (chi tiết ở ROADMAP):

1. Tuần 1-2: phạm vi, đọc paper, baseline RAG văn bản.
2. Tuần 3-5: thu thập dữ liệu, parse, pipeline 1 (giai đoạn 2 trong ROADMAP, giai đoạn hiện tại).
3. Tuần 6-8: pipeline 2 vision-native (ColPali/ColQwen), kiểm chứng trên ViDoRe.
4. Tuần 9-11: benchmark tiếng Việt, khóa tập test.
5. Tuần 12-14: cải tiến (finetune/router/nén index), pipeline 3, chỉ chạy trên tập dev.
6. Tuần 15-16: thí nghiệm cuối trên tập test, phân tích lỗi.
7. Tuần 17-18: demo, báo cáo, bảo vệ.
