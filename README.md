# RAG đa phương thức cho báo cáo tài chính tiếng Việt

Đồ án tốt nghiệp: xây dựng và đánh giá hệ thống hỏi đáp trên báo cáo tài chính / báo cáo thường niên tiếng Việt (có bảng, biểu đồ, hình) bằng RAG đa phương thức.

> Tên tiếng Anh: *Multimodal Retrieval-Augmented Generation for Vietnamese Financial Reports: Benchmark and Comparative Study*

## Câu hỏi nghiên cứu

Với báo cáo tài chính tiếng Việt, cách tiếp cận nào cho kết quả tốt hơn ở từng loại câu hỏi (văn bản, bảng, biểu đồ, nhiều trang), và đánh đổi về chi phí ra sao?

## Ba pipeline cần so sánh

1. **Pipeline 1 - parse-then-retrieve (text-centric):** phát hiện bố cục bằng **D-FINE X** đã fine-tune ([HF: ducnhan0804/dfine-x-obj-detection](https://huggingface.co/ducnhan0804/dfine-x-obj-detection), chạy qua ONNX; vùng table / figure / icon) → trích nội dung theo vùng từ text layer PDF (PyMuPDF, Docling TableFormer dự phòng; OCR chỉ khi thiếu text layer) → bảng sang markdown/HTML, biểu đồ cắt riêng cho VLM sinh caption + số liệu → chunk theo element → hybrid BM25 + dense (bge-m3) → RRF → rerank (bge-reranker-v2-m3) → LLM/VLM sinh đáp án. Chi tiết: [decision 003](docs/decisions/003-tich-hop-dfine-x-vao-pipeline-1.md).
2. **Pipeline 2 - vision-native:** embed ảnh từng trang bằng ColPali/ColQwen → truy xuất trang (MaxSim) → VLM sinh đáp án từ ảnh trang.
3. **Pipeline 3 - hybrid + router:** kết hợp điểm hai nhánh hoặc router chọn nhánh theo loại câu hỏi / loại trang (đặc trưng loại trang lấy từ D-FINE).

Cả ba pipeline dùng chung giao diện và chung một VLM sinh đáp án để so sánh công bằng (xem `docs/ROADMAP.md`).

## Input / Output

- **Input:** kho PDF báo cáo tài chính/thường niên (100-300 tài liệu) và câu hỏi tiếng Việt, ví dụ "Doanh thu thuần năm 2023 của công ty X là bao nhiêu?".
- **Output:** câu trả lời tiếng Việt kèm trích dẫn (tên tài liệu, số trang, vùng bằng chứng trên trang nếu có) và danh sách top-k trang truy xuất.
- **Sản phẩm của đồ án:** benchmark hỏi đáp tiếng Việt, bảng so sánh pipeline, phân tích lỗi, mã nguồn, ứng dụng demo hiển thị trang nguồn.

## Phần cứng

Mọi bước chạy trên **server khoảng 10 GB VRAM trống**. Các model lớn (ColQwen2, VLM) chạy tuần tự theo pha; VLM 7B dùng bản 4-bit (AWQ). Máy cá nhân (RTX 2050 4 GB) chỉ để soạn code và xem kết quả. Xem [decision 004](docs/decisions/004-chien-luoc-tinh-toan-gpu-4gb.md).

## Cấu trúc thư mục

```
.
├── README.md
├── CLAUDE.md                  # ngữ cảnh và quy tắc làm việc cho Claude
├── requirements.txt
├── configs/
│   └── sources.yaml           # danh sách nguồn và danh sách công ty cần tải
├── data/                      # KHÔNG commit (đã có trong .gitignore)
│   ├── raw/pdf/               # PDF gốc: <MA_CK>_BCTN_<nam>.pdf
│   ├── pages/                 # ảnh trang: <doc_id>/p<n>.png (150 DPI)
│   ├── text/                  # <doc_id>/p<n>.{txt,md,json} (text, markdown, block + bbox)
│   ├── layout/                # <doc_id>/p<n>.json: vùng D-FINE X (table/figure/icon)   [dự kiến]
│   ├── crops/                 # ảnh cắt vùng figure cho VLM caption                    [dự kiến]
│   ├── parsed/                # <doc_id>.jsonl: element text/heading/table/figure + bbox [dự kiến]
│   ├── index/                 # BM25, Qdrant, index ColQwen                              [dự kiến]
│   └── metadata.csv           # bảng metadata tài liệu
├── models/                    # KHÔNG commit: dfine_x_bctn/model.onnx, ...
├── src/
│   ├── crawl/                 # ingest.py: xác thực PDF tải thủ công → metadata.csv
│   ├── preprocess/            # extract_pages.py: PDF → ảnh trang, text/md/json
│   ├── layout/                # detect.py, visualize.py: D-FINE X inference           [dự kiến]
│   ├── parse/                 # build_elements.py, caption_figures.py                  [dự kiến]
│   ├── pipelines/             # base.py, p1_text, p2_vision, p3_hybrid
│   ├── benchmark/             # sinh, lọc, duyệt câu hỏi
│   └── eval/                  # script đánh giá
├── notebooks/                 # notebook khám phá dữ liệu, kiểm tra nhanh
├── experiments/               # mỗi thí nghiệm một thư mục: config, seed, kết quả
└── docs/
    ├── ROADMAP.md             # kế hoạch chi tiết 7 giai đoạn
    ├── STATUS.md              # trạng thái hiện tại
    ├── worklog/               # nhật ký từng phiên làm việc
    ├── decisions/             # quyết định thiết kế và lý do
    ├── data/sources.md        # nguồn dữ liệu, điều khoản
    └── papers/                # ghi chú đọc paper
```

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Hoặc dùng `uv sync` (xem [decision 001](docs/decisions/001-su-dung-pyproject-toml-va-uv.md)). Phụ thuộc hiện có đủ cho ingest và tiền xử lý. Các bước sau sẽ thêm: `onnxruntime-gpu` (D-FINE), `docling`, `FlagEmbedding` (bge-m3, reranker), `rank-bm25` cùng bộ tách từ tiếng Việt, `qdrant-client`, `colpali-engine`, `gradio`.

## Giai đoạn hiện tại: Giai đoạn 2 – dữ liệu, parse bố cục, pipeline 1

Trạng thái chi tiết xem [`docs/STATUS.md`](docs/STATUS.md).

### Phương thức thu thập
Theo Quyết định kiến trúc [002-chuyen-sang-thu-thap-du-lieu-thu-cong](docs/decisions/002-chuyen-sang-thu-thap-du-lieu-thu-cong.md), dự án áp dụng phương thức **thu thập thủ công có kiểm định (curated collection)** thay vì cào web tự động. Người thực hiện tải trực tiếp tệp BCTN toàn văn từ website IR chính thức của từng doanh nghiệp hoặc sở giao dịch (HOSE/HNX) về thư mục `data/raw/pdf/`.

Cách tiếp cận này đảm bảo 100% tài liệu thu thập là bản Digital PDF chất lượng cao (vector graphics, text selectable, đầy đủ biểu đồ trực quan), loại bỏ hoàn toàn các lỗi cào nhầm file văn bản ngắn hoặc bị tường lửa chặn.

### Phạm vi thu thập
- 30-60 công ty, đa ngành (ngân hàng, công nghệ, thực phẩm, bán lẻ, thép, bất động sản, năng lượng, logistics...).
- Mỗi công ty: Báo cáo thường niên (BCTN) của 2-3 năm gần nhất (2023, 2024, 2025).
- 100% tệp là bản Digital PDF có text layer và visual graphics sắc nét.

### Quy ước đặt tên
`<MA_CK>_BCTN_<nam>.pdf`, ví dụ `VNM_BCTN_2024.pdf`, `FPT_BCTN_2025.pdf`.

### Xử lý & Xác thực tự động (Ingestion)
Sau khi đưa file vào `data/raw/pdf/`, chạy script ingestion:
```bash
python -m src.crawl.ingest
```
Script sẽ tự động:
1. Mở và kiểm tra cấu trúc từng file PDF bằng PyMuPDF (`fitz`).
2. Đếm số trang thực tế.
3. Kiểm tra sự tồn tại của text layer (`has_text_layer`).
4. Tính mã băm `sha256` để loại trừ trùng lặp nội dung.
5. Tra cứu thông tin công ty và ngành từ `configs/sources.yaml` để cập nhật đồng bộ vào `data/metadata.csv`.

### Schema `data/metadata.csv`

| Cột | Ý nghĩa |
| --- | --- |
| `doc_id` | Tên file không có đuôi, ví dụ `VNM_BCTN_2024` |
| `ticker` | Mã chứng khoán |
| `company` | Tên công ty |
| `industry` | Ngành |
| `doc_type` | `BCTN` (Báo cáo thường niên) |
| `year` | Năm báo cáo |
| `num_pages` | Số trang |
| `has_text_layer` | `true`/`false` |
| `source_url` | URL nguồn tải |
| `source_name` | Nguồn (ir / hose / hnx) |
| `sha256` | Băm nội dung file để phát hiện trùng |
| `downloaded_at` | Thời điểm ghi nhận (ISO 8601) |

### Tiêu chí hoàn thành bước thu thập

- [ ] Có ít nhất 100 PDF BCTN hợp lệ, phủ ít nhất 8 ngành kinh tế.
- [ ] `metadata.csv` đầy đủ, không có dòng trùng `sha256`.
- [ ] 100% file mở được bằng PyMuPDF, xác định được số trang và text layer.
- [ ] Ảnh từng trang đã tạo (DPI 150-200) và text thô đã trích vào `data/pages/` và `data/text/`.

## Lộ trình tổng quát (18 tuần)

| Giai đoạn | Tuần | Công việc |
| --- | --- | --- |
| 1 | 1-2 | Phạm vi, đọc paper, baseline RAG văn bản |
| **2** | **3-5** | **Thu thập dữ liệu, parse bố cục (D-FINE X), pipeline 1** |
| 3 | 6-8 | Pipeline 2 (ColQwen + VLM), kiểm chứng trên ViDoRe |
| 4 | 9-11 | Xây benchmark tiếng Việt |
| 5 | 12-14 | Cải tiến (finetune/router/nén index), pipeline 3 |
| 6 | 15-16 | Thí nghiệm cuối, ablation, phân tích lỗi |
| 7 | 17-18 | Demo, báo cáo, bảo vệ |

Kế hoạch chi tiết từng giai đoạn (các bước, đầu ra, tiêu chí xong) xem [`docs/ROADMAP.md`](docs/ROADMAP.md). Trạng thái hiện tại xem [`docs/STATUS.md`](docs/STATUS.md).

## Đánh giá

- **Retrieval (mức trang):** Recall@1/3/5, nDCG@5, MRR, tách theo loại câu hỏi (văn bản, bảng, biểu đồ, đa trang, nhiều tài liệu).
- **Sinh đáp án:** so khớp số liệu (chuẩn hóa đơn vị), LLM-as-judge (hiệu chỉnh bằng 100 câu chấm tay), faithfulness.
- **Trích dẫn:** citation precision/recall mức trang; IoU vùng bằng chứng (pipeline có bbox).
- **Chi phí hệ thống:** độ trễ p50/p95, dung lượng index, VRAM, thời gian lập chỉ mục, chi phí API (ghi rõ phần cứng).
- **Thành phần:** mAP của D-FINE X; tỷ lệ bảng/ô parse đúng trên trang khó.

## Ghi chú về dữ liệu

Dữ liệu là tài liệu công bố công khai của doanh nghiệp. Repo **không chứa** file PDF; chỉ chứa mã nguồn, cấu hình và danh sách nguồn để tái lập việc tải.
