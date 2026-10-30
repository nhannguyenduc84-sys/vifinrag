# ROADMAP: kế hoạch thực hiện 18 tuần

Mỗi giai đoạn gồm: mục tiêu, các bước, đầu ra và tiêu chí xong. Giai đoạn đang làm được ghi trong `docs/STATUS.md`. **Không làm trước các giai đoạn sau** khi giai đoạn hiện tại chưa đạt tiêu chí xong; khi bắt đầu giai đoạn mới, nêu kế hoạch cho người dùng duyệt trước.

| Giai đoạn | Tuần | Nội dung |
| --- | --- | --- |
| 1 | 1-2 | Chốt phạm vi, đọc paper, baseline RAG văn bản |
| 2 | 3-5 | Thu thập dữ liệu, parse, pipeline 1 |
| 3 | 6-8 | Pipeline 2 (vision-native), kiểm chứng trên ViDoRe |
| 4 | 9-11 | Xây benchmark tiếng Việt |
| 5 | 12-14 | Cải tiến và pipeline 3 |
| 6 | 15-16 | Thí nghiệm cuối trên tập test, phân tích |
| 7 | 17-18 | Demo, báo cáo, bảo vệ |

## Nguyên tắc xuyên suốt

- Dùng Git; cố định phiên bản thư viện và model; mỗi thí nghiệm lưu config, seed, kết quả thô vào `experiments/<ten>/`.
- Hai pipeline đầu cùng một giao diện: nhận `câu hỏi`, trả `danh sách trang truy xuất (kèm điểm)`, `câu trả lời`, `trang trích dẫn`, `độ trễ`.
- Mọi con số trong báo cáo phải truy ngược được về file kết quả thô và cấu hình đã lưu.
- Tập test của benchmark bị **khóa** từ cuối giai đoạn 4 và chỉ chạy ở giai đoạn 6.

---

## Giai đoạn 1 (tuần 1-2): Chốt phạm vi và dựng baseline

**Mục tiêu:** hiểu bài toán, chuẩn bị môi trường, có một RAG văn bản chạy được đầu-cuối trên vài tài liệu.

1. Đọc ColPali, VisRAG, M3DocRAG, benchmark ViDoRe; mỗi bài ghi 5-10 dòng (bài toán, phương pháp, kết quả, hạn chế) vào `docs/papers/`.
2. Dựng môi trường: Python, PyTorch khớp CUDA, `transformers`, `colpali-engine`, `docling`, Qdrant (Docker). Kiểm tra GPU và đo VRAM trống.
3. Chọn 10 báo cáo mẫu (3-4 công ty, 2-3 năm).
4. Baseline: PDF → text (PyMuPDF) → chia đoạn → embed bge-m3 → Qdrant → top-5 → LLM trả lời.
5. Viết tay 20 câu hỏi mẫu, ghi nhận lỗi của baseline (đặc biệt bảng và biểu đồ).
6. Chốt với GVHD: domain, số tài liệu, 1-2 điểm đóng góp dự kiến.

**Đầu ra:** ghi chú paper, repo tái lập được môi trường, baseline chạy được, 20 câu mẫu kèm nhận xét lỗi.

**Xong khi:** hỏi được một câu bất kỳ trên bộ mẫu và nhận câu trả lời có trích nguồn; có danh sách lỗi của baseline.

## Giai đoạn 2 (tuần 3-5): Thu thập dữ liệu và pipeline 1

**Mục tiêu:** có kho tài liệu hoàn chỉnh và pipeline text-centric xử lý được bảng, hình.

1. **Thu thập (tuần 3):** 30-60 công ty đa ngành; báo cáo thường niên và tài chính 2-3 năm gần nhất; đặt tên `<MA_CK>_<loai>_<nam>.pdf`; lập `data/metadata.csv`; loại bản scan quá kém. Tuân thủ các quy tắc crawl trong `CLAUDE.md`.
2. **Tiền xử lý (tuần 3):** PDF → ảnh từng trang (DPI 150-200) và text thô; mã trang `<doc_id>_p<số trang>`.
3. **Parse bố cục (tuần 4):** Docling và thử MinerU; xuất bảng sang markdown/HTML; so sánh trên 20 trang khó, ghi tỷ lệ lỗi.
4. **Hình và biểu đồ (tuần 4):** VLM sinh caption và số liệu đọc được, lưu kèm mã trang; chạy theo lô.
5. **Chia đoạn và lập chỉ mục (tuần 5):** mỗi bảng là một đơn vị kèm tiêu đề và đơn vị tính; gắn metadata (công ty, năm, loại báo cáo, trang); embed bge-m3 và lập chỉ mục BM25.
6. **Truy xuất và sinh (tuần 5):** BM25 + dense, hợp nhất RRF, rerank bge-reranker-v2-m3, top-5, LLM với prompt bắt buộc trích dẫn trang và trả lời "không tìm thấy" khi thiếu bằng chứng.
7. Đo sơ bộ trên 20 câu mẫu làm mốc.

**Đầu ra:** kho tài liệu + metadata, ảnh trang, kết quả parse, chỉ mục, pipeline 1 chạy qua một script, báo cáo ngắn so sánh công cụ parse.

**Xong khi:** toàn bộ kho đã đánh chỉ mục; pipeline 1 trả lời được câu hỏi về bảng với trích dẫn trang. Tiêu chí riêng của bước thu thập nằm trong `README.md`.

## Giai đoạn 3 (tuần 6-8): Pipeline 2, vision-native

**Mục tiêu:** truy xuất trên ảnh trang và sinh đáp án bằng VLM, đã kiểm chứng trên benchmark chuẩn.

1. **Chạy thử retriever (tuần 6):** cài `colpali-engine`, tải checkpoint ColQwen/ColPali, embed vài chục trang; ghi VRAM, thời gian embed mỗi trang, kích thước vector mỗi trang. Thiếu VRAM: giảm độ phân giải, dùng bản nhỏ, embed theo lô nhỏ.
2. **Kiểm chứng trên ViDoRe (tuần 6):** chạy vài tập con, đối chiếu số liệu công bố; nếu lệch nhiều, kiểm tra tiền xử lý ảnh và phiên bản thư viện trước khi đi tiếp.
3. **Lưu trữ đa vector (tuần 7):** embed toàn kho, lưu Qdrant cấu hình multi-vector (MaxSim) kèm metadata; chạy theo lô, có checkpoint.
4. **Sinh đáp án (tuần 7):** server VLM (Qwen-VL qua vLLM, lượng tử hóa nếu cần); đưa ảnh top-k (k = 1-3) cùng câu hỏi; thử vài độ phân giải.
5. **Thống nhất giao diện (tuần 8):** pipeline 1 và 2 dùng chung giao diện đã nêu ở "Nguyên tắc xuyên suốt".
6. So sánh định tính trên 20 câu mẫu: câu nào pipeline nào thắng và vì sao.

**Đầu ra:** pipeline 2, kết quả đối chiếu ViDoRe, bảng đo tài nguyên (VRAM, thời gian, dung lượng index), giao diện chung.

**Xong khi:** hai pipeline chạy được trên cùng kho tài liệu qua cùng một giao diện.

## Giai đoạn 4 (tuần 9-11): Xây benchmark tiếng Việt

**Mục tiêu:** 400-800 câu hỏi đã duyệt, chia dev/test. Đây là giai đoạn dễ trễ nhất; bắt đầu viết hướng dẫn duyệt từ tuần 8.

1. **Hướng dẫn duyệt (đầu tuần 9):** định nghĩa 5 loại câu hỏi (văn bản, bảng, biểu đồ, đa trang, nhiều tài liệu); checklist (đáp án đúng, đủ ngữ cảnh, chỉ một đáp án hợp lý, đúng trang bằng chứng, đúng loại, không lộ từ khóa, tự nhiên); ví dụ đúng/sai. Lưu `docs/annotation_guideline.md`.
2. **Lấy mẫu trang (tuần 9):** 1.000-1.500 trang phân tầng theo loại nội dung, công ty, năm; câu đa trang ghép 2-3 trang.
3. **Sinh câu hỏi (tuần 9):** dùng VLM khác với model được đánh giá; câu hỏi độc lập (nêu rõ công ty, năm, đơn vị); đầu ra gồm đáp án, mã trang, đoạn bằng chứng, loại; yêu cầu cả câu khó (so sánh, tính toán, đa trang); sinh khoảng 700-1.600 câu.
4. **Lọc tự động (tuần 10):** loại câu trùng (embedding), câu thiếu ngữ cảnh; đánh dấu câu mà hai VLM đều không đồng ý với đáp án vàng.
5. **Duyệt thủ công (tuần 10-11):** giao diện hiển thị ảnh trang cạnh câu hỏi/đáp án với 3 nút giữ/sửa/loại; 1-3 phút mỗi câu; chia phiên 1-2 giờ.
6. **Duyệt chéo (tuần 11):** người thứ hai duyệt độc lập 10-15% số câu; tính tỷ lệ đồng ý và Cohen's kappa; thấp thì sửa hướng dẫn và duyệt lại phần bất đồng.
7. **Chốt và chia tập:** cho phép nhiều trang vàng; dev khoảng 30%, test khoảng 70%, chia theo công ty để tránh rò rỉ; **khóa tập test**.
8. Lập bảng thống kê: số câu theo loại, theo công ty, tỷ lệ loại ở mỗi bước, độ đồng thuận.

**Đầu ra:** hướng dẫn duyệt, file benchmark JSONL (id, câu hỏi, đáp án, loại, trang vàng, tài liệu), bảng thống kê, script đánh giá retrieval.

**Xong khi:** có ít nhất 400 câu đã duyệt, kappa chấp nhận được (nên từ khoảng 0,6 trở lên), tập test đã khóa.

## Giai đoạn 5 (tuần 12-14): Cải tiến và pipeline 3

**Mục tiêu:** hoàn thành 1-2 điểm đóng góp và dựng pipeline hybrid. Chỉ chạy trên tập **dev**.

1. **Baseline trên dev (đầu tuần 12):** đo Recall@k, nDCG, MRR của pipeline 1 và 2 theo từng loại câu hỏi.
2. **Chọn điểm đóng góp dựa trên số liệu (tuần 12):** ColQwen yếu ở tiếng Việt → finetune; hai nhánh bổ trợ nhau → router; index quá nặng → nén. Tối đa 2 điểm.
3. **Phương án A, finetune ColQwen bằng LoRA:** câu hỏi tổng hợp trên các trang **không thuộc benchmark**; hard negatives (cùng công ty khác năm, cùng loại bảng); contrastive loss; theo dõi trên dev, dừng sớm.
4. **Phương án B, router:** gán nhãn loại câu hỏi/loại trang; bộ phân loại nhẹ hoặc LLM nhỏ chọn nhánh; so sánh với RRF và với việc luôn dùng nhánh tốt nhất.
5. **Phương án C, nén index:** token pooling, lượng tử hóa; vẽ đường đánh đổi dung lượng index và Recall.
6. **Pipeline 3 (tuần 13-14):** kết hợp truy xuất hai nhánh (hợp nhất điểm hoặc router), rerank, chọn đầu vào cho bước sinh (văn bản parse, ảnh trang, hoặc cả hai); ablation riêng cho từng thành phần thêm vào.
7. Mỗi cải tiến có so sánh trước/sau cùng cấu hình; chạy nhiều seed nếu có huấn luyện.

**Đầu ra:** adapter đã finetune hoặc router đã huấn luyện, pipeline 3, bảng kết quả dev trước/sau.

**Xong khi:** có ít nhất một cải tiến chứng minh được bằng số liệu trên dev (kết luận âm tính cũng hợp lệ nếu phân tích rõ).

## Giai đoạn 6 (tuần 15-16): Thí nghiệm cuối và phân tích

**Mục tiêu:** bảng kết quả cuối trên tập test, đáng tin cậy và tái lập được.

1. **Đóng băng cấu hình (đầu tuần 15):** Git tag, ghi model và tham số mọi pipeline; sau mốc này không chỉnh theo kết quả test.
2. **Chạy trên tập test (tuần 15):** ba pipeline + các biến thể ablation (có/không rerank, có/không finetune, độ phân giải 1-2 mức, k khác nhau); lưu kết quả thô từng câu.
3. **Chấm đáp án (tuần 15):** so khớp số liệu tự động; LLM-as-judge cho câu diễn giải; chấm tay 100 câu, tính độ đồng thuận giữa judge và người.
4. **Phân tích lỗi (tuần 16):** mẫu ngẫu nhiên 100-150 câu sai; gán nguyên nhân (OCR/parse, truy xuất sai trang, đúng trang nhưng đọc sai, sinh sai, benchmark sai); chọn 5-8 ví dụ kèm ảnh trang.
5. **Chi phí (tuần 16):** độ trễ, VRAM, dung lượng index, thời gian lập chỉ mục.
6. **Ý nghĩa thống kê:** bootstrap lấy khoảng tin cậy cho chênh lệch giữa các pipeline; không kết luận khi khác biệt nằm trong sai số.
7. Nếu có bộ domain phụ (50-100 câu), chạy thêm để nhận xét khả năng tổng quát hóa.

**Đầu ra:** bảng kết quả chính, bảng ablation, phân tích lỗi, biểu đồ theo loại câu hỏi, bảng chi phí.

**Xong khi:** mọi con số truy ngược được về file kết quả thô và cấu hình đã lưu.

## Giai đoạn 7 (tuần 17-18): Demo, báo cáo và bảo vệ

**Mục tiêu:** hoàn thiện sản phẩm và quyển báo cáo (nên viết dần từ giai đoạn 2).

1. **Demo (tuần 17):** Gradio/Streamlit với ô hỏi, chọn pipeline, câu trả lời, danh sách trang truy xuất kèm ảnh trang và vùng trích (nếu có); chuẩn bị 5-8 câu demo đã thử, gồm một ca thất bại để phân tích trung thực; quay video dự phòng.
2. **Hoàn thiện mã nguồn (tuần 17):** README chạy lại thí nghiệm, script tái lập bảng kết quả chính, đóng gói benchmark.
3. **Viết báo cáo (tuần 17-18):** Mở đầu; Cơ sở lý thuyết; Công trình liên quan; Xây dựng benchmark; Phương pháp; Thực nghiệm và kết quả; Phân tích lỗi; Kết luận và hướng phát triển; Phụ lục (hướng dẫn duyệt, prompt, cấu hình).
4. Gửi GVHD bản nháp đầu tuần 18, chừa thời gian sửa.
5. **Bảo vệ (tuần 18):** slide 15-20 trang xoay quanh vấn đề, câu hỏi nghiên cứu, benchmark, so sánh pipeline, đóng góp, hạn chế; tập trả lời: vì sao chọn domain này, benchmark có đáng tin không, vì sao pipeline X thắng, có rò rỉ dữ liệu không, chi phí triển khai.

**Đầu ra:** demo, mã nguồn và benchmark đóng gói, báo cáo hoàn chỉnh, slide, video dự phòng.

**Xong khi:** một người ngoài nhóm làm theo README chạy lại được demo.

## Lịch báo cáo GVHD gợi ý

| Thời điểm | Nội dung |
| --- | --- |
| Cuối tuần 2 | Phạm vi, baseline, ghi chú paper |
| Cuối tuần 5 | Kho dữ liệu, pipeline 1 |
| Cuối tuần 8 | Pipeline 2, đối chiếu ViDoRe |
| Cuối tuần 11 | Benchmark, thống kê, độ đồng thuận |
| Cuối tuần 14 | Kết quả cải tiến trên dev |
| Cuối tuần 16 | Kết quả cuối, phân tích lỗi |
| Tuần 18 | Bản nháp báo cáo và demo |
