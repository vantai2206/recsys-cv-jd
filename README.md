# Xếp hạng tin tuyển dụng và gợi ý khóa học theo khoảng cách kỹ năng CV–JD

Đề tài Nghiên cứu khoa học sinh viên (đang thực hiện).

**Ý tưởng:** người tìm việc tải CV lên → hệ thống trích xuất kỹ năng → xếp hạng các tin tuyển dụng (JD) theo **% đáp ứng yêu cầu** → chỉ ra kỹ năng còn thiếu → gợi ý khóa học để lấp khoảng trống.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `code_project_demo/Chuan_hoa_ngon_ngu.py` | Trích xuất + chuẩn hóa kỹ năng nhiều tầng: tiền xử lý → khớp chính xác → alias theo ranh giới từ (chống khớp nhầm `java`/`javascript`, `Node.js`) |
| `code_project_demo/Xep_hang_JD.py` | Tính % đáp ứng, xếp hạng tin tuyển dụng, lọc theo nguồn |
| `code_project_demo/data/` | Dữ liệu mẫu tự dựng: CV mẫu, 12 tin tuyển dụng hư cấu, từ điển kỹ năng |
| `RecSys_UC3_GoiY_KhoaHoc/` | Bản đầu của hướng gợi ý khóa học (LangGraph + Ollama) |
| `Dữ liệu khóa học/` | Dữ liệu khóa học Coursera lấy từ Kaggle (xem mục Nguồn dữ liệu) |

## Công thức chấm điểm

```
tỷ lệ đáp ứng = 1 − |S̃ \ S| / |S̃|        (S = kỹ năng của CV, S̃ = kỹ năng JD yêu cầu)
điểm = 0.8 × tỷ lệ(bắt buộc) + 0.2 × tỷ lệ(ưu tiên)
```

> Con số này là **mức đáp ứng yêu cầu kỹ năng**, không phải xác suất trúng tuyển.

## Chạy thử

```bash
cd code_project_demo
python Xep_hang_JD.py
```

## Hướng phát triển

- Trích xuất kỹ năng bằng LLM (LangChain + Ollama), từ điển dùng để chuẩn hóa tên kỹ năng
- LangGraph: khi không có tin nào đạt ngưỡng thì rẽ nhánh sang gợi ý khóa học (Greedy Set Cover)
- Web app: tải CV lên → xem bảng xếp hạng
- Đánh giá: Precision/Recall/F1 cho bước trích xuất, NDCG@K cho bước xếp hạng

## Nguồn dữ liệu

Dữ liệu khóa học Coursera lấy từ các bộ dữ liệu công khai trên Kaggle (Coursera Courses Dataset 2021, Coursera Dataset 2024). Bản quyền thuộc các tác giả gốc.

## Tác giả

Trần Văn Tài, sinh viên CNTT, HUTECH
