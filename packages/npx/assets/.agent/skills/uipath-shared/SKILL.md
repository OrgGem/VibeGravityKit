---
name: uipath-shared
description: Shared UiPath reference docs — uip CLI reference, UI Automation prerequisites & configuration, debugging, selector recovery, multi-step flows, validation loop.
tags: [uipath, rpa, reference, cli, ui-automation]
---

# UiPath Shared References

Bộ tài liệu tham chiếu dùng chung cho tất cả UiPath skills. Không chứa scripts hay generators — chỉ là reference docs để tra cứu khi phát triển.

## Files trong skill này

| File | Nội dung |
|---|---|
| `cli-reference.md` | Reference đầy đủ cho `uip rpa` CLI — tất cả commands, options, IPC patterns |
| `ui-automation-guide.md` | Hướng dẫn tổng quan UI Automation với `uip rpa` |
| `uia-prerequisites.md` | Yêu cầu trước khi dùng UI Automation (Studio version, extensions, process check) |
| `uia-configure-target-workflows.md` | Cấu hình target workflows — attach, open mode, UiElement chaining |
| `uia-debug-workflow.md` | Debug UI Automation workflows — logs, breakpoints, highlight selectors |
| `uia-multi-step-flows.md` | Patterns cho multi-step UI flows — navigation, state management |
| `uia-selector-recovery.md` | Recovery khi selector thay đổi — dynamic selectors, fallback strategies |
| `validation-loop.md` | Validation loop pattern — lint → fix → re-validate cycle |

## Khi nào đọc

- Trước khi dùng `uip rpa` commands → đọc `cli-reference.md`
- Khi setup project UI Automation mới → đọc `uia-prerequisites.md` + `uia-configure-target-workflows.md`
- Khi selector bị lỗi sau UI change → đọc `uia-selector-recovery.md`
- Khi debug automation không chạy đúng → đọc `uia-debug-workflow.md`
- Khi thiết kế quy trình nhiều bước → đọc `uia-multi-step-flows.md`
- Khi validate project → đọc `validation-loop.md`

## Mối quan hệ với skills khác

- `uipath-rpa-workflows` và `uipath-coded-workflows` reference `../shared/` cho CLI và UIA docs
- `uipath-core` dùng Python generators (offline) — không phụ thuộc vào shared này
- `uipath-platform` dùng `uip` platform commands (khác `uip rpa`) — xem `uipath-platform/references/uip-commands.md`
