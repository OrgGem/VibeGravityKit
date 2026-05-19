---
name: jira-automation
description: "Migrated from grandcamel/jira-assistant-skills: A unified, 14-module enterprise JIRA automation suite. Allows conversational Jira execution covering CRUD, agile, JSM, relationships, and time logs."
requires:
  mcp: []
---

# Unified Jira Enterprise Automation Skill

> **Migration Notice**: This skill is migrated from `grandcamel/jira-assistant-skills` and unified into a single high-performance framework in GravityKit. It enables conversational Jira management via the built-in python client or native requests.

---

## ⚙️ Environment Variables & Configuration

Both the **USER** and the **AI AGENT** can store and load the following variables to connect and execute requests without repeating authorization flags on the command line:

### 1. Variables Definition
| Variable Name | Alternative | Required | Description |
| :--- | :--- | :--- | :--- |
| `JIRA_SITE_URL` | `JIRA_HOST` | **Yes** | Base URL of your Jira instance (e.g. `https://jira.company.com` or `https://org.atlassian.net`) |
| `JIRA_API_TOKEN` | `JIRA_PAT` | **Yes** | Your Personal Access Token (Server/DC) or API Token (Cloud) |
| `JIRA_EMAIL` | - | *Cloud Only* | Account email address associated with the Cloud API Token |

### 2. Storing in Project `.env` File
Create or update a `.env` file in the root of the project (`GravityKit/.env`) with these variables:
```env
# Jira Host / Base URL
JIRA_SITE_URL=https://jira.yourcompany.com

# Personal Access Token (PAT) or Cloud API Token
JIRA_API_TOKEN=your_jira_access_token_here

# Required only if you are using Jira Cloud (instead of self-hosted Server/Data Center)
# JIRA_EMAIL=user@company.com
```

### 3. Setting Environment Variables in Terminal
- **Windows (PowerShell)**:
  ```powershell
  $env:JIRA_SITE_URL="https://jira.yourcompany.com"
  $env:JIRA_API_TOKEN="your_jira_access_token_here"
  ```
- **Windows (CMD)**:
  ```cmd
  set JIRA_SITE_URL=https://jira.yourcompany.com
  set JIRA_API_TOKEN=your_jira_access_token_here
  ```
- **macOS / Linux (Bash/Zsh)**:
  ```bash
  export JIRA_SITE_URL="https://jira.yourcompany.com"
  export JIRA_API_TOKEN="your_jira_access_token_here"
  ```

---

## 1. Architecture Overview (14-Module Blueprint)

This unified skill is organized into 14 functional areas, exposing the full power of Jira's REST API:

1. **`jira-issue`**: Issue CRUD operations (Create, Read, Update, Delete).
2. **`jira-lifecycle`**: Workflow states and transitions (e.g. In Progress, Resolved).
3. **`jira-search`**: Fast JQL query execution and paging.
4. **`jira-collaborate`**: Comments, watchers, and attachments.
5. **`jira-agile`**: Epics, Sprints, Boards, and Backlog management.
6. **`jira-relationships`**: Linking issues, blocking dependencies, and duplicates.
7. **`jira-time`**: Worklogs, logging hours, and time-tracking statistics.
8. **`jira-jsm`**: Jira Service Management queues, customers, and SLAs.
9. **`jira-bulk`**: Multi-issue operations (bulk transition, bulk updating).
10. **`jira-dev`**: Connecting issues to Git commits, branches, and Pull Requests.
11. **`jira-fields`**: Inspecting screens and handling custom field IDs.
12. **`jira-ops`**: High-speed batching and validation checks.
13. **`jira-admin`**: Basic project setup and user administration.
14. **`jira-assistant`**: Unified NLP router for intelligent action execution.

---

## 2. Core Workflows & REST API Payload Reference

### Module 1: `jira-issue` (CRUD)
- **Create Issue**: `POST /rest/api/2/issue`
  ```json
  {
    "fields": {
      "project": { "key": "PROJ" },
      "summary": "Task Summary",
      "description": "Task Description",
      "issuetype": { "name": "Task" }
    }
  }
  ```
- **Update Issue**: `PUT /rest/api/2/issue/{issueKey}`
  ```json
  {
    "fields": {
      "summary": "Updated Summary"
    }
  }
  ```
- **Delete Issue**: `DELETE /rest/api/2/issue/{issueKey}`

### Module 2: `jira-lifecycle` (Workflow Transitions)
- **Get Transitions**: `GET /rest/api/2/issue/{issueKey}/transitions`
- **Apply Transition**: `POST /rest/api/2/issue/{issueKey}/transitions`
  ```json
  {
    "transition": { "id": "31" }
  }
  ```

### Module 3: `jira-search` (JQL Querying)
- **Execute JQL**: `POST /rest/api/2/search`
  ```json
  {
    "jql": "project = PROJ AND status = Open ORDER BY created DESC",
    "startAt": 0,
    "maxResults": 50,
    "fields": ["summary", "status", "assignee", "priority"]
  }
  ```

### Module 4: `jira-collaborate` (Comments & Watchers)
- **Add Comment**: `POST /rest/api/2/issue/{issueKey}/comment`
  ```json
  { "body": "Comment text here." }
  ```
- **Add Watcher**: `POST /rest/api/2/issue/{issueKey}/watchers`
  ```json
  "username_or_account_id"
  ```

### Module 5: `jira-agile` (Sprints, Epics & Boards)
- **List Boards**: `GET /rest/agile/1.0/board`
- **Get Sprints on Board**: `GET /rest/agile/1.0/board/{boardId}/sprint`
- **Get Active Sprint Issues**: `GET /rest/agile/1.0/sprint/{sprintId}/issue`
- **Get Epics on Board**: `GET /rest/agile/1.0/board/{boardId}/epic`
- **Get Backlog**: `GET /rest/agile/1.0/board/{boardId}/backlog`

### Module 6: `jira-relationships` (Linking & Dependencies)
- **Link Issues**: `POST /rest/api/2/issueLink`
  ```json
  {
    "type": { "name": "Blocks" },
    "inwardIssue": { "key": "PROJ-1" },
    "outwardIssue": { "key": "PROJ-2" }
  }
  ```

### Module 7: `jira-time` (Time Tracking)
- **Add Worklog**: `POST /rest/api/2/issue/{issueKey}/worklog`
  ```json
  {
    "timeSpent": "2h 30m",
    "comment": "Implemented OAuth token rotation logic."
  }
  ```
- **Get Worklogs**: `GET /rest/api/2/issue/{issueKey}/worklog`

### Module 8: `jira-jsm` (Jira Service Management)
- **Get Service Desks**: `GET /rest/servicedeskapi/servicedesk`
- **Get Queues**: `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue`
- **Get SLA Details**: `GET /rest/servicedeskapi/request/{issueKey}/sla`

---

## 3. High-Resiliency Implementation Patterns

To match the robust production-ready design of `jira-assistant-skills`, developers should observe the following guidelines:

1. **4-Layer Validation**:
   - **Parameter Validation**: Validate JQL syntax and issue keys locally before dispatching HTTP calls.
   - **State Checking**: Always fetch current ticket status or transition lists before invoking state migrations.
   - **API Schema Parsing**: Gracefully parse API differences between self-hosted Server/Data Center and Jira Cloud.
   - **User Friendly Feedback**: Translate obscure JSON errors (e.g. `Field 'customfield_10100' is required`) into plain human advice.

2. **Rate Limits & Backoff**:
   - If Jira triggers `429 Too Many Requests`, catch the exception and pause using exponential backoff with jitter:
     $$T_{\text{wait}} = 2^{\text{attempt}} + \text{random\_ms}$$

3. **Field Resolving**:
   - Resolve display priority names (e.g. "Highest", "Medium") or custom fields dynamically using project createmeta endpoints.
