---
name: outlook-automation
description: "Automate Microsoft Outlook on Windows (Desktop App): send/reply, search, read emails, and manage folders via Python pywin32 or PowerShell COM interface."
requires:
  os: [windows]
---

# Microsoft Outlook Windows Automation

Automate Microsoft Outlook desktop client operations directly on Windows using COM (Component Object Model) interface via Python (`pywin32`) or native Windows PowerShell.

## Prerequisites

- **Operating System**: Windows OS
- **Application**: Microsoft Outlook Desktop Application installed and configured with at least one active mail account.
- **Python Setup** (for Python workflow):
  ```bash
  pip install pywin32
  ```
- **PowerShell Setup** (for PowerShell workflow): Built-in out of the box, no external module dependencies.

---

## Core Workflows

### 1. Send a New Email

**When to use**: Automating notification emails, sending reports, or forwarding files as attachments via Outlook.

#### Python (pywin32) Pattern:
```python
import win32com.client
import os

def send_outlook_email(to_email, subject, body, attachments=None, is_html=True):
    try:
        # Initialize Outlook COM Application
        outlook = win32com.client.Dispatch("Outlook.Application")
        
        # Create a new mail item (0 = olMailItem)
        mail = outlook.CreateItem(0)
        mail.To = to_email
        mail.Subject = subject
        
        # Set body format
        if is_html:
            mail.HTMLBody = body
        else:
            mail.Body = body
            
        # Add attachments if any
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    mail.Attachments.Add(Source=os.path.abspath(filepath))
                else:
                    print(f"Warning: Attachment not found at {filepath}")
        
        # Send email (use mail.Save() to save as draft instead)
        mail.Send()
        print("[OK] Email sent successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
```

#### PowerShell (COM) Pattern:
```powershell
function Send-OutlookEmail {
    param (
        [string]$To,
        [string]$Subject,
        [string]$Body,
        [string[]]$Attachments,
        [bool]$IsHtml = $true
    )
    
    try {
        $outlook = New-Object -ComObject Outlook.Application
        $mail = $outlook.CreateItem(0)
        $mail.To = $To
        $mail.Subject = $Subject
        
        if ($IsHtml) {
            $mail.HTMLBody = $Body
        } else {
            $mail.Body = $Body
        }
        
        if ($Attachments) {
            foreach ($file in $Attachments) {
                if (Test-Path $file) {
                    $absPath = Resolve-Path $file
                    $mail.Attachments.Add($absPath.Path) | Out-Null
                }
            }
        }
        
        $mail.Send()
        Write-Output "[OK] Email sent successfully."
    }
    catch {
        Write-Warning "Error sending email: $_"
    }
}
```

---

### 2. Read and Search Emails

**When to use**: Fetching incoming emails, searching for specific subjects/senders, or processing invoice emails.

#### Python (pywin32) Pattern:
```python
import win32com.client

def read_inbox_emails(limit=10, search_query=None):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        
        # 6 = olFolderInbox
        inbox = namespace.GetDefaultFolder(6)
        messages = inbox.Items
        
        # Sort messages by received time descending
        messages.Sort("[ReceivedTime]", True)
        
        # Filter if a search query is provided
        if search_query:
            # DASL query syntax is extremely fast
            # Example search_query: "@SQL=\"urn:schemas:httpmail:subject\" LIKE '%Invoice%'"
            messages = messages.Restrict(search_query)
            
        print(f"Processing top {limit} emails...")
        emails_list = []
        
        for i in range(1, min(limit, len(messages)) + 1):
            try:
                msg = messages.Item(i)
                emails_list.append({
                    "Subject": msg.Subject,
                    "Sender": msg.SenderName,
                    "SenderEmail": msg.SenderEmailAddress,
                    "ReceivedTime": str(msg.ReceivedTime),
                    "Body": msg.Body[:200] + "..." if msg.Body else "",
                    "Unread": msg.UnRead
                })
            except Exception:
                continue
                
        return emails_list
    except Exception as e:
        print(f"[ERROR] Failed to read emails: {e}")
        return []
```

#### PowerShell (COM) Pattern:
```powershell
function Get-OutlookInbox {
    param (
        [int]$Limit = 10,
        [string]$Filter = ""
    )
    
    try {
        $outlook = New-Object -ComObject Outlook.Application
        $namespace = $outlook.GetNamespace("MAPI")
        $inbox = $namespace.GetDefaultFolder(6) # olFolderInbox
        $items = $inbox.Items
        $items.Sort("[ReceivedTime]", $true)
        
        if ($Filter) {
            $items = $items.Restrict($Filter)
        }
        
        $count = [Math]::Min($Limit, $items.Count)
        $emails = @()
        
        for ($i = 1; $i -le $count; $i++) {
            $msg = $items.Item($i)
            $emails += [PSCustomObject]@{
                Subject      = $msg.Subject
                Sender       = $msg.SenderName
                SenderEmail  = $msg.SenderEmailAddress
                ReceivedTime = $msg.ReceivedTime
                Unread       = $msg.UnRead
            }
        }
        return $emails
    }
    catch {
        Write-Warning "Error reading inbox: $_"
        return @()
    }
}
```

---

### 3. Reply or Forward to a Thread

**When to use**: Automatically replying to standard requests or forwarding alerts to team members.

#### Python (pywin32) Pattern:
```python
import win32com.client

def reply_to_latest_email(search_subject, reply_body):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        inbox = namespace.GetDefaultFolder(6)
        
        # Search for target email
        filter_str = f"@SQL=\"urn:schemas:httpmail:subject\" LIKE '%{search_subject}%'"
        items = inbox.Items.Restrict(filter_str)
        items.Sort("[ReceivedTime]", True)
        
        if len(items) == 0:
            print(f"No emails found matching subject: {search_subject}")
            return False
            
        target_msg = items.Item(1) # Get the latest one
        
        # Create a Reply (or .Forward() to forward)
        reply = target_msg.Reply()
        
        # Add reply body before existing email content
        reply.HTMLBody = f"<p>{reply_body}</p>" + reply.HTMLBody
        reply.Send()
        
        print(f"[OK] Replied to thread: {target_msg.Subject}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to reply: {e}")
        return False
```

---

## Folder Navigation Constants

When using the `GetDefaultFolder(FolderType)` interface, use the following standard integers to access specific folders:

| Folder Type | Integer Value |
|-------------|---------------|
| `olFolderDeletedItems` | 3 |
| `olFolderOutbox` | 4 |
| `olFolderSentMail` | 5 |
| `olFolderInbox` | 6 |
| `olFolderCalendar` | 9 |
| `olFolderContacts` | 10 |
| `olFolderDrafts` | 16 |
| `olFolderJunk` | 23 |

---

## Known Pitfalls & Security Notes

1. **Security Guard Dialog**:
   - If Outlook is configured under a tight corporate policy, attempting to read `SenderEmailAddress` or sending bulk emails via COM might trigger a security prompt: *"A program is trying to access email address information..."*.
   - **Fix**: Run scripts on a machine with a trusted, updated antivirus program installed, or configure the programmatic access settings in Outlook (`File -> Options -> Trust Center -> Trust Center Settings -> Programmatic Access`).

2. **Outlook Must Be running/Configured**:
   - The COM interface directly interacts with the local Outlook client process. If Outlook has never been configured on the PC, or is running with a different privilege level (e.g., Administrator vs standard User), COM instantiation may fail.
   - **Best Practice**: Always make sure Outlook is launched and logged in before running automated background scripts.

3. **Background Hangs**:
   - If you instantiate `Outlook.Application` in a script, it launches a background process. If your script crashes without properly releasing the object or exiting, you may find zombie `OUTLOOK.EXE` processes in Task Manager.
   - **Fix**: Under Python, ensure clean exit. In PowerShell, garbage collect or kill the process if orphaned:
     ```powershell
     [System.Runtime.InteropServices.Marshal]::ReleaseComObject($outlook)
     [GC]::Collect()
     [GC]::WaitForPendingFinalizers()
     ```
