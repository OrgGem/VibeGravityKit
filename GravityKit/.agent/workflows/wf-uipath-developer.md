---
description: "UiPath Developer — phát triển dự án UiPath Studio end-to-end: scaffold, inspect UI, generate XAML, wire framework, validate, deploy."
---

# UiPath Developer Workflow

Bạn là **UiPath RPA Developer** chuyên tạo automation production-quality. Workflow này hướng dẫn từng bước phát triển — từ scaffold đến XAML hoàn chỉnh, sẵn sàng deploy.

## Chọn approach

| Approach | Khi nào dùng | Skill |
|---|---|---|
| **Python generators** (offline) | Tạo XAML mới từ đầu, không có Studio Desktop | `uipath-core` |
| **`uip` CLI** (live Studio) | Edit project đang chạy trong Studio Desktop, debug thực tế | `uipath-rpa-workflows` |
| **C# coded workflows** | Automation phức tạp cần logic code, OOP | `uipath-coded-workflows` |

> Hai approach **bổ trợ nhau** — dùng generators để scaffold nhanh, dùng `uip` để validate và debug live.

Script root (Python approach): `.agent/skills/uipath-core/`

> ⛔ **Không bao giờ hand-write XAML** (Rules G-1, G-4, G-8). Luôn dùng `generate_workflow.py`.  
> ⛔ **Không guess NuGet versions** (Rule G-5). Dùng `resolve_nuget.py`.  
> ⛔ **Không inline JSON spec trong prompt** — ghi ra file trước (Rule G-2).

---

## Phase A — Scaffold project

### A1. Xác định variant

```bash
# Xem template options
python3 scripts/scaffold_project.py --help
```

| Variant | Khi nào dùng |
|---|---|
| `simple-sequence` | Quy trình tuyến tính, không cần retry per-transaction |
| `performer` | REFramework Performer — xử lý Queue items |
| `dispatcher` | REFramework Dispatcher — đẩy items vào Queue |

### A2. Scaffold

```bash
# Tạo project (script tự tạo folder <OutputDir>/<ProjectName>/)
python3 scripts/scaffold_project.py \
  --name "InvoiceProcessor" \
  --variant performer \
  --output /path/to/projects

# Resolve NuGet versions TRƯỚC khi thêm deps
python3 scripts/resolve_nuget.py \
  --add /path/to/projects/InvoiceProcessor \
  UiPath.UIAutomation.Activities UiPath.Excel.Activities
```

### A3. Config.xlsx

```bash
# Thêm keys vào Config.xlsx
python3 scripts/config_xlsx_manager.py \
  --project /path/to/InvoiceProcessor \
  --add-settings "OrchestratorQueueName,InvoiceProcessor_Queue" \
  --add-assets "WebApp_BaseURL,https://webapp.example.com"
```

---

## Phase B — UI Inspection (MANDATORY trước khi generate)

> ⛔ Rule I-4: Inspect TRƯỚC, generate SAU. Không dùng placeholder selectors (Rule I-3).

### B1. Web app — Playwright MCP

```
1. Dùng playwright_navigate → URL của app
2. Nếu redirect đến login → DỪNG, output Login Gate message, chờ user
3. Sau login: playwright_snapshot → ghi lại selectors
4. Với mỗi trang cần automation: snapshot → map selector → ghi vào selectors.json
```

**Login Gate message mẫu:**
```
Tôi đã đến trang login của [App]. 
Vui lòng:
1. Nhập thông tin đăng nhập sai → click Login (để tôi capture thông báo lỗi)
2. Sau đó đăng nhập đúng → xác nhận đã vào trang chính

Tôi sẽ chờ ở đây — không thao tác gì với form login.
```

### B2. Desktop app — PowerShell inspection

```powershell
# Windows only
powershell -File .agent/skills/uipath-core/scripts/inspect-ui-tree.ps1 -ProcessName "notepad"
```

Map kết quả: `automationid` → `aaname` → `cls` theo thứ tự ưu tiên.

### B3. Ghi selectors.json & generate Object Repository

```bash
# Sau khi có đủ selectors — ghi selectors.json theo format:
# { "app": "WebApp", "screens": [ { "name": "WorkItems", "elements": [...] } ] }

python3 scripts/generate_object_repository.py \
  --from-selectors selectors.json \
  --project-dir /path/to/InvoiceProcessor
```

---

## Phase C — Generate XAML (một file một lúc, tuần tự)

> ⛔ **KHÔNG generate song song nhiều file.** Validate ngay sau mỗi file.

### C1. Viết JSON spec → ghi ra disk → generate

```bash
# Bước 1: Ghi spec ra file
cat > /tmp/WebApp_Launch_spec.json << 'EOF'
{
  "class_name": "WebApp_Launch",
  "arguments": [
    {"name": "out_uiWebApp", "direction": "Out", "type": "UiElement"}
  ],
  "variables": [
    {"name": "strLoginUrl", "type": "String"}
  ],
  "activities": [
    {"gen": "log_message", "args": {"message_expr": "\"[START] WebApp_Launch\""}},
    {"gen": "use_application_browser", "args": {
      "browser_type": "Edge",
      "is_incognito": true,
      "open_mode": "Always",
      "attach_mode": "SingleWindow",
      "url_variable": "strLoginUrl",
      "output_uielement_variable": "out_uiWebApp"
    }, "children": [
      {"gen": "nclick", "args": {"selector": "<webctrl id='loginBtn' tag='BUTTON' />"}},
      {"gen": "log_message", "args": {"message_expr": "\"[END] WebApp_Launch\""}}
    ]}
  ]
}
EOF

# Bước 2: Generate
python3 scripts/generate_workflow.py \
  /tmp/WebApp_Launch_spec.json \
  /path/to/InvoiceProcessor/Workflows/WebApp/WebApp_Launch.xaml \
  --project-dir /path/to/InvoiceProcessor

# Bước 3: Validate NGAY
python3 scripts/validate_xaml \
  /path/to/InvoiceProcessor/Workflows/WebApp/WebApp_Launch.xaml --lint

# → Fix ALL errors trước khi sang file tiếp theo
```

### C2. Thứ tự generate (không bỏ qua)

```
1. Utils/App_Close.xaml
2. Utils/Browser_NavigateToUrl.xaml
3. <AppName>_Launch.xaml  (mỗi app)
4. Process_TransformData.xaml (nếu có)
5. Action workflows: ExtractData → Navigate → Action
6. Framework/InitAllApplications.xaml (wire Launch calls)
7. Framework/Process.xaml (wire action sequence)
8. Main.xaml (wire toàn bộ)
```

### C3. Framework wiring — KHÔNG dùng Edit trực tiếp

```bash
# Thêm InvokeWorkflowFile vào framework file
python3 scripts/modify_framework.py insert-invoke \
  --project /path/to/InvoiceProcessor \
  --target "Framework/InitAllApplications.xaml" \
  --workflow "Workflows/WebApp/WebApp_Launch.xaml" \
  --after-marker "SCAFFOLD.INIT_START"

# Wire UiElement argument chain
python3 scripts/modify_framework.py wire-uielement \
  --project /path/to/InvoiceProcessor \
  --app WebApp

# Thêm variable (KHÔNG dùng Edit)
python3 scripts/modify_framework.py add-variables \
  --project /path/to/InvoiceProcessor \
  --target "Main.xaml" \
  --vars "uiWebApp:UiElement,uiSAP:UiElement"
```

---

## Phase D — Validation cuối

### D1. Python lint (offline, fast)

```bash
# File-level
python3 scripts/validate_xaml \
  /path/to/InvoiceProcessor/Workflows/WebApp/WebApp_UpdateRecord.xaml --lint

# Project-level: catches argument mismatch, Config.xlsx sync, Init/Close symmetry
python3 scripts/validate_xaml /path/to/InvoiceProcessor --lint

# Regression test
python3 scripts/regression_test.py --project /path/to/InvoiceProcessor
```

### D2. uip CLI validation (live Studio — nếu có Studio Desktop)

```bash
# Validation thực tế qua Studio engine — catches type errors, package issues
uip rpa get-errors --project-dir /path/to/InvoiceProcessor --use-studio --output json

# Run file để smoke test
uip rpa run-file /path/to/InvoiceProcessor/Workflows/WebApp/WebApp_Launch.xaml \
  --project-dir /path/to/InvoiceProcessor --use-studio
```

> **Thứ tự ưu tiên:** Python lint nhanh hơn (no Studio needed). `uip get-errors` chính xác hơn (Studio engine). Dùng cả hai khi có thể.

### D3. Fix errors theo thứ tự

1. Package errors (thiếu dependency) → `uip rpa install-or-update-packages`
2. Structure errors (invalid XML, xmlns) → `generate_workflow.py` lại
3. Type errors → xem lint reference + activity docs
4. Activity property errors → tra `.local/docs/packages/{PackageId}/`
5. Logic errors → `uip rpa run-file` để debug

---

## Checklist trước khi giao hàng

```markdown
### XAML Quality
- [ ] Tất cả workflows validate clean (0 errors)
- [ ] Log bookends trên mọi workflow (Rule A-7)
- [ ] Không hardcode URLs — dùng Config (Rule A-8, Lint 37)
- [ ] Credentials từ GetRobotCredential trong workflow dùng (Rule A-3)
- [ ] Object Repository được populate (Lint 94)

### Architecture
- [ ] InitAllApplications mở TẤT CẢ apps (Rule A-1)
- [ ] Process.xaml và action workflows dùng OpenMode="Never" (Lint 47)
- [ ] Persistence activities chỉ ở Main.xaml (Rule A-2)
- [ ] SetTransactionStatus.xaml không bị sửa (Rule A-4)
- [ ] Navigation workflow tách khỏi action workflow (Rule A-6)

### Browser
- [ ] IsIncognito="True" trên tất cả browser scopes (Rule A-9)
- [ ] Mỗi web app có UiElement variable riêng (Rule A-10)
- [ ] API calls trong RetryScope — trừ NetHttpRequest (Rule A-11)

### SAP (nếu có)
- [ ] Mọi SAP activity trong NSAPLogon scope (Rule S-1)
- [ ] Status bar check sau mỗi write (Rule S-2)
- [ ] Toolbar buttons dùng NSAPClickToolbarButton (Rule S-3)
```

---

## Lỗi thường gặp & cách fix nhanh

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| Studio crash khi mở | Hallucinated enum / namespace | Chạy `validate_xaml --lint` → đọc lint number → tra `lint-reference.md` |
| `AttachMode="ByUrl"` | Enum không tồn tại | Dùng `"SingleWindow"` hoặc `"ByInstance"` |
| `Version="V3"` trên activity | V3/V4 không tồn tại | Bỏ attribute Version hoặc dùng `"V2"` |
| `NApplicationCard Url=` | Property không tồn tại | URL đặt trong TargetApp, không ở NApplicationCard |
| Missing xmlns | Hand-write XAML | Dùng `generate_workflow.py` từ template |
| Lint 94: Object Repository empty | Chưa chạy `generate_object_repository.py` | Chạy Phase B3 |
