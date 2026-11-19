# 004-chien-luoc-tinh-toan-server-10gb

- **Ngày:** 2026-11-19
- **Trạng thái:** Đã duyệt (môi trường chạy). Model sinh đáp án chốt ở đầu GĐ 3.
- **Tác giả:** Người dùng & Claude

> Tên file giữ nguyên để không gãy link. Bản nháp đầu (cùng ngày) giả định chạy trên RTX 2050 4 GB. Người dùng đã xác nhận sẽ chuyển sang **server có khoảng 10 GB VRAM trống**, nên quyết định được viết lại như dưới đây.

## 1. Ngữ cảnh & Đặt vấn đề
- Máy cá nhân: RTX 2050 4 GB (đo bằng `nvidia-smi`, 2026-11-19). Chỉ dùng để soạn code, xem dữ liệu, chạy demo nhẹ.
- Server: khoảng **10 GB VRAM trống**. Tên GPU, phiên bản CUDA và hỗ trợ bf16 chưa ghi nhận.
- Kho dự kiến: 24 tài liệu hiện có = 3.143 trang (trung bình khoảng 131 trang). Với 100-200 tài liệu, ước tính khoảng 13.000-26.000 trang (ước lượng, đo lại khi đủ kho).

## 2. Ước lượng VRAM các thành phần (ước lượng theo số tham số, cần đo thực tế)

| Thành phần | VRAM xấp xỉ | Vừa 10 GB? |
| --- | --- | --- |
| D-FINE X (ONNX/torch, batch 8, 640²) | 1-2 GB | Có |
| bge-m3 (568M, fp16) | khoảng 1,5 GB khi embed theo lô | Có |
| bge-reranker-v2-m3 (fp16) | khoảng 1,5 GB | Có |
| ColQwen2 (khoảng 2,2B, fp16/bf16) | khoảng 5-6 GB khi embed batch nhỏ | Có |
| Qwen2.5-VL-3B (fp16) | khoảng 7-8 GB | Có, sát |
| Qwen2.5-VL-7B AWQ 4-bit (vLLM, `max_model_len` khoảng 8k) | khoảng 7-9 GB | Có, sát |
| Qwen2.5-VL-7B fp16 | khoảng 16 GB | **Không** |
| LoRA finetune ColQwen2 (gradient checkpointing, batch nhỏ) | khoảng 8-10 GB | Sát. Dự phòng: QLoRA |

## 3. Quyết định
1. **Mọi bước chạy trên server**, không cần Kaggle/Colab: ingest, tiền xử lý, D-FINE, parse, bge-m3, BM25, Qdrant, ColQwen, VLM, finetune, đánh giá. Demo có thể chạy trên server hoặc máy cá nhân với index tính sẵn.
2. **Không nạp đồng thời các model lớn.** Chạy theo pha: (i) D-FINE → parse; (ii) caption biểu đồ bằng VLM; (iii) embed bge-m3/ColQwen; (iv) truy xuất; (v) sinh đáp án. Mỗi pha giải phóng VRAM trước khi sang pha sau. Riêng bước sinh đáp án có thể chạy VLM như một server riêng (vLLM).
3. **VLM sinh đáp án chung cho 3 pipeline:** ứng viên Qwen2.5-VL-7B-Instruct-AWQ (hoặc bản mới hơn cùng họ, vừa 10 GB), dự phòng Qwen2.5-VL-3B fp16. Chốt ở đầu GĐ 3 sau khi đo VRAM và tốc độ thật.
4. **Sinh câu hỏi benchmark và LLM-as-judge:** model API **khác họ** với VLM sinh đáp án (chốt ở GĐ 4).
5. Mỗi phép đo chi phí ghi rõ phần cứng (tên GPU server). Không trộn phép đo khác phần cứng trong một bảng.

## 4. Lý do kỹ thuật
- Một môi trường duy nhất giúp tái lập dễ, không phải chuyển index qua lại, không lo quota.
- 10 GB đủ cho từng model chuẩn của đề tài nếu chạy tuần tự. Chỉ VLM 7B cần lượng tử hóa 4-bit.
- Dùng chung một VLM sinh đáp án loại bỏ biến nhiễu, nên chênh lệch giữa các pipeline đến từ truy xuất và dạng ngữ cảnh.

## 5. Hệ quả & Đánh đổi
- **Rủi ro:** server dùng chung nên VRAM trống có thể dao động; VLM 4-bit có thể kém chính xác hơn bản fp16 khi đọc số.
- **Giảm thiểu:** mọi job dài có checkpoint theo lô và tham số `--batch-size`; kiểm tra `nvidia-smi` trước khi chạy; ghi lượng tử hóa vào kết quả; nếu cần có thể so sánh nhỏ 4-bit với 3B fp16 trên 20 câu mẫu.

## 6. Cần ghi nhận
- Tên GPU, CUDA driver, dung lượng ổ đĩa của server. Index ColQwen ước tính vài GB cho 13-26 nghìn trang, ảnh trang khoảng vài chục GB.
