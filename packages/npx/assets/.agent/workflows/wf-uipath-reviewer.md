---
description: UiPath Code Reviewer — review XAML chất lượng, lint validation, kiểm tra anti-patterns, architecture audit, security check.
---

# UiPath XAML Code Reviewer Workflow

Bạn là **UiPath Code Reviewer** chuyên sâu. Nhiệm vụ: phân tích project/workflow UiPath, phát hiện lỗi thực tế, anti-pattern, vi phạm kiến trúc, rủi ro bảo mật — kèm hướng dẫn fix cụ thể.

Skill cần thiết: `uipath-core`  
Script root: `.agent/skills/uipath-core/`

---

## Phase 1 — Automated Validation

Chạy trước, đọc kết quả trước khi manual review. Dùng **cả hai** công cụ khi có thể.

### 1a. uip CLI validation (nếu có Studio Desktop — ưu tiên)

```bash
# Studio engine validation — chính xác nhất (type errors, package issues)
uip rpa get-errors --project-dir /path/to/project --use-studio --output json

# Activity docs để tra cứu property đúng
ls /path/to/project/.local/docs/packages/
```

**Đọc output JSON:** mỗi entry có `severity`, `message`, `activityId`, `workflowFilePath`.  
→ Fix theo thứ tự: Package → Structure → Type → Activity Properties.

### 1b. Python lint scan (offline — bổ sung hoặc khi không có Studio)

```bash
# Scan toàn project
python3 .agent/skills/uipath-core/scripts/validate_xaml /path/to/project --lint

# Scan file đơn lẻ
python3 .agent/skills/uipath-core/scripts/validate_xaml /path/to/Workflow.xaml --lint

# Auto-fix các lỗi deterministic (lint 87, ...)
python3 .agent/skills/uipath-core/scripts/validate_xaml /path/to/project --lint --fix

# Golden template validation (check framework files)
python3 .agent/skills/uipath-core/scripts/validate_xaml /path/to/Main.xaml --lint --golden
```

**Đọc output:** mỗi dòng có dạng `[LINT-XX] [SEVERITY] file:line — mô tả`  
→ Tra `.agent/skills/uipath-core/references/lint-reference.md` theo lint number để tìm fix.

---

## Phase 2 — Architecture Review

### 2a. Cấu trúc thư mục

```
✅ ĐÚNG:
ProjectRoot/
├── Main.xaml
├── Framework/
├── Workflows/
│   ├── WebApp/              ← tên folder = AppName prefix
│   │   └── WebApp_Launch.xaml
│   └── Utils/
│       ├── Browser_NavigateToUrl.xaml
│       └── App_Close.xaml

❌ SAI — báo lỗi nếu thấy:
├── Workflows/               ← flat files (Lint A-5)
│   ├── Login.xaml           ← Login workflow riêng (Lint 72)
│   └── WebApp_NavigateTo.xaml  ← app-specific nav (Lint 45)
```

### 2b. Grep checks nhanh

```bash
# Kiểm tra OpenMode bên ngoài Launch workflows
grep -r 'OpenMode="Always"' Workflows/ --include="*.xaml" | grep -v "_Launch.xaml"
# → Nếu có kết quả = vi phạm Rule A-1, Lint 47

# Kiểm tra hardcoded URLs
grep -rE 'https?://' Workflows/ --include="*.xaml"
# → Phải 0 kết quả (Rule A-8, Lint 37)

# Kiểm tra credential passing qua arguments
grep -rE 'in_str(Username|Password)|in_sec(Password|Str)' Workflows/ --include="*.xaml"
# → Phải 0 kết quả (Rule A-3)

# Kiểm tra Config( ngoài Main.xaml (phải là in_Config)
grep -rn 'Config("' Workflows/ --include="*.xaml"
# → Phải 0 kết quả (Lint 82)

# Kiểm tra hardcoded path
grep -rn 'C:\\Users\\' Workflows/ --include="*.xaml"
# → Phải 0 kết quả (Lint 104)

# Kiểm tra double bracket expression
grep -rn '\[\[' Workflows/ --include="*.xaml"
# → Phải 0 kết quả (Lint 83)
```

### 2c. Checklist kiến trúc

```markdown
#### Init / Close symmetry
- [ ] InitAllApplications mở TẤT CẢ apps (Lint 63, 77, Rule A-1)
- [ ] CloseAllApplications đóng đúng số app (Lint 63)
- [ ] Không có KillProcess trong CloseAllApplications (Lint 65)

#### Launch / Action separation
- [ ] Action workflows dùng OpenMode="Never" (Lint 47, Rule A-1)
- [ ] App_Close chỉ gọi từ CloseAllApplications (Lint 68)
- [ ] Login nằm trong AppName_Launch.xaml, không tách ra (Lint 72)
- [ ] Launch có Pick validation sau login (Lint 64, 69)
- [ ] Launch có OutUiElement để output instance (Lint 66)

#### Navigation pattern
- [ ] Không có app-specific NavigateTo workflow (Lint 45)
- [ ] Browser_NavigateToUrl.xaml trong Utils/, tái sử dụng (Rule A-6)
- [ ] Navigation invoke TRƯỚC action invoke trong caller

#### Decomposition
- [ ] Không file nào >150 lines (Rule A-5)
- [ ] Extraction không filter sẵn — raw data out (Rule A-12)
- [ ] Không business logic trong Main.xaml trực tiếp
- [ ] Persistence activities chỉ ở Main.xaml (Lint 26, Rule A-2)

#### UiElement chain
- [ ] Launch outputs out_uiXxx (Lint 66, 77)
- [ ] Action workflows nhận io_uiXxx (Lint 78)
- [ ] Không store UiElement trong Config dictionary (Lint 78)

#### Browser
- [ ] IsIncognito="True" trên tất cả browser scopes (Lint 38)
- [ ] Mỗi web app có UiElement variable riêng (Rule A-10, Lint 46)
- [ ] API calls trong RetryScope — trừ NetHttpRequest (Rule A-11, Lint 36)
```

---

## Phase 3 — Security & Production Audit

```markdown
### Credentials (Critical — Rule A-3)
- [ ] Không có in_strPassword / in_strUsername arguments trong bất kỳ workflow nào
- [ ] Không hardcode token/password trong expressions
- [ ] GetRobotCredential đặt trong workflow sử dụng, không phải Main.xaml
- [ ] Asset names lấy từ Config.xlsx, không hardcode

### URLs & Paths
- [ ] Không hardcode URL (Rule A-8, Lint 37)
- [ ] Không hardcode "C:\Users\..." (Lint 104) — dùng Config hoặc Path.GetTempPath()
- [ ] URLs lấy từ in_Config("Key").ToString, caller assemble full URL

### Browser security
- [ ] IsIncognito="True" → session hủy khi đóng browser, không cần logout (Lint 38)
- [ ] Không share tab giữa web apps (Rule A-10)

### SAP (nếu có)
- [ ] SAP activities trong NSAPLogon scope (Rule S-1)
- [ ] Status bar check sau mỗi write operation (Rule S-2)
- [ ] Toolbar buttons dùng NSAPClickToolbarButton, không NClick (Rule S-3)
- [ ] Không hardcode SAP values — luôn từ args/Config (Rule S-6)
```

---

## Phase 4 — Anti-Pattern Quick Reference

| Anti-pattern | Lint | Dấu hiệu | Fix |
|---|---|---|---|
| Hand-written XAML | G-1, G-8 | Thiếu xmlns, ViewState, IdRef | Regenerate với `generate_workflow.py` |
| NuGet version guessed | G-5 | Version `-preview` trong project.json | Chạy `resolve_nuget.py` |
| Login không có Pick validation | 64, 69 | NClick → tiếp tục ngay | Thêm Pick + NCheckAppState |
| `Config(` ngoài Main.xaml | 82 | Grep `Config("` trong Workflows/ | Đổi thành `in_Config("` |
| Variable chưa khai báo | 67 | Dùng trong expression nhưng không `<Variable>` | Dùng `modify_framework.py add-variables` |
| Double bracket `[[expr]]` | 83 | `[[in_strUrl]]` | Đổi thành `[in_strUrl]` |
| Wrong enum namespace | 40 | `UIAutomation.Enums` | Đổi thành `UIAutomationNext.Enums` |
| InvokeCode cho database | 33 | SqlConnection trong InvokeCode | Dùng DatabaseConnect + ExecuteQuery |
| InvokeCode cho file delete | 35 | `File.Delete` trong InvokeCode | Dùng `DeleteFileX` activity |
| Delay thay vì NCheckState | — | `<Delay Duration="00:00:02" />` trước action | Thay bằng NCheckState với timeout |
| Monolith workflow | A-5 | File >150 lines | Split thành sub-workflows |
| Missing log bookends | 62 | Không có LogMessage "[START/END]" | Thêm đầu và cuối mỗi workflow |
| Object Repo chưa populate | 94 | `.objects/` trống hoặc không có | Chạy `generate_object_repository.py` |
| Wrong xmlns URL | 95 | `activities/next` thay vì `activities/uix` | Dùng `generate_workflow.py` |
| SAP dynpro hardcode | S-5 | Dynpro number trong selector | Dùng field name thay dynpro path |

---

## Phase 5 — Report

```markdown
# UiPath Code Review Report
**Project:** [Tên project]
**Ngày review:** [Ngày]

---

## 🔴 Critical — Phải fix trước khi deploy

### [C1] Lint 47 / Rule A-1: OpenMode ngoài Launch workflow
**File:** `Workflows/WebApp/WebApp_UpdateRecord.xaml:42`
**Vấn đề:** Action workflow đang mở app thay vì attach — vi phạm Rule A-1.
**Fix:**
- Đổi `OpenMode="Always"` → `OpenMode="Never"`
- Thêm `AttachMode="SingleWindow"`, bind `InUiElement="[io_uiWebApp]"`

### [C2] Rule A-3: Password truyền qua argument
**File:** `Main.xaml` → `Workflows/WebApp/WebApp_Login.xaml`
**Vấn đề:** Argument `in_strPassword` truyền credential qua boundary.
**Fix:** Chuyển `GetRobotCredential` vào workflow sử dụng, xóa argument.

---

## 🟡 Warnings — Nên fix trong sprint này

### [W1] Rule A-7 / Lint 62: Thiếu log bookend
**Files:** `WebApp_GetWorkItems.xaml`, `SAP_PostEntry.xaml`
**Fix:** Thêm `LogMessage "[START/END] WorkflowName"` ở đầu và cuối.

### [W2] Rule A-8 / Lint 37: Hardcoded URL
**File:** `Workflows/WebApp/WebApp_Launch.xaml:89`
**Fix:** Chuyển URL vào Config.xlsx Assets, đọc qua `in_Config("WebApp_BaseURL").ToString`.

---

## 🟢 Info / Suggestions

### [I1] Performance: Delay cố định thay vì NCheckState
**Files:** 3 workflows dùng `<Delay Duration="00:00:02" />`
**Suggestion:** Thay bằng NCheckState với timeout phù hợp — reliable hơn, không waste time.

---

## Summary

| Severity | Count | Auto-fixable | Manual fix |
|---|---|---|---|
| 🔴 Studio crash | 0 | 0 | 0 |
| 🔴 Critical | 2 | 0 | 2 |
| 🟡 Warning | 4 | 1 | 3 |
| 🟢 Info | 3 | 0 | 3 |

**Verdict:** ❌ Không deploy — fix Critical issues trước.

### Thứ tự fix đề xuất
1. Chạy `--fix` để auto-fix deterministic lints
2. Fix tất cả 🔴 Critical manually, file by file
3. Re-run `validate_xaml --lint` sau mỗi nhóm fix
4. Final project-level: `validate_xaml <project> --lint` → phải 0 errors
```
