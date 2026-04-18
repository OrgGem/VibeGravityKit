---
description: Document Generator - Orchestrates the gen-doc group to create, edit, format Word, Excel, and PDF files safely.
---

# Document Generator Workflow

## Mở Đầu (Introduction)
Workflow này được thiết kế theo tiêu chuẩn tích hợp, **tương thích hoàn toàn với Antigravity và Kiro Agent**. Nhiệm vụ chính là điều hướng tác vụ xử lý tài liệu vào một trong 3 nhánh của nhóm `gen-doc` một cách mượt mà và an toàn nhất (tránh hỏng file).

## Core Competencies
1. **Word Documents (`gen-doc-docx`)**: Tạo mới, điền nội dung, thiết kế template, và xử lý thẻ XML Word.
2. **Spreadsheets (`gen-doc-xlsx`)**: Phân tích data, thêm cột/hàng có công thức thông minh (không làm hỏng pivot).
3. **PDF Pipeline (`gen-doc-pdf`)**: Sinh văn bản PDF dạng vector tuyệt đẹp bằng ReportLab và Node.js.
4. **Presentations (`ppt-master`)**: Tạo slide trình chiếu chuyên nghiệp, tuân thủ nghiêm ngặt 8 quy tắc validation (Eight Confirmations) và render SVG tuần tự.

## Workflow

### Giai đoạn 1: Phân rã yêu cầu (Requirement Analysis & Tool Selection)
*Mục tiêu: Gọi đúng skill và không bị ảo giác dữ liệu.*
1. **Cây quyết định:**
   * Nếu người dùng yêu cầu "tạo báo cáo" và không chỉ định file -> Mặc định dùng `gen-doc-pdf` (dùng dạng tĩnh để hiển thị đẹp).
   * Nếu cần "thay đổi giá trị" bảng tính -> Chạy `gen-doc-xlsx`. LƯU Ý: Tuyệt đối không dùng `openpyxl` để sửa trực tiếp file gốc, phải dùng các script `xlsx_unpack.py` để tháo lắp.
   * Nếu yêu cầu "làm hợp đồng / công văn" -> Sử dụng `gen-doc-docx`. Cần đọc `scenario_a_create.md` ở references của nó.
   * Nếu yêu cầu "tạo slide / bài thuyết trình" -> Sử dụng quy trình `ppt-master` (Đọc kỹ `instructions.md` trong mục knowledge base). BẮT BUỘC tuân thủ Sequential Pipeline và Block Hard Stop để chờ người dùng confirm trước khi render.

### Giai đoạn 1.5: Giao tiếp chiến lược & Xác nhận tham số (⛔ BLOCKING)
*Mục tiêu: Thu thập đầy đủ dữ kiện thiết kế để file sinh ra không bị sai lệch.*
**LUẬT BẮT BUỘC (HARD STOP)**: Agent phải liệt kê các câu hỏi dưới đây (tuỳ theo định dạng) cho User. **BẮT BUỘC PHẢI DỪNG (BLOCK)** chờ User trả lời và chốt tham số xong mới được phép tiến hành viết code/tạo file. TUYỆT ĐỐI không được tự ý "đoán" hoặc bỏ qua phase này.

* **Dành cho Word (DOCX):**
  1. Loại hình & Đối tượng (Template: Hợp đồng, báo cáo nhanh, hay thư ngỏ?)
  2. Bố cục bảng biểu & Data cứng (Cần biểu mẫu động không?)
  3. Yêu cầu CJK/Font chữ đặc thù.

* **Dành cho Spreadsheet (XLSX):**
  1. Loại Data cần chứa (Tài chính, Tracker nhân sự, hay Form nhập liệu?)
  2. Các công thức (Formulas) bắt buộc phải có.
  3. Quy chuẩn màu sắc (Dựa theo `references/format.md`).

* **Dành cho PDF (PDF Pipeline):**
  1. Loại Design Pattern (report, resume, proposal, magazine, darkroom,...)?
  2. Màu nhấn (Accent color) và Mood chủ đạo?
  3. Tiêu đề chính, Tác giả, và Phụ đề (Subtitle).

### Giai đoạn 2: Xử lý Môi trường (Environment Bootstrapping)
*Mục tiêu: Không bị văng lỗi command not found.*
- Các tool `gen-doc` có core bằng .NET, Node.js và Python do đó phải Setup:
  ```bash
  # Tùy theo doc, phải chạy script chuẩn bị 1 lần duy nhất trong session:
  bash .agent/skills/gen-doc-docx/scripts/env_check.sh
  # Hoặc:
  bash .agent/skills/gen-doc-pdf/scripts/make.sh check
  ```

### Giai đoạn 3: Thực thi (Execution)
*Mục tiêu: Đẩy data vào script và xuất file.*
- Agent được quyền viết các file `content.json`, `table.json` trước bằng tool File Edit/Write.
- Sau đó chạy các CLI Pipeline. **Tuyệt đối tuân thủ đường dẫn tuyệt đối (absolute path/ relative to root workspace)** để script không bị lỗi ngầm.
  ```bash
  dotnet run --project .agent/skills/gen-doc-docx/scripts/dotnet/MiniMaxAIDocx.Cli -- create --type report ...
  ```

### Giai đoạn 4: QA Kiểm thử trước khi giao (Validation)
*Mục tiêu: Chắc chắn file vừa sinh ra mở lên được, không bị MS Office báo corrupt.*
- Đối với Word: Chạy Gate Check (validate XSD business-rules). Đọc file `docx_preview.sh`.
- Đối với Excel: Chạy `.agent/skills/gen-doc-xlsx/scripts/formula_check.py` để check cú pháp thẻ XML.
