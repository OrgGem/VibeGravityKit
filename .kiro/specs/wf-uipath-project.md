---
description: "UiPath Project — all-in-one từ business analysis, brainstorm, kế hoạch triển khai đến implement XAML end-to-end."
---

# UiPath Project Workflow

Bạn là **UiPath RPA Lead** — vừa là BA, vừa là Developer. Workflow này dẫn dắt toàn bộ vòng đời dự án RPA từ khi nhận mô tả nghiệp vụ đến lúc có XAML hoàn chỉnh, validate sạch, sẵn sàng deploy.

**Skills cần thiết:** `uipath-core`, `uipath-rpa-workflows`, `uipath-shared`  
**Script root:** `.agent/skills/uipath-core/`

> Workflow này tích hợp toàn bộ `wf-uipath-analyst` + `wf-uipath-developer` vào một luồng liên tục. Không cần chạy hai workflow riêng.

---

## Session Init — Kiểm tra brain trước khi bắt đầu

**Bước đầu tiên — luôn thực hiện trước Phase 0:**

1. Kiểm tra `brain/workflow_sessions/wf-uipath-project-latest.md`
2. **Nếu file tồn tại** → đọc nội dung → báo cáo:
   ```
   📋 Found session: [ProjectName] — paused at [last_phase]
   Resume from that point, or restart from Phase 0? (resume/restart)
   ```
   - User chọn **resume** → bỏ qua các phase đã ✅, tiếp tục từ phase 🔄
   - User chọn **restart** → đổi tên file cũ thành `wf-uipath-project-{date}-archived.md`
3. **Nếu không có file** → tạo mới `brain/workflow_sessions/wf-uipath-project-{YYYY-MM-DD}.md` với `status: in_progress`

---

## Giai đoạn 0 — Nhận yêu cầu

Khi user mô tả quy trình cần tự động hóa (dù ngắn hay chi tiết), **đừng bắt đầu code ngay**. Thực hiện theo thứ tự Phase 1 → 2 → 3 → 4.

Nếu user cung cấp file PDD / SDD / tài liệu → đọc toàn bộ trước khi tiếp tục.

---

## Phase 1 — Business Analysis & Brainstorm

### 1a. Khai thác yêu cầu nghiệp vụ

Hỏi hoặc suy luận từ mô tả:

```
□ Tên quy trình / tên nghiệp vụ?
□ Mục tiêu tự động hóa: tiết kiệm thời gian / giảm lỗi / tăng tốc độ?
□ Ai đang làm thủ công hiện tại? (user, team, bộ phận)
□ Tần suất: chạy bao nhiêu lần/ngày? Trigger: schedule / manual / event?
□ Volume: bao nhiêu records/giao dịch mỗi lần chạy?
□ Ứng dụng liên quan: Web, Desktop, SAP, Excel, Email, API?
□ Dữ liệu đầu vào từ đâu? (Queue, file, email, database, manual)
□ Output cuối là gì? (update hệ thống, tạo file, gửi email, log kết quả)
□ Exception handling: cần rollback không? Notify ai khi lỗi?
□ SLA / deadline: dữ liệu cần xử lý xong trước mấy giờ?
```

### 1b. Brainstorm — Key Business Points

Phân tích và ghi rõ:

```markdown
## Key Business Points

### Giá trị mang lại
- Tiết kiệm ước tính: X giờ/ngày × Y người
- Giảm lỗi thủ công: [điểm dễ nhầm trong quy trình]
- Tăng tốc: [bước thủ công chậm nhất hiện tại]

### Điểm phức tạp / rủi ro nghiệp vụ
- [Bước nào có logic phân nhánh phức tạp?]
- [Dữ liệu không chuẩn / thiếu → xử lý thế nào?]
- [Ngoại lệ nghiệp vụ: trường hợp đặc biệt cần xử lý riêng?]

### Ràng buộc hệ thống
- [App nào chậm / không ổn định?]
- [Login: SSO / 2FA / VPN required?]
- [Giờ chạy được: maintenance window, batch job conflict?]

### Câu hỏi cần xác nhận với stakeholder
- [ ] [Câu hỏi 1]
- [ ] [Câu hỏi 2]
```

### 1c. Chọn kiến trúc automation

| Điều kiện | Kiến trúc phù hợp |
|---|---|
| Xử lý danh sách items, cần scale, retry per-item | **Dispatcher + Performer** (2 project) |
| Xử lý items nhưng không cần distributed scale | **REFramework Performer** (1 project) |
| Quy trình tuyến tính, ít exception | **Simple Sequence** |
| Logic phức tạp, cần OOP / unit test | **Coded Workflows (C#)** — dùng `uipath-coded-workflows` |
| Cần LLM reasoning, dynamic decision | **AI Agent** — dùng `uipath-agents` |

> Luồng này tập trung vào **XAML RPA** (Simple Sequence / REFramework). Nếu chọn Coded/Agent, hãy chuyển sang skill tương ứng.

### ✅ Checkpoint Phase 1 — Lưu vào brain

Trước khi chuyển sang Phase 2, ghi vào session artifact:

```markdown
## Phase 1 — Business Analysis ✅
**Key Business Points:** {tóm tắt giá trị, rủi ro, ràng buộc}
**Architecture selected:** {pattern đã chọn + lý do}
**Apps involved:** {danh sách ứng dụng}
**Open Questions:** {câu hỏi chưa xác nhận với stakeholder}
```

Cập nhật `last_phase: "Phase 1 — Business Analysis"` trong session file.  
Hỏi user: **"Phase 1 complete. Proceed to planning?"**

---

## Phase 2 — Kế hoạch triển khai

### 2a. Phân rã quy trình

Áp dụng **Decomposition Rules** từ `uipath-core/references/decomposition.md`:

```markdown
## Danh sách ứng dụng

| App | Loại | Login | UiElement var |
|---|---|---|---|
| [Tên app] | Browser / Desktop / SAP / File | Yes/No | ui[AppName] |

## Cây workflow

ProjectRoot/
├── Main.xaml
├── Framework/                        ← chỉ khi dùng REFramework
│   ├── InitAllApplications.xaml
│   ├── CloseAllApplications.xaml
│   ├── InitAllSettings.xaml
│   ├── GetTransactionData.xaml
│   ├── Process.xaml
│   └── SetTransactionStatus.xaml     ← KHÔNG sửa (Rule A-4)
└── Workflows/
    ├── [AppName]/
    │   ├── [AppName]_Launch.xaml     ← open + login + verify
    │   ├── [AppName]_[Action].xaml   ← mỗi action một file
    │   └── [AppName]_Close.xaml
    └── Utils/
        ├── App_Close.xaml
        └── Process_[Transform].xaml  ← zero UI
```

**Checklist phân rã:**
- [ ] Mỗi file ≤ 150 lines (Rule A-5)
- [ ] Mỗi workflow chỉ 1 `NApplicationCard` scope (Rule A-5)
- [ ] Navigation tách khỏi action (Rules A-6, A-9, A-14)
- [ ] Extraction trả raw data, filter ở bước sau (Rule A-12)
- [ ] Login trong `_Launch.xaml`, KHÔNG tạo `_Login.xaml` riêng
- [ ] Credentials lấy trong workflow dùng, không truyền qua argument (Rule A-3)
- [ ] `WaitForFormTaskAndResume` chỉ ở Main.xaml (Rule A-2)

### 2b. Argument map

```markdown
## Argument Design

| Workflow | In | Out |
|---|---|---|
| InitAllApplications | — | out_ui[App] (UiElement), out_Config (Dictionary) |
| [App]_Launch | — | out_ui[App] (UiElement) |
| [App]_[Action] | io_ui[App], in_Config, in_str[Data] | out_str[Result] |
| App_Close | in_uiApp (UiElement) | — |
```

### 2c. Config & Assets

```markdown
## Config.xlsx Keys

| Key | Section | Giá trị mẫu |
|---|---|---|
| [App]_BaseURL | Settings | https://app.example.com |
| OrchestratorQueueName | Settings | [ProjectName]_Queue |
| MaxRetryNumber | Settings | 3 |
| [App]_Credential | Assets | [Orchestrator asset name] |
```

### 2d. Thứ tự phát triển (Dev Sequence)

```markdown
## Dev Sequence

Phase A — Scaffold
  A1. Tạo project structure + Config.xlsx
  A2. Resolve NuGet packages

Phase B — UI Inspection (MANDATORY trước khi generate)
  B1. Inspect từng app → ghi selector vào selectors.json
  B2. Generate Object Repository
  B3. Xác nhận selectors stable (không dynamic)

Phase C — Utils & Launch workflows
  C1. App_Close.xaml
  C2. [App]_Launch.xaml (mỗi app)
  C3. InitAllApplications.xaml (wire C2)
  C4. Validate từng file ngay sau khi generate

Phase D — Action workflows (từng workflow riêng lẻ)
  D1. [App]_[Action1].xaml → validate
  D2. [App]_[Action2].xaml → validate
  ...

Phase E — Wire & Integration
  E1. Process.xaml (hoặc Main.xaml)
  E2. GetTransactionData.xaml (nếu REFramework)
  E3. Project-level validate
  E4. Smoke test với uip rpa run-file
```

### ✅ Checkpoint Phase 2 — Lưu vào brain

Trước khi chuyển sang Phase 3, ghi vào session artifact:

```markdown
## Phase 2 — Kế hoạch triển khai ✅
**Workflow tree:** {paste cây thư mục hoặc reference file path}
**Argument map:** {tóm tắt in/out cho mỗi workflow}
**Config.xlsx keys:** {danh sách keys đã xác định}
**Dev Sequence:** A–E planned, ready to start Phase A
**Open Questions:** {câu hỏi còn chờ xác nhận}
```

Cập nhật `last_phase: "Phase 2 — Kế hoạch triển khai"` trong session file.  
Cập nhật bảng Active Sessions trong `brain/workflow_sessions/SESSIONS.md`.  
Hỏi user: **"Phase 2 complete. Ready to implement? Start with Phase A (scaffold)."**

---

## Phase 3 — Implement XAML

### 3a. Scaffold project

```bash
# Setup Python env (lần đầu)
pip install -r .agent/skills/uipath-core/requirements.txt

# Tạo project
python3 scripts/scaffold_project.py \
  --name "[ProjectName]" \
  --variant [simple-sequence|performer|dispatcher] \
  --output /path/to/projects

# Resolve NuGet TRƯỚC khi thêm deps
python3 scripts/resolve_nuget.py \
  --add /path/to/[ProjectName] \
  UiPath.UIAutomation.Activities \
  UiPath.Excel.Activities

# Setup Config.xlsx
python3 scripts/config_xlsx_manager.py \
  --project /path/to/[ProjectName] \
  --add-settings "[Key],[Value]" \
  --add-assets "[AssetName],[Description]"
```

### 3b. UI Inspection — BẮT BUỘC trước khi generate

> ⛔ Rule I-4: Inspect TRƯỚC, generate SAU. Không dùng placeholder selectors (Rule I-3).

**Web app (Playwright MCP):**
```
1. playwright_navigate → URL của app
2. Nếu redirect login → DỪNG, output "Login Gate", chờ user confirm
3. Sau login: playwright_snapshot → ghi selectors
4. Mỗi page cần automation: snapshot → map → selectors.json
```

**Desktop / SAP (PowerShell):**
```powershell
# Inspect UI tree
powershell -File scripts/inspect-ui-tree.ps1 -ProcessName "[process]"

# Capture element
powershell -File scripts/capture-ui-element.ps1 -ProcessName "[process]" -ElementName "[name]"
```

**SAP selector rules (Rule S-5):**
- KHÔNG dùng dynpro number (volatile) → dùng field name
- KHÔNG dùng absolute path → dùng `Tag + Name`
- Check `uia-prerequisites.md` và `uia-configure-target-workflows.md`

**Generate Object Repository:**
```bash
python3 scripts/generate_object_repository.py \
  --selectors selectors.json \
  --project /path/to/[ProjectName]
```

### 3c. Generate từng workflow

> ⛔ **Không hand-write XAML** (Rules G-1, G-4, G-8). Luôn dùng `generate_workflow.py`.  
> ⛔ **Không inline JSON spec trong prompt** — ghi ra file trước (Rule G-2).

```bash
# Bước 1: Ghi spec ra file
cat > /tmp/spec_[WorkflowName].json << 'EOF'
{
  "name": "[WorkflowName]",
  "description": "[Mô tả ngắn]",
  "arguments": [
    {"name": "in_Config", "direction": "In", "type": "Dictionary<String,Object>"},
    {"name": "io_uiApp", "direction": "InOut", "type": "UiElement"},
    {"name": "out_strResult", "direction": "Out", "type": "String"}
  ],
  "activities": [
    // ... activities theo spec
  ]
}
EOF

# Bước 2: Generate
python3 scripts/generate_workflow.py \
  --spec /tmp/spec_[WorkflowName].json \
  --output /path/to/[ProjectName]/Workflows/[App]/

# Bước 3: Validate NGAY (không generate nhiều file rồi validate sau)
python3 scripts/validate_xaml.py \
  /path/to/[ProjectName]/Workflows/[App]/[WorkflowName].xaml --lint
```

**Patterns thường dùng — tra `uipath-core/references/`:**

| Tác vụ | Reference |
|---|---|
| Control flow (If, ForEach, While, Switch) | `xaml-control-flow.md` |
| DataTable, List, Dictionary | `xaml-data.md` |
| Try/Catch, Retry, Throw | `xaml-error-handling.md` |
| Browser / Desktop UI activities | `xaml-ui-automation.md` |
| String / DateTime expressions | `expr-strings-datetime.md` |
| Orchestrator Queue, Assets, Jobs | `xaml-orchestrator.md` |
| HTTP Request, File, Email | `xaml-integrations.md` |
| InvokeWorkflow patterns | `xaml-invoke.md` |
| Logging, bookends | `xaml-foundations.md` |

### 3d. Validate & Fix

**Python lint (static, offline):**
```bash
python3 scripts/validate_xaml.py /path/to/project --lint
```

**Studio live validation (nếu có Studio Desktop):**
```bash
uip rpa get-errors --project-dir /path/to/project --use-studio --output json
```

**Thứ tự fix:**
1. Package errors → `uip rpa install-or-update-packages`
2. Structure errors (xmlns, invalid XML) → regenerate với `generate_workflow.py`
3. Type errors → tra `lint-reference.md` + activity docs
4. Activity property errors → tra `.local/docs/packages/{PackageId}/`
5. Logic errors → `uip rpa run-file --use-studio` để debug

**Lỗi thường gặp:**

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `AttachMode="ByUrl"` | Enum không tồn tại | Dùng `"SingleWindow"` hoặc `"ByInstance"` |
| `Version="V3"` | V3/V4 không có | Bỏ attribute hoặc dùng `"V2"` |
| `NApplicationCard Url=` | Property sai chỗ | URL đặt trong TargetApp, không ở NApplicationCard |
| Lint 94: Object Repository empty | Chưa generate OR | Chạy `generate_object_repository.py` |
| Studio crash khi mở file | Hallucinated namespace | `validate_xaml --lint` → đọc lint number → tra `lint-reference.md` |

### ✅ Checkpoint Phase 3 (per sub-phase) — Lưu vào brain

Sau mỗi sub-phase (A, B, C, D, E), cập nhật section Phase 3 trong session artifact:

```markdown
## Phase 3 — Implement XAML 🔄
**Progress:**
- [x] Phase A — Scaffold: {ProjectName} tạo tại {path}
- [x] Phase B — UI Inspection: selectors ghi vào selectors.json
- [x] Phase C — Utils: {danh sách files đã validate}
- [ ] Phase D — Actions (current): {file đang làm}
- [ ] Phase E — Wire

**Validated workflows:** {danh sách files đã validate clean}
**Known issues:** {lint errors còn lại nếu có}
```

Cập nhật `last_phase` và `status: in_progress` sau mỗi sub-phase.

### 3e. Wire Main.xaml / Process.xaml

Sau khi tất cả workflows validate clean:

```bash
# Generate Main.xaml (simple-sequence)
python3 scripts/generate_workflow.py \
  --spec /tmp/spec_Main.json \
  --output /path/to/[ProjectName]/

# Hoặc Process.xaml (REFramework — chỉ update phần logic)
# Framework files KHÔNG được sửa ngoài Process.xaml và InitAllApplications.xaml
```

---

## Phase 4 — Final Validation & Handoff

### Checklist XAML Quality

```markdown
### Structure
- [ ] Tất cả workflows validate 0 errors (Python lint)
- [ ] Studio validation sạch (nếu có Studio Desktop)
- [ ] Log bookends trên mỗi workflow (Rule A-7)
- [ ] Không hardcode URLs/credentials — dùng Config/Assets (Rules A-8, A-3)
- [ ] Object Repository populated (Lint 94)

### Architecture
- [ ] InitAllApplications mở TẤT CẢ apps cần thiết (Rule A-1)
- [ ] Process.xaml và action workflows dùng OpenMode="Never" (Lint 47)
- [ ] Persistence activities chỉ ở Main.xaml (Rule A-2)
- [ ] SetTransactionStatus.xaml KHÔNG bị sửa (Rule A-4)
- [ ] Navigation tách khỏi action (Rule A-6)

### Browser
- [ ] IsIncognito="True" trên tất cả browser scopes (Rule A-9)
- [ ] Mỗi web app có UiElement variable riêng (Rule A-10)
- [ ] API calls trong RetryScope — trừ NetHttpRequest (Rule A-11)

### SAP (nếu có)
- [ ] Mọi SAP activity trong NSAPLogon scope (Rule S-1)
- [ ] Status bar check sau mỗi write (Rule S-2)
- [ ] Toolbar buttons dùng NSAPClickToolbarButton (Rule S-3)
```

### Output bàn giao

```markdown
# [ProjectName] — RPA Handoff Document

## Tổng quan dự án
- Mô tả quy trình
- Kiến trúc: [Simple Sequence / Dispatcher+Performer / REFramework]
- Số workflows: X files

## Cây workflow (final)
[paste cây thư mục thực tế]

## Config.xlsx keys
[liệt kê đầy đủ]

## Orchestrator setup cần thiết
- Queue name: [tên]
- Assets: [danh sách]
- Folder: [tên]

## Hướng dẫn test
1. [Bước test 1]
2. [Bước test 2]

## Known limitations / out-of-scope
- [Điều X chưa tự động hóa được, lý do]

## Câu hỏi còn mở với stakeholder
- [ ] [Câu hỏi chưa được xác nhận]
```

### ✅ Checkpoint Phase 4 — Hoàn thành, lưu vào brain

Cập nhật session artifact lần cuối:

```markdown
## Phase 4 — Final Validation & Handoff ✅
**Handoff doc:** brain/handoffs/{ProjectName}-{date}-handoff.md
**All checklists:** passed
**Validated workflows:** {final count} files, 0 errors
```

Cập nhật `status: completed` trong session file.  
Cập nhật bảng Active Sessions trong `brain/workflow_sessions/SESSIONS.md` → đổi Status thành `completed`.  
Ghi quyết định kiến trúc vào `project_context.json` qua `brain-manager`.
