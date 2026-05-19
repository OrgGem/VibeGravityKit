<#
.SYNOPSIS
    Outlook Windows Automation CLI tool in PowerShell.
    Allows sending, reading, and replying to Outlook emails.
.EXAMPLE
    .\outlook_client.ps1 -Action Send -To "recipient@example.com" -Subject "PowerShell Alert" -Body "This is from PowerShell Outlook COM"
.EXAMPLE
    .\outlook_client.ps1 -Action Read -Limit 5
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("Send", "Read", "Reply")]
    [string]$Action,

    # Send / Reply params
    [string]$To,
    [string]$Subject,
    [string]$Body,
    [string[]]$Attachments,
    [switch]$IsHtml,
    [switch]$Draft,

    # Read params
    [int]$Limit = 10,
    [switch]$UnreadOnly,
    [string]$SearchSubject,

    # Reply params
    [string]$SearchSubjectToReply,
    [switch]$ReplyAll
)

# Set UTF8 encoding for standard output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Check if Outlook COM is available
function Get-OutlookObject {
    try {
        $outlook = New-Object -ComObject Outlook.Application
        return $outlook
    }
    catch {
        Write-Error "Failed to connect to Microsoft Outlook COM interface. Make sure Outlook is installed and running."
        exit 1
    }
}

switch ($Action) {
    "Send" {
        if (-not $To -or -not $Subject -or -not $Body) {
            Write-Error "Parameters -To, -Subject, and -Body are mandatory for 'Send' action."
            exit 1
        }
        
        $outlook = Get-OutlookObject
        $mail = $outlook.CreateItem(0) # 0 = olMailItem
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
                    $absPath = (Resolve-Path $file).Path
                    $mail.Attachments.Add($absPath) | Out-Null
                    Write-Host "[*] Attached: $absPath"
                } else {
                    Write-Warning "Attachment not found: $file"
                }
            }
        }
        
        if ($Draft) {
            $mail.Save()
            $response = @{ status = "success"; action = "draft_saved" }
        } else {
            $mail.Send()
            $response = @{ status = "success"; action = "sent" }
        }
        
        Write-Output ($response | ConvertTo-Json -Depth 5)
    }

    "Read" {
        $outlook = Get-OutlookObject
        $namespace = $outlook.GetNamespace("MAPI")
        $inbox = $namespace.GetDefaultFolder(6) # 6 = olFolderInbox
        $items = $inbox.Items
        $items.Sort("[ReceivedTime]", $true)
        
        $filters = @()
        if ($UnreadOnly) {
            $filters += "[Unread] = True"
        }
        if ($SearchSubject) {
            $filters += "@SQL=`"urn:schemas:httpmail:subject`" LIKE '%$SearchSubject%'"
        }
        
        if ($filters.Count -gt 0) {
            $filterQuery = $filters -join " AND "
            $items = $items.Restrict($filterQuery)
        }
        
        $count = [Math]::Min($Limit, $items.Count)
        $emails = @()
        
        for ($i = 1; $i -le $count; $i++) {
            try {
                $msg = $items.Item($i)
                $bodyPreview = ""
                if ($msg.Body) {
                    $bodyPreview = $msg.Body
                    if ($bodyPreview.Length -gt 300) {
                        $bodyPreview = $bodyPreview.Substring(0, 300) + "..."
                    }
                }
                
                $emails += @{
                    index        = $i
                    subject      = $msg.Subject
                    sender       = $msg.SenderName
                    sender_email = $msg.SenderEmailAddress
                    received     = $msg.ReceivedTime.ToString("yyyy-MM-dd HH:mm:ss")
                    unread       = $msg.UnRead
                    preview      = $bodyPreview
                }
            }
            catch {
                # Skip errors for non-message items (e.g. meeting invitations)
                continue
            }
        }
        
        $response = @{
            status = "success"
            count  = $emails.Count
            emails = $emails
        }
        
        Write-Output ($response | ConvertTo-Json -Depth 5)
    }

    "Reply" {
        if (-not $SearchSubjectToReply -or -not $Body) {
            Write-Error "Parameters -SearchSubjectToReply and -Body are mandatory for 'Reply' action."
            exit 1
        }
        
        $outlook = Get-OutlookObject
        $namespace = $outlook.GetNamespace("MAPI")
        $inbox = $namespace.GetDefaultFolder(6)
        $items = $inbox.Items
        
        $filterQuery = "@SQL=`"urn:schemas:httpmail:subject`" LIKE '%$SearchSubjectToReply%'"
        $matching = $items.Restrict($filterQuery)
        $matching.Sort("[ReceivedTime]", $true)
        
        if ($matching.Count -eq 0) {
            $response = @{ status = "error"; message = "No emails found matching subject '$SearchSubjectToReply'" }
            Write-Output ($response | ConvertTo-Json -Depth 5)
            exit 1
        }
        
        $targetMsg = $matching.Item(1) # Get latest one
        
        if ($ReplyAll) {
            $reply = $targetMsg.ReplyAll()
        } else {
            $reply = $targetMsg.Reply()
        }
        
        $reply.HTMLBody = "<p>$Body</p>" + $reply.HTMLBody
        $reply.Send()
        
        $response = @{
            status = "success"
            action = "replied"
            thread = $targetMsg.Subject
        }
        
        Write-Output ($response | ConvertTo-Json -Depth 5)
    }
}
