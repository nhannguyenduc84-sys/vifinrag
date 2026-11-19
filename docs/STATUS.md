# Trạng thái dự án (STATUS.md)

*Cập nhật lần cuối: 2026-11-19*

## 1. Giai đoạn hiện tại
**Giai đoạn 2 (tuần 3-5): thu thập dữ liệu, parse bố cục (D-FINE X), pipeline 1.** Kế hoạch chi tiết các bước 2.0–2.6 ở `docs/ROADMAP.md`.

## 2. Số liệu thực tế (đo 2026-11-19)
- `data/raw/pdf/`: **24 PDF**, 8 công ty (FPT, GMD, HPG, MWG, TCB, VCB, VHM, VNM) × 3 năm (2023-2025), 7 ngành, tổng **3.143 trang**; `metadata.csv` có 24 dòng.
- `data/pages/`, `data/text/`: đã tiền xử lý cả 24 tài liệu.
- `configs/sources.yaml`: 39 công ty tham chiếu.
- Phần cứng: chuyển sang **server khoảng 10 GB VRAM trống** (tên GPU chưa ghi). Máy cá nhân RTX 2050 4 GB chỉ để soạn code.
- D-FINE X: checkpoint ở HF [`ducnhan0804/dfine-x-obj-detection`](https://huggingface.co/ducnhan0804/dfine-x-obj-detection) (`best_stg2.pth`, ≈ 1 GB, commit `0733fe6`). Lớp Figure/Icon/Table. Metric công bố **trên valid**: mAP@50:95 = 0,8375, mAP@50 = 0,9182. Chưa có metric trên test.

## 3. Việc đã hoàn thành
- Khung dự án, môi trường `uv`, `sources.yaml`, `src/crawl/ingest.py`, `src/preprocess/extract_pages.py` (PNG 150 DPI, TXT, MD, JSON bbox).
- Fine-tune D-FINE X và đưa lên Hugging Face (người dùng làm).
- Báo cáo tiến độ LaTeX `docs/reports/bao_cao_tien_do.tex`.
- 2026-11-19: lập kế hoạch chi tiết; decision 003 (D-FINE X qua ONNX, đã duyệt hướng) và 004 (server 10 GB, đã duyệt); viết lại ROADMAP, cập nhật README, CLAUDE.

## 4. Việc tiếp theo (theo thứ tự)
1. Trên server: dựng môi trường, ghi tên GPU/CUDA; clone D-FINE; export ONNX từ checkpoint HF; kiểm tra tương đương torch/ONNX (003 §3.2).
2. Viết `src/layout/detect.py` + `src/layout/visualize.py`; chạy thử 1 tài liệu, duyệt trực quan 30 trang.
3. Đánh giá D-FINE trên tập test 103 ảnh (AP từng lớp).
4. Bước 2.0: 20 câu hỏi mẫu + baseline P1-v0.
5. Bước 2.4: `src/parse/build_elements.py`, so sánh parse trên 20-30 trang khó.
6. Song song: tải thêm BCTN (còn thiếu ≥ 76 PDF để đạt 100).

## 5. Vấn đề & Rủi ro
- **Wrapper HF của D-FINE không import được trong dự án** vì cùng tên package `src` với D-FINE. Đã chọn cách export ONNX; chưa chạy thử.
- Model card HF ghi 80 epoch, YAML trên HF ghi 35 epoch; cần người dùng xác nhận. `preprocessor_config.json` ghi Normalize nhưng lúc train không Normalize.
- Chưa rõ 676 ảnh train D-FINE lấy từ tài liệu nào (nguy cơ trùng với benchmark).
- **Kho mới đạt 24/100 PDF.** Báo cáo tiến độ LaTeX ghi "16 lĩnh vực" và "thu thập 100%", không khớp `metadata.csv`; cần sửa trước khi nộp GVHD.
- Giai đoạn 1 còn nợ: `docs/papers/` trống, chưa có baseline và 20 câu mẫu.
- Server dùng chung nên VRAM trống có thể dao động; mọi job dài cần checkpoint theo lô.
