# Nhật ký phiên làm việc: 2026-11-19 - Lập kế hoạch chi tiết và kế hoạch tích hợp D-FINE X

## 1. Mục tiêu phiên
- Đọc đề cương `Project 3_Nguyễn Đức Nhẫn.pdf`, CLAUDE.md và `docs/`; lập kế hoạch chi tiết toàn dự án.
- Nêu rõ cách tích hợp D-FINE X vào hệ thống.
- Sửa các file .md cho khớp đề cương và hiện trạng.

## 2. Việc đã thực hiện & Kết quả
- **Đối chiếu đề cương với ROADMAP:** đề cương có 4 mục tiêu (benchmark, 3 pipeline, đánh giá 4 nhóm chỉ số, demo) và yêu cầu output gồm "vùng bằng chứng trên trang". ROADMAP cũ thiếu chỉ số trích dẫn mức vùng và chi phí API; đã bổ sung.
- **Kiểm tra hiện trạng dữ liệu:**
  - *Lệnh*: `ls data/raw/pdf | wc -l`; đọc `data/metadata.csv`
  - *Kết quả*: 24 PDF, 8 công ty × 3 năm, tổng 3.143 trang; 24 thư mục trong `data/pages/`.
- **Kiểm tra GPU:**
  - *Lệnh*: `nvidia-smi --query-gpu=name,memory.total --format=csv`
  - *Kết quả*: NVIDIA GeForce RTX 2050, 4096 MiB.
- **Kiểm tra repo D-FINE (`d:\Project\D-FINE`):**
  - Dataset Roboflow 676 ảnh; train/valid/test = 472/101/103 ảnh, 1248/282/278 box; lớp `Object-detection` (lớp cha), `Figure`, `Icon`, `Table`.
  - `find` không thấy file `*.pth`/`*.onnx`/`*.pt` trong repo.
- **Tài liệu mới/sửa:**
  - Mới: `docs/decisions/003-tich-hop-dfine-x-vao-pipeline-1.md`, `docs/decisions/004-chien-luoc-tinh-toan-gpu-4gb.md` (cả hai *Đề xuất*).
  - Viết lại `docs/ROADMAP.md`: thêm bảng đối chiếu đề cương; GĐ 2 tách thành bước 2.0–2.6 (gồm 2.3 D-FINE, 2.4 trích element); D-FINE dùng lại ở GĐ 3-7; giao diện chung; 4 nhóm chỉ số.
  - Sửa `README.md` (pipeline 1 có D-FINE, phần cứng, cấu trúc thư mục mới, chỉ số), `CLAUDE.md` (mục tiêu đề cương, GPU, giai đoạn hiện tại), ghi đè `docs/STATUS.md`.

- **Cập nhật trong cùng phiên, sau phản hồi của người dùng:**
  - Người dùng cung cấp checkpoint D-FINE X tại HF `ducnhan0804/dfine-x-obj-detection` và xác nhận chuyển sang server khoảng 10 GB VRAM.
  - *Lệnh*: `curl https://huggingface.co/api/models/ducnhan0804/dfine-x-obj-detection`; tải và đọc `README.md`, `config.json`, `preprocessor_config.json`, `custom_detection.yml`, `dfine_hgnetv2_x_custom.yml`, `modeling_dfine.py`. Lấy kích thước checkpoint bằng `curl -I`.
  - *Kết quả*:
    - Commit `0733fe6`; `best_stg2.pth` 1.003.102.397 byte; `num_classes` 4 (0 Object-detection, 1 Figure, 2 Icon, 3 Table).
    - mAP@50:95 = 0,8375 và mAP@50 = 0,9182, trên valid.
    - `modeling_dfine.py` import `src.core` từ `cwd`, nên xung đột với package `src` của vifinrag.
    - Lúc train dùng `ConvertPILImage(scale=True)`, không Normalize (xem `D-FINE/configs/dfine/include/dataloader.yml`).
    - YAML HF ghi 35 epoch; YAML local và model card ghi 80 epoch.
  - Viết lại decision 003 (chọn ONNX, có lệnh export và quy trình kiểm tra tương đương) và 004 (server 10 GB, chạy tuần tự theo pha). Cập nhật ROADMAP 2.3 và GĐ 3/5/7, README, CLAUDE, STATUS.
  - **Chưa chạy thử** checkpoint: máy local không có torch và không phải môi trường đích.

## 3. Lỗi / Vấn đề gặp phải & Cách xử lý
- In tiếng Việt từ `python -c` lỗi `UnicodeEncodeError` (console cp1252). Tổng trang được lấy bằng lệnh in không dấu. Lần sau đặt `PYTHONIOENCODING=utf-8`.

## 4. Vấn đề và chưa chắc chắn
- D-FINE: chưa rõ số epoch thật (35 hay 80) và nguồn 676 ảnh (decision 003 §6). Export ONNX chưa thử.
- VLM sinh đáp án chốt ở đầu GĐ 3 sau khi đo VRAM thật; model sinh câu hỏi/judge chốt ở GĐ 4.
- Tên GPU/CUDA của server chưa ghi nhận.
- `docs/reports/bao_cao_tien_do.tex` ghi "16 lĩnh vực" và "thu thập 100%", không khớp số liệu thật (24 PDF, 7 ngành). Chưa sửa vì là file của người dùng.
- Mốc tuần trong ROADMAP chưa gắn ngày lịch cụ thể (chưa rõ ngày bắt đầu tuần 1).

## 5. Lệnh tái lập kết quả
```bash
ls data/raw/pdf | wc -l
nvidia-smi --query-gpu=name,memory.total --format=csv
PYTHONIOENCODING=utf-8 python -c "import csv;r=list(csv.DictReader(open('data/metadata.csv',encoding='utf-8')));print(len(r),sum(int(x['num_pages']) for x in r))"
```

## 6. Kế hoạch phiên tiếp theo
- [ ] Trên server: export ONNX D-FINE X + kiểm tra tương đương (decision 003 §3.2).
- [ ] Bước 2.3: viết `src/layout/detect.py`, `src/layout/visualize.py`; đánh giá trên test 103 ảnh.
- [ ] Bước 2.0: 20 câu hỏi mẫu + baseline P1-v0.
- [ ] Sửa số liệu trong báo cáo tiến độ LaTeX cho khớp `metadata.csv`.
