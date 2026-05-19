#!/usr/bin/env python3
"""
Outlook COM Automation Client for Windows.
Provides capabilities to send, search, read, and reply to emails using pywin32.
"""

import sys
import os
import argparse
import json

try:
    import win32com.client
    import pythoncom
except ImportError:
    print("[!] Error: 'pywin32' is not installed. Please run: pip install pywin32", file=sys.stderr)
    sys.exit(1)


class OutlookClient:
    def __init__(self):
        try:
            # Initialize COM libraries for current thread
            pythoncom.CoInitialize()
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
        except Exception as e:
            print(f"[!] Critical Error initializing Outlook COM: {e}", file=sys.stderr)
            sys.exit(1)

    def send_email(self, to, subject, body, attachments=None, is_html=True, draft=False):
        """Send or save email as draft."""
        try:
            # 0 = olMailItem
            mail = self.outlook.CreateItem(0)
            mail.To = to
            mail.Subject = subject

            if is_html:
                mail.HTMLBody = body
            else:
                mail.Body = body

            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment):
                        abs_path = os.path.abspath(attachment)
                        mail.Attachments.Add(Source=abs_path)
                        print(f"[*] Attached: {abs_path}")
                    else:
                        print(f"[!] Warning: Attachment not found at {attachment}", file=sys.stderr)

            if draft:
                mail.Save()
                print("[+] Email saved to Drafts.")
                return {"status": "success", "action": "draft_saved"}
            else:
                mail.Send()
                print("[+] Email sent successfully.")
                return {"status": "success", "action": "sent"}

        except Exception as e:
            print(f"[!] Error sending email: {e}", file=sys.stderr)
            return {"status": "error", "message": str(e)}

    def read_inbox(self, limit=10, unread_only=False, search_subject=None):
        """Read latest emails from inbox."""
        try:
            # 6 = olFolderInbox
            inbox = self.namespace.GetDefaultFolder(6)
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)

            filters = []
            if unread_only:
                filters.append("[Unread] = True")
            if search_subject:
                filters.append(f"@SQL=\"urn:schemas:httpmail:subject\" LIKE '%{search_subject}%'")

            if filters:
                filter_query = " AND ".join(filters)
                messages = messages.Restrict(filter_query)

            count = min(limit, len(messages))
            emails = []

            for i in range(1, count + 1):
                try:
                    msg = messages.Item(i)
                    emails.append({
                        "index": i,
                        "subject": msg.Subject,
                        "sender": msg.SenderName,
                        "sender_email": msg.SenderEmailAddress,
                        "received_time": str(msg.ReceivedTime),
                        "unread": msg.UnRead,
                        "body_preview": msg.Body[:300] if msg.Body else ""
                    })
                except Exception as ex:
                    continue

            return {"status": "success", "count": len(emails), "emails": emails}

        except Exception as e:
            print(f"[!] Error reading inbox: {e}", file=sys.stderr)
            return {"status": "error", "message": str(e)}

    def reply_to_email(self, search_subject, reply_body, reply_all=False):
        """Reply to the latest email matching search_subject."""
        try:
            inbox = self.namespace.GetDefaultFolder(6)
            filter_query = f"@SQL=\"urn:schemas:httpmail:subject\" LIKE '%{search_subject}%'"
            items = inbox.Items.Restrict(filter_query)
            items.Sort("[ReceivedTime]", True)

            if len(items) == 0:
                print(f"[!] No emails found matching subject: {search_subject}", file=sys.stderr)
                return {"status": "error", "message": "Email not found"}

            target_msg = items.Item(1)  # Get the latest matching email
            
            if reply_all:
                reply = target_msg.ReplyAll()
            else:
                reply = target_msg.Reply()

            reply.HTMLBody = f"<p>{reply_body}</p>" + reply.HTMLBody
            reply.Send()

            print(f"[+] Replied successfully to: {target_msg.Subject}")
            return {"status": "success", "action": "replied", "thread": target_msg.Subject}

        except Exception as e:
            print(f"[!] Error replying to email: {e}", file=sys.stderr)
            return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Outlook Automation Client for Windows")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send a new email")
    send_parser.add_argument("--to", required=True, help="Recipient email address")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--html", action="store_true", help="Send as HTML email")
    send_parser.add_argument("--draft", action="store_true", help="Save as draft instead of sending")
    send_parser.add_argument("--attach", nargs="*", help="Filepaths to attach")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read inbox emails")
    read_parser.add_argument("--limit", type=int, default=10, help="Max emails to retrieve")
    read_parser.add_argument("--unread", action="store_true", help="Only show unread emails")
    read_parser.add_argument("--search", help="Search subject term")

    # Reply command
    reply_parser = subparsers.add_parser("reply", help="Reply to an email")
    reply_parser.add_argument("--search-subject", required=True, help="Subject of the email to reply to")
    reply_parser.add_argument("--body", required=True, help="Reply body text/HTML")
    reply_parser.add_argument("--all", action="store_true", help="Reply to all recipients")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = OutlookClient()

    if args.command == "send":
        result = client.send_email(
            to=args.to,
            subject=args.subject,
            body=args.body,
            attachments=args.attach,
            is_html=args.html,
            draft=args.draft
        )
        print(json.dumps(result, indent=2))

    elif args.command == "read":
        result = client.read_inbox(
            limit=args.limit,
            unread_only=args.unread,
            search_subject=args.search
        )
        print(json.dumps(result, indent=2))

    elif args.command == "reply":
        result = client.reply_to_email(
            search_subject=args.search_subject,
            reply_body=args.body,
            reply_all=args.all
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
