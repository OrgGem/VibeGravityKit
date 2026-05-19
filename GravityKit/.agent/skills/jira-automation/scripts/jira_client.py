#!/usr/bin/env python3
"""
Migrated from grandcamel/jira-assistant-skills.
Unified Jira REST API CLI Client supporting CRUD, Agile (sprints, boards, epics, backlogs),
Time tracking (worklogs), JSM (queues, service desks), and Relationship Linking.
"""

import sys
import os
import argparse
import json
import base64

try:
    import requests
    # Try importing from standard urllib3 first (highly recommended for IDE resolution)
    try:
        import urllib3
        from urllib3.exceptions import InsecureRequestWarning
    except ImportError:
        # Fallback to requests vendorized namespace
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        urllib3 = None
except ImportError:
    print("[!] Error: 'requests' library is not installed. Please run: pip install requests", file=sys.stderr)
    sys.exit(1)


class JiraClient:
    def __init__(self, base_url, token, email=None, verify_ssl=True):
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Authentication Strategy
        if email:
            # Jira Cloud Basic Auth (Email + API Token)
            auth_str = f"{email}:{token}"
            encoded_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
            self.headers["Authorization"] = f"Basic {encoded_auth}"
            print("[*] Auth Mode: Jira Cloud (Basic Authentication)")
        else:
            # Jira Server / Data Center Bearer Token (PAT)
            self.headers["Authorization"] = f"Bearer {token}"
            print("[*] Auth Mode: Jira Server/Data Center (Personal Access Token - PAT)")

        if not verify_ssl:
            # Disable warnings for self-signed certificates
            if urllib3:
                urllib3.disable_warnings(InsecureRequestWarning)
            else:
                requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            print("[!] Warning: SSL Certificate Verification is DISABLED.")

    def _request(self, method, endpoint, data=None, files=None, custom_headers=None):
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, verify=self.verify_ssl)
            elif method.upper() == "POST":
                if files:
                    headers.pop("Content-Type", None)
                    response = requests.post(url, headers=headers, files=files, verify=self.verify_ssl)
                else:
                    response = requests.post(url, headers=headers, json=data, verify=self.verify_ssl)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, verify=self.verify_ssl)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, verify=self.verify_ssl)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Standard responses parsing
            if response.status_code in [200, 201, 204]:
                if response.status_code == 204 or not response.text:
                    return {"status": "success", "status_code": response.status_code}
                try:
                    return response.json()
                except ValueError:
                    return {"status": "success", "data": response.text}
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ==========================================
    # 1. CORE CRUD & TRANSITIONS (jira-issue, jira-lifecycle)
    # ==========================================
    def check_connection(self):
        return self._request("GET", "/rest/api/2/myself")

    def search_issues(self, jql, limit=10, fields=None):
        if not fields:
            fields = ["summary", "status", "assignee", "priority", "created"]
        payload = {
            "jql": jql,
            "maxResults": limit,
            "fields": fields
        }
        return self._request("POST", "/rest/api/2/search", data=payload)

    def create_issue(self, project, summary, description, issue_type="Task", priority="Medium"):
        payload = {
            "fields": {
                "project": {"key": project},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
        }
        return self._request("POST", "/rest/api/2/issue", data=payload)

    def update_issue(self, issue_key, summary=None, description=None):
        fields = {}
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = description
        
        payload = {"fields": fields}
        return self._request("PUT", f"/rest/api/2/issue/{issue_key}", data=payload)

    def delete_issue(self, issue_key):
        return self._request("DELETE", f"/rest/api/2/issue/{issue_key}")

    def get_transitions(self, issue_key):
        return self._request("GET", f"/rest/api/2/issue/{issue_key}/transitions")

    def transition_issue(self, issue_key, transition_id):
        payload = {
            "transition": {
                "id": str(transition_id)
            }
        }
        return self._request("POST", f"/rest/api/2/issue/{issue_key}/transitions", data=payload)

    # ==========================================
    # 2. COLLABORATION (jira-collaborate)
    # ==========================================
    def add_comment(self, issue_key, body):
        payload = {"body": body}
        return self._request("POST", f"/rest/api/2/issue/{issue_key}/comment", data=payload)

    def add_watcher(self, issue_key, watcher_id):
        return self._request("POST", f"/rest/api/2/issue/{issue_key}/watchers", data=watcher_id)

    def get_watchers(self, issue_key):
        return self._request("GET", f"/rest/api/2/issue/{issue_key}/watchers")

    def attach_file(self, issue_key, file_path):
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found at: {file_path}"}
        filename = os.path.basename(file_path)
        try:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                custom_headers = {"X-Atlassian-Token": "no-check"}
                return self._request("POST", f"/rest/api/2/issue/{issue_key}/attachments", files=files, custom_headers=custom_headers)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ==========================================
    # 3. AGILE MANAGEMENT (jira-agile)
    # ==========================================
    def list_boards(self):
        return self._request("GET", "/rest/agile/1.0/board")

    def list_board_sprints(self, board_id):
        return self._request("GET", f"/rest/agile/1.0/board/{board_id}/sprint")

    def list_board_epics(self, board_id):
        return self._request("GET", f"/rest/agile/1.0/board/{board_id}/epic")

    def get_sprint_issues(self, sprint_id):
        return self._request("GET", f"/rest/agile/1.0/sprint/{sprint_id}/issue")

    def get_board_backlog(self, board_id):
        return self._request("GET", f"/rest/agile/1.0/board/{board_id}/backlog")

    # ==========================================
    # 4. RELATIONSHIP LINKING (jira-relationships)
    # ==========================================
    def link_issues(self, inward_key, outward_key, link_type="Blocks"):
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        return self._request("POST", "/rest/api/2/issueLink", data=payload)

    # ==========================================
    # 5. TIME TRACKING (jira-time)
    # ==========================================
    def add_worklog(self, issue_key, time_spent, comment=None):
        payload = {"timeSpent": time_spent}
        if comment:
            payload["comment"] = comment
        return self._request("POST", f"/rest/api/2/issue/{issue_key}/worklog", data=payload)

    def get_worklogs(self, issue_key):
        return self._request("GET", f"/rest/api/2/issue/{issue_key}/worklog")

    # ==========================================
    # 6. SERVICE MANAGEMENT (jira-jsm)
    # ==========================================
    def list_service_desks(self):
        return self._request("GET", "/rest/servicedeskapi/servicedesk")

    def list_jsm_queues(self, servicedesk_id):
        return self._request("GET", f"/rest/servicedeskapi/servicedesk/{servicedesk_id}/queue")


def main():
    parser = argparse.ArgumentParser(description="Unified JIRA REST API Client - Migrated from grandcamel/jira-assistant-skills")
    
    # Auth configuration fallbacks to env vars
    default_host = os.environ.get("JIRA_SITE_URL") or os.environ.get("JIRA_HOST")
    default_token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_PAT")
    default_email = os.environ.get("JIRA_EMAIL")

    parser.add_argument("--host", default=default_host, required=not default_host, help="Jira base URL (e.g. https://jira.company.com or https://org.atlassian.net)")
    parser.add_argument("--token", default=default_token, required=not default_token, help="Personal Access Token (PAT) or Cloud API Token")
    parser.add_argument("--email", default=default_email, help="Account Email (Required only for Jira Cloud)")
    parser.add_argument("--no-verify", action="store_true", help="Disable SSL certificate verification")

    subparsers = parser.add_subparsers(dest="command", help="Command category")

    # Core Connection Check
    subparsers.add_parser("connect", help="Validate credentials and fetch user profile")

    # Issue Commands
    issue_parser = subparsers.add_parser("issue", help="Create, update, read, or delete tickets")
    issue_sub = issue_parser.add_subparsers(dest="action", help="CRUD Action")
    
    get_parser = issue_sub.add_parser("get", help="Get ticket details")
    get_parser.add_argument("key", help="Issue Key (e.g. PROJ-123)")

    create_parser = issue_sub.add_parser("create", help="Create a ticket")
    create_parser.add_argument("--project", required=True, help="Project Key")
    create_parser.add_argument("--summary", required=True, help="Summary title")
    create_parser.add_argument("--desc", required=True, help="Description details")
    create_parser.add_argument("--type", default="Task", help="Issue Type")
    create_parser.add_argument("--priority", default="Medium", help="Priority")

    update_parser = issue_sub.add_parser("update", help="Update ticket fields")
    update_parser.add_argument("key", help="Issue Key")
    update_parser.add_argument("--summary", help="New summary")
    update_parser.add_argument("--desc", help="New description")

    delete_parser = issue_sub.add_parser("delete", help="Delete a ticket")
    delete_parser.add_argument("key", help="Issue Key")

    # Transitions (Lifecycle) Commands
    lifecycle_parser = subparsers.add_parser("lifecycle", help="Manage ticket transitions and workflow")
    lifecycle_sub = lifecycle_parser.add_subparsers(dest="action", help="Lifecycle Actions")
    
    trans_list_parser = lifecycle_sub.add_parser("list", help="List available transitions")
    trans_list_parser.add_argument("key", help="Issue Key")
    
    trans_apply_parser = lifecycle_sub.add_parser("apply", help="Transition status")
    trans_apply_parser.add_argument("key", help="Issue Key")
    trans_apply_parser.add_argument("id", help="Transition ID")

    # Search Commands
    search_parser = subparsers.add_parser("search", help="Execute queries")
    search_parser.add_argument("--jql", required=True, help="JQL query string")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results limit")

    # Collaboration Commands
    collab_parser = subparsers.add_parser("collaborate", help="Comments, Watchers, and Attachments")
    collab_sub = collab_parser.add_subparsers(dest="action", help="Collaboration action")
    
    comment_parser = collab_sub.add_parser("comment", help="Add a comment")
    comment_parser.add_argument("key", help="Issue Key")
    comment_parser.add_argument("body", help="Comment text")

    watcher_parser = collab_sub.add_parser("watch", help="Add a watcher")
    watcher_parser.add_argument("key", help="Issue key")
    watcher_parser.add_argument("user", help="Username or AccountID")

    watcher_get_parser = collab_sub.add_parser("watchers", help="Get list of watchers")
    watcher_get_parser.add_argument("key", help="Issue key")

    attach_parser = collab_sub.add_parser("attach", help="Attach a file")
    attach_parser.add_argument("key", help="Issue key")
    attach_parser.add_argument("file", help="Local file path")

    # Agile Commands
    agile_parser = subparsers.add_parser("agile", help="Boards, Sprints, Epics, and Backlogs")
    agile_sub = agile_parser.add_subparsers(dest="action", help="Agile action")
    
    agile_sub.add_parser("boards", help="List all Agile boards")
    
    sprint_list_parser = agile_sub.add_parser("sprints", help="List sprints on a board")
    sprint_list_parser.add_argument("board_id", help="Board ID")
    
    epic_list_parser = agile_sub.add_parser("epics", help="List epics on a board")
    epic_list_parser.add_argument("board_id", help="Board ID")

    sprint_issues_parser = agile_sub.add_parser("sprint-issues", help="Get issues inside a specific sprint")
    sprint_issues_parser.add_argument("sprint_id", help="Sprint ID")

    backlog_parser = agile_sub.add_parser("backlog", help="Get backlog issues of a board")
    backlog_parser.add_argument("board_id", help="Board ID")

    # Relationships (Link) Commands
    link_parser = subparsers.add_parser("link", help="Create relationships between tickets")
    link_parser.add_argument("inward", help="Inward Issue Key (e.g. PROJ-1)")
    link_parser.add_argument("outward", help="Outward Issue Key (e.g. PROJ-2)")
    link_parser.add_argument("--type", default="Blocks", help="Link Relationship Type (e.g. Blocks, Duplicates, Relates)")

    # Time Tracking Commands
    time_parser = subparsers.add_parser("time", help="Worklogs and time logging")
    time_sub = time_parser.add_subparsers(dest="action", help="Time action")
    
    log_parser = time_sub.add_parser("log", help="Log spent hours")
    log_parser.add_argument("key", help="Issue Key")
    log_parser.add_argument("spent", help="Time spent (e.g. 2h 30m, 45m)")
    log_parser.add_argument("--comment", help="Worklog description")

    get_logs_parser = time_sub.add_parser("worklogs", help="Get all worklogs of an issue")
    get_logs_parser.add_argument("key", help="Issue Key")

    # JSM Service Management Commands
    jsm_parser = subparsers.add_parser("jsm", help="Jira Service Management Queues and SLA")
    jsm_sub = jsm_parser.add_subparsers(dest="action", help="JSM action")
    
    jsm_sub.add_parser("desks", help="List all Service Desks")
    
    queues_parser = jsm_sub.add_parser("queues", help="List Queues of a Service Desk")
    queues_parser.add_argument("desk_id", help="Service Desk ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    verify_ssl = not args.no_verify
    client = JiraClient(
        base_url=args.host,
        token=args.token,
        email=args.email,
        verify_ssl=verify_ssl
    )

    res = None

    if args.command == "connect":
        res = client.check_connection()

    elif args.command == "issue":
        if not args.action:
            issue_parser.print_help()
            sys.exit(1)
        if args.action == "get":
            res = client.search_issues(jql=f"key = '{args.key}'", limit=1)
        elif args.action == "create":
            res = client.create_issue(
                project=args.project,
                summary=args.summary,
                description=args.desc,
                issue_type=args.type,
                priority=args.priority
            )
        elif args.action == "update":
            res = client.update_issue(args.key, args.summary, args.desc)
        elif args.action == "delete":
            res = client.delete_issue(args.key)

    elif args.command == "lifecycle":
        if not args.action:
            lifecycle_parser.print_help()
            sys.exit(1)
        if args.action == "list":
            res = client.get_transitions(args.key)
        elif args.action == "apply":
            res = client.transition_issue(args.key, args.id)

    elif args.command == "search":
        res = client.search_issues(jql=args.jql, limit=args.limit)

    elif args.command == "collaborate":
        if not args.action:
            collab_parser.print_help()
            sys.exit(1)
        if args.action == "comment":
            res = client.add_comment(args.key, args.body)
        elif args.action == "watch":
            res = client.add_watcher(args.key, args.user)
        elif args.action == "watchers":
            res = client.get_watchers(args.key)
        elif args.action == "attach":
            res = client.attach_file(args.key, args.file)

    elif args.command == "agile":
        if not args.action:
            agile_parser.print_help()
            sys.exit(1)
        if args.action == "boards":
            res = client.list_boards()
        elif args.action == "sprints":
            res = client.list_board_sprints(args.board_id)
        elif args.action == "epics":
            res = client.list_board_epics(args.board_id)
        elif args.action == "sprint-issues":
            res = client.get_sprint_issues(args.sprint_id)
        elif args.action == "backlog":
            res = client.get_board_backlog(args.board_id)

    elif args.command == "link":
        res = client.link_issues(args.inward, args.outward, args.type)

    elif args.command == "time":
        if not args.action:
            time_parser.print_help()
            sys.exit(1)
        if args.action == "log":
            res = client.add_worklog(args.key, args.spent, args.comment)
        elif args.action == "worklogs":
            res = client.get_worklogs(args.key)

    elif args.command == "jsm":
        if not args.action:
            jsm_parser.print_help()
            sys.exit(1)
        if args.action == "desks":
            res = client.list_service_desks()
        elif args.action == "queues":
            res = client.list_jsm_queues(args.desk_id)

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
