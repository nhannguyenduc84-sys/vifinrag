# CLAUDE.md

Tệp này cho Claude biết dự án là gì, đang ở đâu và làm việc theo quy tắc nào. Đọc `README.md` để biết chi tiết cấu trúc và lộ trình.

## Dự án

Đồ án tốt nghiệp đại học (đề cương: `Project 3_Nguyễn Đức Nhẫn.pdf`): **xây dựng và đánh giá** hệ thống hỏi đáp RAG đa phương thức trên **báo cáo tài chính / thường niên tiếng Việt** (PDF có bảng, biểu đồ, hình). Bốn mục tiêu: (1) benchmark hỏi đáp tiếng Việt; (2) cài đặt và so sánh 3 pipeline (text-centric, vision-native ColPali/ColQwen, hybrid + router); (3) đánh giá truy xuất, câu trả lời, độ chính xác trích dẫn, chi phí; (4) demo hiển thị trang nguồn.

- Người dùng là sinh viên, nói tiếng Việt. **Trả lời bằng tiếng Việt**, ngắn gọn, đi thẳng vào việc. Tên biến, tên hàm, comment trong code dùng tiếng Anh.
- Phần cứng: chạy trên **server khoảng 10 GB VRAM trống**. Model lớn chạy tuần tự theo pha, VLM 7B dùng 4-bit (xem [004](docs/decisions/004-chien-luoc-tinh-toan-gpu-4gb.md)). Máy cá nhân RTX 2050 4 GB chỉ để soạn code.
- Model bố cục: **D-FINE X** do người dùng fine-tune, ở HF [`ducnhan0804/dfine-x-obj-detection`](https://huggingface.co/ducnhan0804/dfine-x-obj-detection) (`best_stg2.pth`; lớp 1 Figure, 2 Icon, 3 Table, bỏ lớp 0; repo train `d:\Project\D-FINE`, dataset 676 ảnh). Tích hợp theo [003](docs/decisions/003-tich-hop-dfine-x-vao-pipeline-1.md): export **ONNX** rồi chạy bằng onnxruntime; **không** import wrapper HF vào dự án (xung đột tên package `src`). D-FINE chỉ phát hiện **vùng**, nội dung lấy từ text layer PDF; tiền xử lý không Normalize.

## Giai đoạn hiện tại

**Giai đoạn 2 (ROADMAP): thu thập dữ liệu, parse bố cục bằng D-FINE X, pipeline 1.** Chi tiết các bước 2.0–2.6 ở `docs/ROADMAP.md`. Trạng thái thực tế ở `docs/STATUS.md`.

Tóm tắt thứ tự:

1. Khung dự án, `configs/sources.yaml`, `src/crawl/ingest.py`, `src/preprocess/extract_pages.py`: *đã xong*.
2. Thu thập (song song, liên tục): người dùng tải BCTN về `data/raw/pdf/` (tên `<MA_CK>_BCTN_<nam>.pdf`), chạy `python -m src.crawl.ingest`. Cần ≥ 100 PDF trước khi sang GĐ 4. Theo [002](docs/decisions/002-chuyen-sang-thu-thap-du-lieu-thu-cong.md).
3. Làm bù GĐ 1: 20 câu hỏi mẫu, baseline P1-v0, ghi chú paper.
4. D-FINE X: export ONNX từ checkpoint HF → kiểm tra tương đương torch/ONNX → `src/layout/detect.py` → `data/layout/`; đánh giá mAP trên tập test.
5. Trích element theo vùng (`src/parse/`) → `data/parsed/*.jsonl`; caption biểu đồ bằng VLM.
6. Chunk + index (BM25 + bge-m3) + truy xuất RRF + rerank + sinh có trích dẫn.

Tiêu chí xong: mục "Xong khi" của Giai đoạn 2 trong `docs/ROADMAP.md` và mục "Tiêu chí hoàn thành bước thu thập" trong `README.md`.

## Quy tắc thu thập và quản lý tài liệu

- Chỉ thu thập tài liệu **công bố công khai** của doanh nghiệp niêm yết (theo Thông tư 96/2020/TT-BTC).
- Ưu tiên tối đa **Báo cáo thường niên (BCTN)** toàn văn dạng Digital PDF (vector text layer, ảnh biểu đồ, infographic sắc nét) để phục vụ bài toán RAG đa phương thức và Vision-native (ColPali). Tránh lấy nhầm thông báo ngắn (1-2 trang) hoặc bản scan mờ.
- Quy ước tên file chuẩn bắt buộc: `<MA_CK>_BCTN_<nam>.pdf` (ví dụ: `VNM_BCTN_2024.pdf`, `FPT_BCTN_2025.pdf`).
- Không commit dữ liệu (`data/`) lên Git. Chỉ commit code, cấu hình, danh sách nguồn.
- Mọi tài liệu đưa vào kho phải được xác thực qua script `ingest.py` để ghi nhận đầy đủ vào `data/metadata.csv`.

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
- Không chạy lệnh tốn tài nguyên lớn (tải model hàng chục GB, embed toàn bộ kho, chạy D-FINE/VLM toàn kho) khi chưa báo trước ước lượng.
- Không ghi vào docs hay báo cáo những thành tích chưa có bằng chứng (ví dụ mAP của D-FINE khi chưa có log, số ngành/số tài liệu khác với `metadata.csv`).

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
2. Tuần 3-5: thu thập dữ liệu, parse bố cục (D-FINE X), pipeline 1 (giai đoạn hiện tại).
3. Tuần 6-8: pipeline 2 vision-native (ColPali/ColQwen), kiểm chứng trên ViDoRe.
4. Tuần 9-11: benchmark tiếng Việt, khóa tập test.
5. Tuần 12-14: cải tiến (finetune/router/nén index), pipeline 3, chỉ chạy trên tập dev.
6. Tuần 15-16: thí nghiệm cuối trên tập test, phân tích lỗi.
7. Tuần 17-18: demo, báo cáo, bảo vệ.
