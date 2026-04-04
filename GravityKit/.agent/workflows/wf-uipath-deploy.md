---
description: UiPath Deploy — pack, publish, deploy lên Orchestrator; quản lý assets, queues, folders; Integration Service; Test Manager.
---

# UiPath Deploy & Platform Workflow

Bạn là **UiPath Platform Engineer**. Workflow này hướng dẫn toàn bộ vòng đời deploy — từ pack project đến publish Orchestrator, quản lý resources, và CI/CD.

Skill cần thiết: `uipath-platform`  
CLI: `uip` (UiPath CLI)

> ⚠️ **Luôn kiểm tra auth trước mọi cloud command.**  
> `uip login status --output json`

---

## Phase 0 — Xác thực môi trường

```bash
# Kiểm tra login status
uip login status --output json

# Login nếu chưa
uip login

# Kiểm tra tenant hiện tại
cat ~/.uipath/.auth
```

**Tokens được lưu tại `~/.uipath/.auth`** — có thể tái dùng cho REST API calls trực tiếp khi CLI không đủ.

---

## Phase 1 — Pack & Publish

### 1a. Pack project

```bash
# Pack project thành .nupkg
uip rpa pack --project-path /path/to/project --output /path/to/output

# Pack với version override
uip rpa pack --project-path /path/to/project --output /path/to/output --version 1.2.3
```

> **Lưu ý:** Version phải được tăng nếu re-publish cùng tên — Orchestrator từ chối publish duplicate version.

### 1b. Publish lên Orchestrator

```bash
# Publish .nupkg lên Orchestrator
uip package publish --package /path/to/project.1.0.0.nupkg

# Publish với folder cụ thể
uip package publish --package /path/to/project.1.0.0.nupkg --folder MyFolder
```

### 1c. Deploy / Activate process

```bash
# Tạo process mới từ package đã publish
uip orchestrator process create --name "MyProcess" --package-name "MyProject" --package-version "1.0.0" --folder MyFolder

# Update process lên version mới
uip orchestrator process update --name "MyProcess" --package-version "1.1.0" --folder MyFolder
```

---

## Phase 2 — Quản lý Orchestrator Resources

### 2a. Folders

```bash
# List folders
uip orchestrator folder list --output json

# Tạo folder
uip orchestrator folder create --name "Production" --parent-folder "Default"
```

### 2b. Assets

```bash
# List assets
uip orchestrator asset list --folder MyFolder --output json

# Tạo asset text
uip orchestrator asset create --name "WebApp_BaseURL" --type Text --value "https://app.example.com" --folder MyFolder

# Tạo credential asset
uip orchestrator asset create --name "WebApp_Credentials" --type Credential --folder MyFolder

# Update asset
uip orchestrator asset update --name "WebApp_BaseURL" --value "https://newapp.example.com" --folder MyFolder

# Get asset value
uip orchestrator asset get --name "WebApp_BaseURL" --folder MyFolder --output json
```

> **Rule A-3 compliance:** Asset names phải khớp với tên dùng trong `GetRobotCredential` trong workflows.

### 2c. Queues

```bash
# List queues
uip orchestrator queue list --folder MyFolder --output json

# Tạo queue
uip orchestrator queue create --name "InvoiceProcessor_Queue" --folder MyFolder

# Add queue item
uip orchestrator queue item add --queue-name "InvoiceProcessor_Queue" --data '{"InvoiceId":"INV-001","Amount":1500}' --folder MyFolder

# Get queue items
uip orchestrator queue item list --queue-name "InvoiceProcessor_Queue" --folder MyFolder --output json
```

### 2d. Storage Buckets

```bash
# List buckets
uip orchestrator bucket list --folder MyFolder --output json

# Upload file
uip orchestrator bucket file upload --bucket-name "ReportBucket" --file-path /local/report.xlsx --blob-name "reports/2025/report.xlsx" --folder MyFolder

# Download file
uip orchestrator bucket file download --bucket-name "ReportBucket" --blob-name "reports/2025/report.xlsx" --output /local/downloaded.xlsx --folder MyFolder
```

---

## Phase 3 — Integration Service

### 3a. Kiểm tra connectors

```bash
# List available connectors
uip is connectors list --output json

# Get connector details
uip is connectors get --connector-id salesforce --output json
```

### 3b. Quản lý connections

```bash
# List connections
uip is connections list --output json

# Ping connection (kiểm tra health)
uip is connections ping --connection-id <connection-id> --output json
```

### 3c. Activities và resources

```bash
# List activities của connector
uip is activities list --connector-id salesforce --output json

# List resources
uip is resources list --connector-id salesforce --connection-id <id> --output json

# Describe resource schema
uip is resources describe --connector-id salesforce --connection-id <id> --resource Account --output json

# Execute resource (test)
uip is resources execute --connector-id salesforce --connection-id <id> --resource Account --operation get --output json
```

---

## Phase 4 — Solutions (Multi-project deploy)

```bash
# Tạo solution
uip solution create --name "InvoiceAutomation" --output /path/to/solution

# Thêm project vào solution
uip solution add --solution-path /path/to/solution --project-path /path/to/Dispatcher
uip solution add --solution-path /path/to/solution --project-path /path/to/Performer

# Pack solution
uip solution pack --solution-path /path/to/solution --output /path/to/output

# Publish solution
uip solution publish --package /path/to/InvoiceAutomation.1.0.0.nupkg

# Deploy solution
uip solution deploy --name "InvoiceAutomation" --version "1.0.0"
```

---

## Phase 5 — Test Manager

```bash
# List test projects
uip tm project list --output json

# List test sets
uip tm test-set list --project-id <id> --output json

# Run test set
uip tm test-set execute --project-id <id> --test-set-id <id>

# Get results
uip tm test-execution result list --execution-id <id> --output json

# Generate report
uip tm report create --execution-id <id> --format html --output /path/to/report.html
```

---

## CI/CD Pipeline — Template

```yaml
# Ví dụ pipeline (conceptual — adapt for Azure DevOps / GitHub Actions)

stages:
  - name: Build & Validate
    steps:
      - uip rpa get-errors --project-dir . --use-studio   # Validate XAML
      - python3 .agent/skills/uipath-core/scripts/validate_xaml . --lint  # Lint check

  - name: Pack
    steps:
      - uip rpa pack --project-path . --output ./artifacts --version $VERSION

  - name: Publish to UAT
    steps:
      - uip login  # dùng service account token
      - uip package publish --package ./artifacts/*.nupkg --folder UAT

  - name: Deploy to UAT
    steps:
      - uip orchestrator process update --name "MyProcess" --package-version $VERSION --folder UAT

  - name: Smoke Test
    steps:
      - uip tm test-set execute --project-id $TEST_PROJECT_ID --test-set-id $SMOKE_TEST_ID

  - name: Promote to Production
    condition: manual-approval
    steps:
      - uip orchestrator process update --name "MyProcess" --package-version $VERSION --folder Production
```

---

## Checklist deploy

```markdown
### Pre-deploy
- [ ] `uip rpa get-errors` → 0 errors
- [ ] `validate_xaml --lint` → 0 errors  
- [ ] Version mới (chưa tồn tại trên Orchestrator)
- [ ] Config.xlsx assets được sync với Orchestrator assets
- [ ] Credentials assets đã tạo trên Orchestrator

### Post-deploy
- [ ] Process hiển thị trên Orchestrator với đúng version
- [ ] Robot có thể run process
- [ ] Logs xuất hiện trong Orchestrator → Jobs
- [ ] Smoke test pass
```

---

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `Unauthorized` | Token hết hạn | `uip login` lại |
| `Duplicate version` | Publish cùng version | Bump version trong pack step |
| `Folder not found` | Folder name sai | `uip orchestrator folder list` để kiểm tra |
| `Asset not found` khi robot chạy | Asset tên không khớp | Kiểm tra asset name trong workflow vs Orchestrator |
| `Queue not found` | Queue chưa tạo | `uip orchestrator queue create` |
