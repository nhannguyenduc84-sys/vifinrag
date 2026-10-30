# RAG đa phương thức cho báo cáo tài chính tiếng Việt

Đồ án tốt nghiệp: xây dựng và đánh giá hệ thống hỏi đáp trên báo cáo tài chính / báo cáo thường niên tiếng Việt (có bảng, biểu đồ, hình) bằng RAG đa phương thức.

> Tên tiếng Anh: *Multimodal Retrieval-Augmented Generation for Vietnamese Financial Reports: Benchmark and Comparative Study*

## Câu hỏi nghiên cứu

Với báo cáo tài chính tiếng Việt, cách tiếp cận nào cho kết quả tốt hơn ở từng loại câu hỏi (văn bản, bảng, biểu đồ, nhiều trang), và đánh đổi về chi phí ra sao?

## Ba pipeline cần so sánh

1. **Pipeline 1 - parse-then-retrieve:** layout analysis + OCR (Docling/MinerU, PaddleOCR) → text/markdown → hybrid BM25 + dense (bge-m3) → rerank → LLM.
2. **Pipeline 2 - vision-native:** embed ảnh từng trang bằng ColPali/ColQwen → truy xuất trang → VLM (Qwen-VL) sinh đáp án.
3. **Pipeline 3 - hybrid + router:** kết hợp hai nhánh hoặc chọn nhánh theo loại câu hỏi.

## Input / Output

- **Input:** kho PDF báo cáo tài chính/thường niên (100-300 tài liệu) và câu hỏi tiếng Việt.
- **Output:** câu trả lời kèm trích dẫn (tài liệu, số trang), danh sách trang truy xuất.
- **Sản phẩm nghiên cứu:** benchmark hỏi đáp tiếng Việt, kết quả so sánh pipeline, phân tích lỗi, mã nguồn, demo.

## Cấu trúc thư mục

```
.
├── README.md
├── CLAUDE.md                  # ngữ cảnh và quy tắc làm việc cho Claude
├── requirements.txt
├── configs/
│   └── sources.yaml           # danh sách nguồn và danh sách công ty cần tải
├── data/                      # KHÔNG commit (đã có trong .gitignore)
│   ├── raw/pdf/               # PDF gốc: <MA_CK>_<loai>_<nam>.pdf
│   ├── pages/                 # ảnh từng trang: <ten_tai_lieu>/p<so_trang>.png
│   ├── text/                  # text thô từng trang
│   ├── metadata.csv           # bảng metadata tài liệu
│   └── crawl_log.csv          # nhật ký tải (thành công/lỗi)
├── src/
│   ├── crawl/                 # crawler từng nguồn
│   ├── preprocess/            # PDF → ảnh trang, text
│   ├── pipelines/             # p1_text, p2_vision, p3_hybrid
│   ├── benchmark/             # sinh, lọc, duyệt câu hỏi
│   └── eval/                  # script đánh giá
├── notebooks/
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

Gợi ý `requirements.txt` ban đầu cho bước crawl và tiền xử lý:

```
requests
httpx
beautifulsoup4
lxml
pyyaml
pandas
tqdm
tenacity
pymupdf
pdf2image
```

Bước sau sẽ thêm: `torch`, `transformers`, `colpali-engine`, `docling`, `qdrant-client`, `ragas`.

## Giai đoạn hiện tại: thu thập dữ liệu (tuần 3)

### Nguồn dữ liệu dự kiến

| Nguồn | Ghi chú |
| --- | --- |
| Trang quan hệ nhà đầu tư (IR) của từng công ty | Nguồn gốc, ổn định nhất, nhưng mỗi trang một cấu trúc |
| Sở giao dịch HOSE / HNX | Công bố thông tin của công ty niêm yết |
| CafeF, Vietstock | Tập hợp sẵn, nhưng cần kiểm tra điều khoản và kiểm soát tốc độ |

Trước khi viết crawler cho mỗi nguồn, cần: (1) đọc `robots.txt`, (2) đọc điều khoản sử dụng, (3) kiểm tra cấu trúc trang thực tế. Chỉ tải tài liệu công bố công khai.

### Phạm vi tải

- 30-60 công ty, đa ngành (ngân hàng, bất động sản, bán lẻ, sản xuất, công nghệ...).
- Mỗi công ty: báo cáo thường niên và báo cáo tài chính của 2-3 năm gần nhất.
- Ưu tiên PDF có text layer; loại bản scan chất lượng quá thấp.

### Quy ước đặt tên

`<MA_CK>_<loai>_<nam>.pdf`, trong đó `loai` là `BCTN` (thường niên) hoặc `BCTC` (tài chính); ví dụ `VNM_BCTN_2024.pdf`.

### Schema `data/metadata.csv`

| Cột | Ý nghĩa |
| --- | --- |
| `doc_id` | Tên file không có đuôi, ví dụ `VNM_BCTN_2024` |
| `ticker` | Mã chứng khoán |
| `company` | Tên công ty |
| `industry` | Ngành |
| `doc_type` | `BCTN` hoặc `BCTC` |
| `year` | Năm báo cáo |
| `num_pages` | Số trang |
| `has_text_layer` | `true`/`false` |
| `source_url` | URL tải |
| `source_name` | Nguồn (IR / HOSE / HNX / CafeF / Vietstock) |
| `sha256` | Băm nội dung file để phát hiện trùng |
| `downloaded_at` | Thời điểm tải (ISO 8601) |

### Yêu cầu kỹ thuật cho crawler

- Giới hạn tốc độ (ví dụ 1 request mỗi 1-2 giây mỗi domain), User-Agent rõ ràng.
- Retry có backoff khi lỗi tạm thời; ghi mọi kết quả vào `crawl_log.csv`.
- Có thể chạy lại mà không tải trùng (bỏ qua file đã có, so sánh `sha256`).
- Cấu hình danh sách công ty và nguồn nằm trong `configs/sources.yaml`, không hard-code trong code.
- Sau khi tải: kiểm tra file mở được, đếm trang, kiểm tra text layer, điền `metadata.csv`.

### Tiêu chí hoàn thành bước thu thập

- [ ] Có ít nhất 100 PDF hợp lệ, phủ nhiều ngành.
- [ ] `metadata.csv` đầy đủ, không có dòng trùng `sha256`.
- [ ] `crawl_log.csv` ghi rõ các file lỗi và lý do.
- [ ] Ảnh từng trang đã tạo (DPI 150-200) và text thô đã trích.
- [ ] Danh sách nguồn kèm ghi chú điều khoản sử dụng, để đưa vào báo cáo.

## Lộ trình tổng quát (18 tuần)

| Giai đoạn | Tuần | Công việc |
| --- | --- | --- |
| 1 | 1-2 | Phạm vi, đọc paper, baseline RAG văn bản |
| **2** | **3-5** | **Thu thập dữ liệu, parse, pipeline 1** |
| 3 | 6-8 | Pipeline 2 (ColQwen + VLM), kiểm chứng trên ViDoRe |
| 4 | 9-11 | Xây benchmark tiếng Việt |
| 5 | 12-14 | Cải tiến (finetune/router/nén index), pipeline 3 |
| 6 | 15-16 | Thí nghiệm cuối, ablation, phân tích lỗi |
| 7 | 17-18 | Demo, báo cáo, bảo vệ |

Kế hoạch chi tiết từng giai đoạn (các bước, đầu ra, tiêu chí xong) xem [`docs/ROADMAP.md`](docs/ROADMAP.md). Trạng thái hiện tại xem [`docs/STATUS.md`](docs/STATUS.md).

## Đánh giá

- **Retrieval (mức trang):** Recall@1/3/5, nDCG@5, MRR.
- **Sinh đáp án:** độ chính xác số liệu, LLM-as-judge (hiệu chỉnh bằng chấm tay), faithfulness.
- **Trích dẫn:** tỷ lệ trỏ đúng trang bằng chứng.
- **Hệ thống:** độ trễ, dung lượng index, VRAM.

## Ghi chú về dữ liệu

Dữ liệu là tài liệu công bố công khai của doanh nghiệp. Repo **không chứa** file PDF; chỉ chứa mã nguồn, cấu hình và danh sách nguồn để tái lập việc tải.
