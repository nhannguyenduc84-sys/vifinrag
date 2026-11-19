# 003-tich-hop-dfine-x-vao-pipeline-1

- **Ngày:** 2026-11-19
- **Trạng thái:** Đã duyệt hướng tích hợp; còn 2 điểm cần xác nhận (mục 6)
- **Tác giả:** Người dùng & Claude

## 1. Ngữ cảnh & Đặt vấn đề

Pipeline 1 (text-centric) cần biết **vùng nào trên trang là bảng, vùng nào là hình/biểu đồ** để:
- trích bảng thành markdown/HTML mà không lẫn văn bản xung quanh;
- cắt riêng vùng biểu đồ để VLM sinh caption và đọc số liệu (thay vì đưa cả trang);
- lưu tọa độ vùng làm "vùng bằng chứng" trong trích dẫn (yêu cầu output của đề cương).

Hiện tại `src/preprocess/extract_pages.py` chỉ dùng `page.find_tables()` của PyMuPDF. Hàm này dựa vào đường kẻ nên dễ bỏ sót bảng không kẻ khung (borderless), loại bảng phổ biến trong BCTN. Nó cũng không nhận diện được biểu đồ vector.

### 1.1 Mô hình đã có (kiểm tra 2026-11-19)

**Hugging Face:** [`ducnhan0804/dfine-x-obj-detection`](https://huggingface.co/ducnhan0804/dfine-x-obj-detection) (public, Apache-2.0, commit `0733fe6`).

| Mục | Giá trị |
| --- | --- |
| Kiến trúc | D-FINE HGNetv2-X (backbone B5), input 640×640 |
| Checkpoint | `best_stg2.pth`, 1.003.102.397 byte (≈ 1 GB, có cả EMA) |
| Lớp | 0 `Object-detection` (lớp cha Roboflow, bỏ), 1 `Figure`, 2 `Icon`, 3 `Table` |
| Dataset | Roboflow `vdataset`, 676 ảnh; train/valid/test = 472/101/103 ảnh (`d:\Project\D-FINE\datasets`) |
| Metric công bố (trên **valid**) | mAP@50:95 = 0,8375; mAP@50 = 0,9182; mAP@75 = 0,8966; AR@100 = 0,9348 |
| Tiền xử lý lúc train | Resize 640×640 (không giữ tỉ lệ), `ConvertPILImage(scale=True)`, **không** Normalize |
| File kèm | `config.json`, `preprocessor_config.json`, `modeling_dfine.py` (wrapper `trust_remote_code`), `dfine_hgnetv2_x_custom.yml`, `custom_detection.yml` (num_classes 4) |

**Đánh giá: dùng được.** Checkpoint, config và số lớp khớp với dataset. Có 4 điểm cần lưu ý:
1. **Wrapper HF không dùng thẳng trong dự án được.** `modeling_dfine.py` yêu cầu chạy từ thư mục gốc repo D-FINE và gọi `from src.core import YAMLConfig`. Dự án `vifinrag` cũng có package tên `src`, nên khi chạy từ `vifinrag` lệnh import sẽ trỏ nhầm sang `vifinrag/src` và lỗi.
2. **Metric hiện chỉ có trên tập valid**, cũng là tập dùng để chọn checkpoint, nên số này lạc quan. Chưa có metric trên tập test 103 ảnh và chưa có AP từng lớp.
3. **Model card không nhất quán về số epoch:** dòng "Training" ghi 80 (72 + 8), còn YAML trên HF ghi 35 (30 + 5). Bản YAML local `d:\Project\D-FINE\configs\dfine\custom\dfine_hgnetv2_x_custom.yml` ghi 80 (72 + 2n). Kiến trúc giống nhau nên vẫn load được, nhưng báo cáo cần ghi đúng số epoch.
4. `preprocessor_config.json` khai báo Normalize theo ImageNet, nhưng wrapper và pipeline train đều không Normalize. Khi tự viết inference phải theo cách lúc train (không Normalize).

Ngoài ra, bản local `d:\Project\D-FINE\configs\dataset\custom_detection.yml` đang là mẫu gốc (`num_classes: 777`). Khi export phải thay bằng bản HF (`num_classes: 4`), nếu không head sẽ lệch shape với checkpoint.

## 2. Các phương án cân nhắc

### Về vai trò của D-FINE
- **PA 1: chỉ dùng PyMuPDF `find_tables()`** (hiện trạng). Nhanh nhưng sót bảng không khung, không có vùng biểu đồ.
- **PA 2: layout model mặc định của Docling.** Có sẵn nhưng train trên tài liệu tiếng Anh, chưa đánh giá trên BCTN Việt.
- **PA 3: D-FINE X phát hiện vùng, nội dung lấy theo vùng.** Chọn phương án này. PA 1 và PA 2 giữ làm baseline.

### Về cách chạy inference trong dự án
- **Cách A: wrapper HF (`AutoModel`, `trust_remote_code`).** Vướng xung đột tên `src` và yêu cầu `cwd`, như mục 1.1.
- **Cách B: export ONNX một lần bằng repo D-FINE, rồi dùng `onnxruntime-gpu` trong dự án.** Lúc chạy không phụ thuộc code D-FINE hay PyTorch. Input/output rõ ràng (`images[N,3,640,640]`, `orig_target_sizes[N,2]` → `labels`, `boxes`, `scores`).
- **Cách C: gọi `tools/inference/torch_inf.py` của D-FINE qua subprocess** với `cwd = D-FINE`. Đơn giản nhưng chậm (load model mỗi lần) và khó chạy theo lô.

## 3. Quyết định được chọn

- **Vai trò:** PA 3. D-FINE X chỉ trả **vùng** (table/figure/icon); **nội dung** lấy từ text layer PDF (PyMuPDF), Docling/VLM chỉ làm dự phòng.
- **Inference:** **Cách B (ONNX)** là chính. Cách C làm dự phòng nếu export ONNX lỗi.

### 3.1 Luồng xử lý

```
HF best_stg2.pth ──(export 1 lần, trong repo D-FINE)──► models/dfine_x_bctn/model.onnx
                                                                │
data/pages/<doc_id>/p<n>.png  (150 DPI, đã có)                  │
        │◄──────────────────────────────────────────────────────┘
        ▼
[A] src/layout/detect.py        ONNX Runtime → data/layout/<doc_id>/p<n>.json
        ▼
[B] src/parse/build_elements.py ghép vùng D-FINE + text layer PyMuPDF
        │   ├─ table  → find_tables(clip=vùng) → nếu rỗng: Docling TableFormer trên ảnh crop
        │   │           → nếu vẫn lỗi: text theo dòng trong vùng (words, sort theo y,x)
        │   ├─ figure → render crop DPI 200-300 → data/crops/<element_id>.png
        │   │           + text vector trong vùng (nhãn trục, số liệu) làm gợi ý cho VLM
        │   ├─ icon   → bỏ (kèm text bên trong icon)
        │   └─ text   → block PyMuPDF ngoài vùng bảng/hình; heading theo cỡ chữ
        ▼
[C] src/parse/caption_figures.py  VLM theo lô trên data/crops/ → caption + số liệu (JSON)
        ▼
data/parsed/<doc_id>.jsonl   (mỗi dòng một element)
        ▼
[D] src/pipelines/p1_text/chunk.py → index BM25 + bge-m3
```

### 3.2 Export ONNX (làm một lần, trên server)

```bash
cd D-FINE                                   # repo Peterande/D-FINE, môi trường riêng có torch
huggingface-cli download ducnhan0804/dfine-x-obj-detection \
    best_stg2.pth dfine_hgnetv2_x_custom.yml custom_detection.yml --local-dir hf_dfine
cp hf_dfine/custom_detection.yml configs/dataset/custom_detection.yml       # num_classes: 4
cp hf_dfine/dfine_hgnetv2_x_custom.yml configs/dfine/custom/dfine_hgnetv2_x_custom.yml
pip install onnx onnxsim
python tools/deployment/export_onnx.py -c configs/dfine/custom/dfine_hgnetv2_x_custom.yml \
    -r hf_dfine/best_stg2.pth --check --simplify          # → hf_dfine/best_stg2.onnx
mkdir -p ../vifinrag/models/dfine_x_bctn && cp hf_dfine/best_stg2.onnx ../vifinrag/models/dfine_x_bctn/model.onnx
```

**Kiểm tra tương đương (bắt buộc):** chạy cùng 10 trang qua `torch_inf.py` (PyTorch) và qua ONNX. Box lệch ≤ 1 px, score lệch ≤ 1e-3, cùng số box sau ngưỡng. Ghi kết quả vào `experiments/dfine_eval/onnx_parity.json`.

### 3.3 Inference trong dự án (`src/layout/detect.py`)
- Tiền xử lý **giống lúc train**: PIL RGB → resize 640×640 (bilinear) → `/255` → CHW float32, **không Normalize**. `orig_target_sizes = [[W, H]]` của ảnh gốc, nên box trả về đã ở tọa độ pixel ảnh gốc.
- Hậu xử lý: map `1→figure, 2→icon, 3→table`, bỏ `0`. Ngưỡng score riêng từng lớp (mặc định 0,4; chọn lại trên valid). NMS theo lớp (IoU 0,5). Gộp box lồng nhau (IoU > 0,7). Bỏ box có diện tích < 0,2% trang.
- Đổi tọa độ: `bbox_pdf = bbox_px * 72 / dpi`, để dùng với `page.get_text(clip=…)`, `find_tables(clip=…)`, `get_pixmap(clip=…)`.
- CLI: `python -m src.layout.detect --model models/dfine_x_bctn/model.onnx [--doc-id|--ticker] --batch-size 8 --conf 0.4 --force`. Có cache, `tqdm`, `logging`. Ghi `configs/layout.yaml` (repo HF, commit `0733fe6`, sha256 file ONNX, ngưỡng).

`data/layout/<doc_id>/p<n>.json`:

```json
{
  "page_id": "FPT_BCTN_2024_p37", "image_size": [1240, 1754], "dpi": 150,
  "model": "ducnhan0804/dfine-x-obj-detection@0733fe6",
  "detections": [
    {"region_id": "FPT_BCTN_2024_p37_r0", "label": "table", "score": 0.93,
     "bbox_px": [102, 410, 1130, 980], "bbox_pdf": [48.96, 196.8, 542.4, 470.4]}
  ]
}
```

`data/parsed/<doc_id>.jsonl`, mỗi dòng một element:

```json
{"element_id": "FPT_BCTN_2024_p37_e3", "doc_id": "FPT_BCTN_2024", "page_id": "FPT_BCTN_2024_p37",
 "page": 37, "type": "table", "bbox_pdf": [48.96, 196.8, 542.4, 470.4],
 "content": "| Chỉ tiêu | 2023 | 2024 |\n|---|---|---|\n| Doanh thu thuần | ... | ... |",
 "caption": "Kết quả kinh doanh hợp nhất", "unit": "tỷ đồng",
 "section_path": ["Báo cáo của Ban Tổng Giám đốc", "Kết quả kinh doanh"],
 "source": "dfine+pymupdf", "layout_score": 0.93}
```

### 3.4 D-FINE được dùng lại ở các giai đoạn sau
| Giai đoạn | Cách dùng |
| --- | --- |
| 2 – Pipeline 1 | Tách bảng, hình, text; chunk theo element; lưu bbox để trích dẫn vùng |
| 3 – Pipeline 2 | (tùy chọn) Khoanh vùng bằng chứng trên trang top-1 để hiển thị |
| 4 – Benchmark | Gán nhãn loại trang (có bảng / có biểu đồ / chỉ văn bản) để lấy mẫu phân tầng |
| 5 – Pipeline 3 | Đặc trưng cho router: số bảng, số hình, tỷ lệ diện tích bảng/hình của trang |
| 6 – Phân tích lỗi | Nhóm lỗi "phát hiện vùng sai" (sót bảng, cắt thiếu biểu đồ) |
| 7 – Demo | Vẽ bbox vùng bằng chứng lên ảnh trang |

### 3.5 Đánh giá (bắt buộc để đưa vào báo cáo)
1. **Detection trên tập test 103 ảnh** (chưa dùng để chọn checkpoint): mAP@50, mAP@50:95, AP/AR **từng lớp**. Dùng `train.py --test-only` của D-FINE, trỏ `val_dataloader` sang `datasets/test`. Lưu log vào `experiments/dfine_eval/`.
2. **Tổng quát hóa:** khoảng 50 trang tự gán nhãn từ kho BCTN của dự án, chọn công ty không có trong dataset train.
3. **So sánh parse trên 20-30 trang khó** (bảng không khung, bảng nhiều tầng tiêu đề, biểu đồ): (a) PyMuPDF `find_tables`, (b) Docling mặc định, (c) D-FINE X + PyMuPDF/Docling. Đo tỷ lệ bảng phát hiện đúng, ô đúng (chấm tay), thời gian/trang.
4. **Ảnh hưởng tới truy xuất (GĐ 5, trên dev):** Recall@5 của nhóm câu hỏi bảng/biểu đồ khi pipeline 1 dùng (a) so với (c).

## 4. Lý do kỹ thuật & Biện luận
- BCTN Việt Nam là **Digital PDF**: chữ và số có sẵn trong text layer. Phần khó là *biết vùng nào là bảng hay hình*, không phải OCR. D-FINE chỉ làm detection, nội dung lấy từ text layer nên từng con số chính xác. OCR chỉ dùng dự phòng cho trang không có text layer.
- ONNX tách hẳn code và môi trường của D-FINE khỏi dự án. Cách này tránh xung đột package `src`, tránh phụ thuộc phiên bản torch, và chạy theo lô nhanh.
- Cắt vùng biểu đồ trước khi đưa vào VLM giúp tăng độ phân giải hiệu dụng và giảm token ảnh.
- Lưu bbox ở mọi element nên trích dẫn vùng bằng chứng gần như không tốn thêm công.
- Giữ PA 1 và PA 2 làm baseline giúp đóng góp D-FINE **đo được bằng số liệu**.

## 5. Hệ quả & Đánh đổi
- **Tích cực:** xử lý được bảng không khung và biểu đồ; có vùng bằng chứng; có nhãn loại trang cho benchmark và router.
- **Rủi ro:** dataset chỉ 676 ảnh; metric hiện có chỉ trên valid; export ONNX có thể lỗi với một số op (đã có Cách C dự phòng); nếu ảnh train lấy từ tài liệu sẽ vào benchmark thì phải ghi rõ trong báo cáo (rò rỉ ở mức layout, không phải mức hỏi đáp).
- **Giảm thiểu:** kiểm tra tương đương PyTorch/ONNX; đánh giá trên test và trên công ty ngoài dataset; luôn có fallback PyMuPDF khi D-FINE không phát hiện gì.

## 6. Cần người dùng xác nhận
1. `best_stg2.pth` được train với cấu hình nào: 35 epoch (YAML trên HF) hay 80 epoch (model card, YAML local)?
2. 676 ảnh trang lấy từ tài liệu nào (mã CK, năm)? Cần biết để tránh trùng với tài liệu dùng làm benchmark.
