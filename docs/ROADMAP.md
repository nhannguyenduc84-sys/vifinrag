# ROADMAP: kế hoạch thực hiện 18 tuần

Mỗi giai đoạn gồm mục tiêu, các bước (kèm script dự kiến), đầu ra và tiêu chí xong. Giai đoạn đang làm ghi trong `docs/STATUS.md`. **Không làm trước các giai đoạn sau** khi giai đoạn hiện tại chưa đạt tiêu chí xong. Khi bắt đầu giai đoạn mới, nêu kế hoạch cho người dùng duyệt trước.

*Sửa đổi 2026-11-19:*
- Thêm tích hợp D-FINE X từ HF `ducnhan0804/dfine-x-obj-detection` qua ONNX ([003](decisions/003-tich-hop-dfine-x-vao-pipeline-1.md)).
- Toàn bộ tính toán chạy trên server khoảng 10 GB VRAM ([004](decisions/004-chien-luoc-tinh-toan-gpu-4gb.md)).
- Cho phép phát triển pipeline 1 song song với việc tải thêm tài liệu.
- Đối chiếu từng bước với 4 mục tiêu của đề cương.

## Đối chiếu với đề cương (file `Project 3_Nguyễn Đức Nhẫn.pdf`)

| Mục tiêu đề cương | Thực hiện ở | Sản phẩm |
| --- | --- | --- |
| 1. Benchmark hỏi đáp BCTC tiếng Việt | GĐ 4 | `benchmark/*.jsonl`, hướng dẫn duyệt, thống kê, kappa |
| 2. Cài đặt và so sánh 3 pipeline | GĐ 2, 3, 5 | `src/pipelines/p1_text`, `p2_vision`, `p3_hybrid` |
| 3. Đánh giá truy xuất, câu trả lời, trích dẫn, chi phí | GĐ 5 (dev), GĐ 6 (test) | Bảng kết quả, ablation, phân tích lỗi |
| 4. Demo hỏi đáp hiển thị trang nguồn | GĐ 7 | App Gradio/Streamlit |

Output của hệ thống theo đề cương: câu trả lời tiếng Việt, trích dẫn (tên tài liệu, số trang, **vùng bằng chứng nếu có**) và danh sách top-k trang. Pipeline 1 lấy vùng bằng chứng từ bbox của D-FINE/PyMuPDF.

| Giai đoạn | Tuần | Nội dung |
| --- | --- | --- |
| 1 | 1-2 | Chốt phạm vi, đọc paper, baseline RAG văn bản |
| 2 | 3-5 | Thu thập dữ liệu, parse (D-FINE X), pipeline 1 |
| 3 | 6-8 | Pipeline 2 (vision-native), kiểm chứng trên ViDoRe |
| 4 | 9-11 | Xây benchmark tiếng Việt, khóa tập test |
| 5 | 12-14 | Cải tiến và pipeline 3 (chỉ trên dev) |
| 6 | 15-16 | Thí nghiệm cuối trên tập test, phân tích |
| 7 | 17-18 | Demo, báo cáo, bảo vệ |

## Nguyên tắc xuyên suốt

- Dùng Git; cố định phiên bản thư viện và model. Mỗi thí nghiệm lưu config, seed, kết quả thô vào `experiments/<ten>/`.
- **Giao diện chung** cho cả 3 pipeline (`src/pipelines/base.py`):
  ```python
  answer(question: str, top_k: int = 5) -> {
      "retrieved": [{"page_id", "score", "regions": [bbox...]}],
      "answer": str,
      "citations": [{"doc_id", "page", "bbox" | None}],
      "latency_ms": {"retrieve", "rerank", "generate", "total"},
  }
  ```
- Mã trang thống nhất `<doc_id>_p<số trang>` (số trang 1-indexed, khớp `data/pages/<doc_id>/p<n>.png`).
- Một **VLM sinh đáp án chung** cho cả 3 pipeline (xem [004](decisions/004-chien-luoc-tinh-toan-gpu-4gb.md)).
- Mọi con số trong báo cáo phải truy ngược được về file kết quả thô và cấu hình đã lưu.
- Tập test của benchmark bị **khóa** từ cuối giai đoạn 4 và chỉ chạy ở giai đoạn 6.
- Phần cứng: server khoảng 10 GB VRAM. Chạy model lớn **tuần tự theo pha**, không nạp đồng thời; VLM 7B dùng bản 4-bit. Trước mọi job lớn phải báo ước lượng thời gian và dung lượng.

---

## Giai đoạn 1 (tuần 1-2): Chốt phạm vi và dựng baseline

**Mục tiêu:** hiểu bài toán, chuẩn bị môi trường, có một RAG văn bản chạy được đầu-cuối trên vài tài liệu.

1. Đọc ColPali, VisRAG, M3DocRAG, benchmark ViDoRe (thêm: D-FINE, Docling, bge-m3). Mỗi bài ghi 5-10 dòng (bài toán, phương pháp, kết quả, hạn chế) vào `docs/papers/<ten>.md`.
2. Dựng môi trường: Python, PyTorch khớp CUDA, `transformers`, `colpali-engine`, `docling`, Qdrant. Kiểm tra GPU server (khoảng 10 GB trống; ghi tên GPU, CUDA).
3. Chọn 10 báo cáo mẫu (3-4 công ty, 2-3 năm).
4. Baseline (**P1-v0**): PDF → text (PyMuPDF) → chia đoạn cố định → bge-m3 → top-5 → LLM trả lời.
5. Viết tay 20 câu hỏi mẫu (`experiments/seed20/questions.jsonl`), ghi nhận lỗi baseline (đặc biệt bảng và biểu đồ).
6. Chốt với GVHD: domain, số tài liệu, 1-2 điểm đóng góp dự kiến.

**Xong khi:** hỏi được một câu bất kỳ trên bộ mẫu và nhận câu trả lời có trích nguồn; có danh sách lỗi của baseline.

> **Nợ kỹ thuật (2026-11-19):** chưa có ghi chú paper (`docs/papers/` trống), chưa có baseline P1-v0 và 20 câu mẫu. Ba việc này được làm bù trong GĐ 2 (bước 2.0) vì cả ba là mốc so sánh cho pipeline 1.

---

## Giai đoạn 2 (tuần 3-5): Thu thập dữ liệu, parse bố cục và pipeline 1

**Mục tiêu:** có kho tài liệu đủ lớn và pipeline text-centric xử lý được bảng và biểu đồ, trích dẫn được trang và vùng.

**Nguyên tắc song song:** pipeline 1 được phát triển trên kho hiện có (24 tài liệu). Việc tải thêm BCTN chạy song song. Kho phải đủ ≥ 100 tài liệu **trước khi bắt đầu GĐ 4** (benchmark cần kho cố định).

### 2.0 Làm bù GĐ 1 (tuần 3)
- 20 câu hỏi mẫu trên 24 tài liệu hiện có, phủ 4 loại: văn bản, bảng, biểu đồ, đa trang.
- Baseline P1-v0 (chỉ text PyMuPDF, chunk cố định, bge-m3) → `experiments/p1_v0_seed20/`.
- Ghi chú 4 paper chính vào `docs/papers/`.

### 2.1 Thu thập (tuần 3-5, liên tục) – *đang làm*
- Người dùng tải BCTN theo danh mục `configs/sources.yaml` (39 công ty) về `data/raw/pdf/`, tên `<MA_CK>_BCTN_<nam>.pdf`.
- `python -m src.crawl.ingest`: kiểm tra mở được, số trang, text layer, `sha256`, ghi `data/metadata.csv`.
- **Xong khi:** đạt tiêu chí thu thập trong `README.md` (≥ 100 PDF hợp lệ, ≥ 8 ngành, không trùng `sha256`).

### 2.2 Tiền xử lý (tuần 3) – *code đã xong*
- `python -m src.preprocess.extract_pages`: ảnh trang PNG 150 DPI và `.txt/.md/.json` theo trang. Chạy lại mỗi khi có PDF mới (có cache).

### 2.3 Phát hiện bố cục bằng D-FINE X (tuần 4) – chi tiết ở [003](decisions/003-tich-hop-dfine-x-vao-pipeline-1.md)
Checkpoint đã có: HF [`ducnhan0804/dfine-x-obj-detection`](https://huggingface.co/ducnhan0804/dfine-x-obj-detection) (`best_stg2.pth`, ≈ 1 GB; mAP@50 = 0,918 trên valid). Wrapper HF **không import được trực tiếp** vì xung đột tên package `src`, nên dùng ONNX.
1. Trên server, trong repo D-FINE (môi trường riêng): tải checkpoint và 2 file YAML từ HF, thay `configs/dataset/custom_detection.yml` bằng bản HF (`num_classes: 4`), rồi chạy `export_onnx.py --check --simplify` → `models/dfine_x_bctn/model.onnx`. Lệnh cụ thể ở 003 §3.2.
2. Kiểm tra tương đương PyTorch (`torch_inf.py`) với ONNX trên 10 trang → `experiments/dfine_eval/onnx_parity.json`.
3. Viết `src/layout/detect.py` (onnxruntime-gpu): đọc `data/pages/`, ghi `data/layout/<doc_id>/p<n>.json`.
   - Tiền xử lý giống lúc train: resize 640², `/255`, **không Normalize**.
   - Map lớp 1→figure, 2→icon, 3→table; bỏ lớp 0.
   - Ngưỡng theo lớp, NMS, gộp box lồng nhau.
   - Đổi tọa độ `bbox_pdf = bbox_px·72/dpi`. Có cache và `--batch-size`.
   - Ghi `configs/layout.yaml` (repo HF, commit, sha256 ONNX, ngưỡng).
4. Kiểm tra trực quan: `src/layout/visualize.py` vẽ bbox lên 30 trang ngẫu nhiên, người dùng duyệt.
5. Đánh giá detection: mAP và AP/AR **từng lớp trên tập test 103 ảnh** (hiện mới có số trên valid), cùng khoảng 50 trang tự gán nhãn từ kho (công ty ngoài dataset train) → `experiments/dfine_eval/`.
6. Đo thời gian/trang trên server, ước lượng thời gian chạy toàn kho, báo người dùng rồi chạy.

**Xong khi:** mọi trang trong kho hiện có đã có file layout JSON; có bảng mAP và ảnh minh họa.

### 2.4 Trích nội dung theo vùng (tuần 4)
1. `src/parse/build_elements.py`: ghép vùng D-FINE với text layer PyMuPDF thành element `text | heading | table | figure`, mỗi element có `bbox_pdf`, `section_path`, `caption`, `unit` → `data/parsed/<doc_id>.jsonl`.
   - **table:** `page.find_tables(clip=vùng)` → markdown/HTML. Nếu rỗng thì dùng Docling TableFormer trên ảnh crop. Nếu vẫn lỗi thì lấy text theo dòng (words sắp theo y, x). Nhận đơn vị ("Đơn vị: tỷ đồng/triệu VND") bằng regex ở dòng trên/dưới bảng.
   - **figure:** render crop 200-300 DPI → `data/crops/<element_id>.png`; lấy kèm text vector trong vùng (nhãn trục, giá trị).
   - **icon:** bỏ.
   - **text:** block ngoài vùng bảng/hình; heading theo cỡ chữ/đậm; sắp thứ tự đọc theo cột.
2. `src/parse/caption_figures.py`: VLM chạy theo lô trên `data/crops/`. Prompt yêu cầu: loại biểu đồ, tiêu đề, chuỗi số liệu (JSON), 2-3 câu mô tả xu hướng. Truyền text vector làm gợi ý để giảm bịa số. Chạy trên server bằng VLM chung (xem 004), theo lô, có checkpoint.
3. So sánh parse trên 20-30 trang khó (`experiments/parse_compare/`): (a) PyMuPDF `find_tables`, (b) Docling mặc định, (c) D-FINE X + PyMuPDF/Docling. Đo bảng phát hiện đúng, ô đúng (chấm tay), thời gian/trang. Viết báo cáo ngắn.

**Xong khi:** mọi tài liệu hiện có đã có `parsed/*.jsonl`; có báo cáo so sánh parse.

### 2.5 Chia đoạn và lập chỉ mục (tuần 5)
1. `src/pipelines/p1_text/chunk.py`:
   - Mỗi bảng là một chunk (tiền tố: tên công ty, năm, `section_path`, caption, đơn vị). Bảng dài thì cắt theo dòng, lặp lại header.
   - Mỗi figure là một chunk caption + số liệu.
   - Text chia theo mục, 300-500 token, overlap khoảng 50.
   - Metadata gồm `doc_id`, ticker, năm, ngành, trang, loại element, bbox.
2. `src/pipelines/p1_text/index.py`: embed bge-m3 (dense) và lưu Qdrant; lập chỉ mục BM25 (tách từ tiếng Việt bằng `underthesea` hoặc `pyvi`; ghi lựa chọn vào decisions).

### 2.6 Truy xuất và sinh (tuần 5)
1. BM25 + dense → hợp nhất RRF → rerank bge-reranker-v2-m3 → top-5 chunk → gom về trang.
2. Lọc metadata khi câu hỏi nêu rõ công ty/năm (trích bằng regex hoặc LLM nhẹ).
3. Prompt sinh đáp án bắt buộc trích dẫn `[doc_id, trang]`, và trả lời "không tìm thấy trong tài liệu" khi thiếu bằng chứng.
4. `python -m src.pipelines.p1_text.run --question "..."` trả về đúng giao diện chung.
5. Đo trên 20 câu mẫu, so với P1-v0 → `experiments/p1_v1_seed20/`.

**Đầu ra GĐ 2:** kho + metadata, ảnh trang, layout JSON, parsed JSONL, chỉ mục, pipeline 1 chạy qua một script, báo cáo so sánh parse, bảng mAP D-FINE.

**Xong khi:** kho đã đủ ≥ 100 tài liệu và toàn bộ đã qua 2.2–2.5; pipeline 1 trả lời được câu hỏi về bảng với trích dẫn trang và bbox.

---

## Giai đoạn 3 (tuần 6-8): Pipeline 2, vision-native

**Mục tiêu:** truy xuất trên ảnh trang và sinh đáp án bằng VLM, đã kiểm chứng trên benchmark chuẩn.

1. **Chạy thử retriever (tuần 6):** `colpali-engine`, checkpoint ColQwen2 (ghi phiên bản cụ thể), fp16/bf16 trên server. Embed 100 trang; ghi VRAM, giây/trang, dung lượng vector/trang.
2. **Kiểm chứng ViDoRe (tuần 6):** chạy 2-3 tập con, đối chiếu nDCG@5 công bố. Nếu lệch > 2-3 điểm, kiểm tra tiền xử lý ảnh và phiên bản thư viện trước khi đi tiếp.
3. **Embed toàn kho (tuần 7):** theo lô, có checkpoint, lưu tensor/Qdrant multi-vector (MaxSim) kèm metadata. Báo trước ước lượng thời gian và dung lượng.
4. **Sinh đáp án (tuần 7):** chốt VLM chung (004: Qwen2.5-VL-7B AWQ hoặc 3B fp16, đo VRAM/tốc độ trước); VLM nhận ảnh top-k trang (k = 1-3) cùng câu hỏi; thử 2 mức độ phân giải ảnh.
5. **Thống nhất giao diện (tuần 8):** `src/pipelines/p2_vision/` trả về đúng giao diện chung. Vùng bằng chứng tùy chọn: chọn vùng D-FINE trên trang top-1 có overlap cao nhất với attention/MaxSim patch.
6. So sánh định tính P1 với P2 trên 20 câu mẫu: câu nào pipeline nào thắng và vì sao.

**Đầu ra:** pipeline 2, kết quả đối chiếu ViDoRe, bảng tài nguyên (VRAM, thời gian, dung lượng index, ghi rõ phần cứng).

**Xong khi:** hai pipeline chạy được trên cùng kho qua cùng một giao diện.

---

## Giai đoạn 4 (tuần 9-11): Xây benchmark tiếng Việt

**Mục tiêu:** 400-800 câu hỏi đã duyệt, chia dev/test. Đây là giai đoạn dễ trễ nhất; bắt đầu viết hướng dẫn duyệt từ tuần 8.

1. **Hướng dẫn duyệt (đầu tuần 9):** 5 loại câu hỏi (văn bản, bảng, biểu đồ, đa trang, nhiều tài liệu). Checklist: đáp án đúng, đủ ngữ cảnh, chỉ một đáp án hợp lý, đúng trang bằng chứng, đúng loại, không lộ từ khóa, tự nhiên. Kèm ví dụ đúng/sai → `docs/annotation_guideline.md`.
2. **Lấy mẫu trang (tuần 9):** 1.000-1.500 trang **phân tầng theo loại trang** (dùng nhãn D-FINE: có bảng / có biểu đồ / chỉ văn bản), theo công ty, năm. Câu đa trang ghép 2-3 trang. Loại trang bìa, mục lục, trang trống.
3. **Sinh câu hỏi (tuần 9):** VLM **khác họ** với VLM sinh đáp án. Câu hỏi độc lập (nêu rõ công ty, năm, đơn vị). Đầu ra gồm đáp án, mã trang, đoạn bằng chứng, loại. Yêu cầu cả câu khó (so sánh, tính toán, đa trang). Sinh khoảng 700-1.600 câu (`src/benchmark/generate.py`).
4. **Lọc tự động (tuần 10):** loại câu trùng (embedding), câu thiếu ngữ cảnh; đánh dấu câu mà hai VLM đều không đồng ý với đáp án vàng (`src/benchmark/filter.py`).
5. **Duyệt thủ công (tuần 10-11):** giao diện hiển thị ảnh trang cạnh câu hỏi/đáp án, 3 nút giữ/sửa/loại (`src/benchmark/review_app.py`); 1-3 phút mỗi câu; chia phiên 1-2 giờ.
6. **Duyệt chéo (tuần 11):** người thứ hai duyệt độc lập 10-15% số câu; tính tỷ lệ đồng ý và Cohen's kappa; thấp thì sửa hướng dẫn và duyệt lại phần bất đồng.
7. **Chốt và chia tập:** cho phép nhiều trang vàng; dev khoảng 30%, test khoảng 70%, **chia theo công ty** để tránh rò rỉ; **khóa tập test** (lưu `sha256` file test vào `docs/decisions/`).
8. Bảng thống kê: số câu theo loại, theo công ty/ngành, tỷ lệ loại ở mỗi bước, độ đồng thuận.
9. Script đánh giá `src/eval/retrieval.py` (Recall@1/3/5, nDCG@5, MRR) và `src/eval/answer.py` (xem GĐ 6).

**Đầu ra:** hướng dẫn duyệt, `benchmark/{dev,test}.jsonl` (id, câu hỏi, đáp án, loại, trang vàng, tài liệu, bbox nếu có), bảng thống kê, script đánh giá.

**Xong khi:** có ít nhất 400 câu đã duyệt, kappa ≥ khoảng 0,6, tập test đã khóa.

---

## Giai đoạn 5 (tuần 12-14): Cải tiến và pipeline 3

**Mục tiêu:** hoàn thành 1-2 điểm đóng góp và dựng pipeline hybrid. Chỉ chạy trên tập **dev**.

1. **Baseline trên dev (đầu tuần 12):** Recall@k, nDCG, MRR của P1-v0, P1 và P2 theo từng loại câu hỏi.
2. **Ablation D-FINE (tuần 12):** P1 với layout PyMuPDF so với P1 với D-FINE X, đo Recall@5 trên câu bảng/biểu đồ. Đây là đóng góp đã có sẵn, cần chứng minh bằng số.
3. **Chọn điểm đóng góp bằng số liệu (tuần 12):** ColQwen yếu ở tiếng Việt → finetune; hai nhánh bổ trợ nhau → router; index quá nặng → nén. Tối đa 2 điểm.
4. **Phương án A, finetune ColQwen bằng LoRA (server; QLoRA nếu thiếu VRAM):** câu hỏi tổng hợp trên các trang **không thuộc benchmark**; hard negatives (cùng công ty khác năm, cùng loại bảng); contrastive loss; theo dõi trên dev, dừng sớm.
5. **Phương án B, router:** đặc trưng gồm loại câu hỏi (phân loại từ câu hỏi) và loại trang (từ D-FINE: số bảng/hình, tỷ lệ diện tích). Bộ phân loại nhẹ hoặc LLM nhỏ chọn nhánh. So với RRF và với việc luôn dùng nhánh tốt nhất.
6. **Phương án C, nén index:** token pooling, lượng tử hóa; vẽ đường đánh đổi dung lượng index và Recall.
7. **Pipeline 3 (tuần 13-14):** kết hợp truy xuất hai nhánh (hợp nhất điểm hoặc router), rerank, chọn đầu vào cho bước sinh (text parse, ảnh trang, hoặc cả hai); ablation riêng cho từng thành phần.
8. Mỗi cải tiến có so sánh trước/sau cùng cấu hình; chạy nhiều seed nếu có huấn luyện.

**Đầu ra:** adapter/router, pipeline 3, bảng kết quả dev trước/sau.

**Xong khi:** có ít nhất một cải tiến chứng minh được bằng số liệu trên dev (kết luận âm tính cũng hợp lệ nếu phân tích rõ).

---

## Giai đoạn 6 (tuần 15-16): Thí nghiệm cuối và phân tích

**Mục tiêu:** bảng kết quả cuối trên tập test, đáng tin cậy và tái lập được. Đáp ứng mục tiêu 3 của đề cương.

1. **Đóng băng cấu hình (đầu tuần 15):** Git tag; ghi model và tham số mọi pipeline; sau mốc này không chỉnh theo kết quả test.
2. **Chạy trên tập test (tuần 15):** ba pipeline + các biến thể ablation (có/không D-FINE, có/không rerank, có/không finetune, 1-2 mức độ phân giải, k khác nhau); lưu kết quả thô từng câu.
3. **Bốn nhóm chỉ số:**
   - *Truy xuất:* Recall@1/3/5, nDCG@5, MRR (mức trang).
   - *Câu trả lời:* so khớp số liệu tự động (chuẩn hóa đơn vị, sai số tương đối ≤ 1%); LLM-as-judge cho câu diễn giải; chấm tay 100 câu để tính độ đồng thuận judge–người.
   - *Trích dẫn:* citation precision/recall mức trang; với P1/P3, IoU vùng bằng chứng so với bbox vàng (nếu có).
   - *Chi phí:* độ trễ p50/p95 từng bước, VRAM, dung lượng index, thời gian lập chỉ mục, chi phí API (ghi rõ phần cứng).
4. **Phân tích lỗi (tuần 16):** mẫu ngẫu nhiên 100-150 câu sai; gán nguyên nhân (phát hiện vùng sai, parse bảng sai, truy xuất sai trang, đúng trang nhưng đọc sai, sinh sai, benchmark sai); chọn 5-8 ví dụ kèm ảnh trang.
5. **Ý nghĩa thống kê:** bootstrap khoảng tin cậy cho chênh lệch giữa các pipeline; không kết luận khi khác biệt nằm trong sai số.

**Đầu ra:** bảng kết quả chính, bảng ablation, phân tích lỗi, biểu đồ theo loại câu hỏi, bảng chi phí.

**Xong khi:** mọi con số truy ngược được về file kết quả thô và cấu hình đã lưu.

---

## Giai đoạn 7 (tuần 17-18): Demo, báo cáo và bảo vệ

**Mục tiêu:** hoàn thiện sản phẩm và quyển báo cáo (nên viết dần từ giai đoạn 2).

1. **Demo (tuần 17):** Gradio/Streamlit gồm ô hỏi, chọn pipeline, câu trả lời, danh sách top-k trang kèm ảnh, **vẽ bbox vùng bằng chứng** (từ D-FINE/element). Chạy trên server với index tính sẵn. Chuẩn bị 5-8 câu demo đã thử, gồm một ca thất bại để phân tích trung thực; quay video dự phòng.
2. **Hoàn thiện mã nguồn (tuần 17):** README chạy lại thí nghiệm, script tái lập bảng kết quả chính, đóng gói benchmark.
3. **Viết báo cáo (tuần 17-18):** Mở đầu; Cơ sở lý thuyết; Công trình liên quan; Xây dựng benchmark; Phương pháp (gồm D-FINE X); Thực nghiệm và kết quả; Phân tích lỗi; Kết luận; Phụ lục (hướng dẫn duyệt, prompt, cấu hình).
4. Gửi GVHD bản nháp đầu tuần 18, chừa thời gian sửa.
5. **Bảo vệ (tuần 18):** slide 15-20 trang; tập trả lời các câu: vì sao chọn domain này, benchmark có đáng tin không, vì sao pipeline X thắng, có rò rỉ dữ liệu không (kể cả dataset D-FINE), chi phí triển khai.

**Đầu ra:** demo, mã nguồn và benchmark đóng gói, báo cáo hoàn chỉnh, slide, video dự phòng.

**Xong khi:** một người ngoài nhóm làm theo README chạy lại được demo.

## Lịch báo cáo GVHD gợi ý

| Thời điểm | Nội dung |
| --- | --- |
| Cuối tuần 2 | Phạm vi, baseline, ghi chú paper |
| Cuối tuần 5 | Kho dữ liệu, D-FINE + parse, pipeline 1 |
| Cuối tuần 8 | Pipeline 2, đối chiếu ViDoRe |
| Cuối tuần 11 | Benchmark, thống kê, độ đồng thuận |
| Cuối tuần 14 | Kết quả cải tiến trên dev |
| Cuối tuần 16 | Kết quả cuối, phân tích lỗi |
| Tuần 18 | Bản nháp báo cáo và demo |
