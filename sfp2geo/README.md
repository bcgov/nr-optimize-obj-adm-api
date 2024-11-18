# Archive Script README

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
  - [1. ArchiveConfig.json](#1-archiveconfigjson)
  - [2. SourceFolders.csv](#2-sourcefolderscsv)
- [Running the Script](#running-the-script)
- [Logging](#logging)
  - [1. Console and Log File Output](#1-console-and-log-file-output)
  - [2. GeoDrive Audit Log](#2-geodrive-audit-log)
  - [3. Per-Directory Logs](#3-per-directory-logs)
- [Error Handling](#error-handling)
- [Email Notifications](#email-notifications)
- [Conclusion](#conclusion)

---

## Introduction

This script automates the archival of files that have not been accessed for a specified number of days. It moves these files from their original locations to a designated archive location while preserving the directory structure. The script is configurable, allowing you to specify source directories, exclusion patterns, email notifications, and logging options.

---

## Features

- **Configurable File Age Threshold**: Archives files not accessed for a specified number of days.
- **Directory Structure Preservation**: Maintains the original directory structure in the archive location.
- **Exclusion Patterns**: Supports wildcard patterns to exclude specific files from being archived.
- **Breadcrumbs**: Generates logs in each source directory listing the archived files.
- **Audit Logging**: Records all file operations in a central audit log.
- **Email Notifications**: Sends email reports and error notifications to administrators.
- **Logging to File**: All console output is logged to a file for auditing and troubleshooting.
- **Robust Error Handling**: Handles exceptions and retries operations where applicable.

---

## Prerequisites

- **Operating System**: Windows
- **PowerShell**: Version 5.0 or higher
- **Robocopy**: Should be available (built into Windows)
- **SMTP Server**: For email notifications (if enabled)
- **Permissions**: The user running the script must have read/write permissions on source and destination directories and permission to send emails via the SMTP server.

---

## Configuration

The script requires two configuration files:

1. **ArchiveConfig.json**: Contains global settings.
2. **SourceFolders.csv**: Lists the source directories to process and associated business contact emails.

### 1. ArchiveConfig.json

This JSON file contains the global configuration settings for the script.

**Sample `ArchiveConfig.json`:**

<pre><code>{
    "DestinationPath": "C:\\Archive",
    "AdminEmail": "admin@example.com",
    "EnableEmailNotifications": true,
    "PerDirectoryLogFileName": "ArchiveInfo.csv",
    "GeoDriveAuditLogPath": "C:\\Logs\\Archive_log.csv",
    "FileAgeInDays": 1825,
    "ExcludePatterns": ["*_HR*", "*.tmp"],
    "EmailSettings": {
        "SmtpServer": "smtp.nrs.gov.bc.ca",
        "From": "noreply@example.com",
        "Subject": "Archive Script Report"
    },
    "LogFilePath": "C:\\Logs\\ArchiveScriptOutput.log"
}
</code></pre>

**Configuration Parameters:**

- **DestinationPath**: The root directory where archived files will be stored.
- **AdminEmail**: Email address of the administrator to receive notifications.
- **EnableEmailNotifications**: Set to `true` to enable email notifications, `false` to disable.
- **PerDirectoryLogFileName**: Name of the per-directory log file generated in each source directory.
- **GeoDriveAuditLogPath**: Path to the central audit log file.
- **FileAgeInDays**: Number of days to determine if a file is old enough to archive (e.g., 1825 days for 5 years).
- **ExcludePatterns**: Array of wildcard patterns for files to exclude from archiving.
- **EmailSettings**:
  - **SmtpServer**: Address of the SMTP server used for sending emails.
  - **From**: Email address from which notifications will be sent.
  - **Subject**: Subject line for the email notifications.
- **LogFilePath**: Path to the log file where all console output will be recorded.

### 2. SourceFolders.csv

This CSV file lists the source directories to process and the corresponding business contact emails.

**Sample `SourceFolders.csv`:**

<pre><code>"Source Path","Business Email"
"C:\\TestData\\ProjectA","projecta@example.com"
"C:\\TestData\\ProjectB","projectb@example.com"
"C:\\TestData\\ProjectC","projectc@example.com"
</code></pre>

**Columns:**

- **Source Path**: The full path to the source directory to process.
- **Business Email**: Email address of the business contact responsible for the source directory.

---

## Running the Script

1. **Prepare the Environment:**

   - Ensure that the prerequisites are met.
   - Place the script, `ArchiveConfig.json`, and `SourceFolders.csv` in accessible locations.

2. **Adjust Execution Policy (if necessary):**

   - You may need to allow the script to run by setting the execution policy:

     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

3. **Run the Script:**

   - Open PowerShell as an administrator.
   - Navigate to the directory containing the script.
   - Execute the script with optional parameters if needed:

     ```powershell
     .\SFP-Archive.ps1 -ConfigPath "C:\Scripts\ArchiveConfig.json" -SourceListPath "C:\Scripts\SourceFolders.csv"
     ```

   - If `-ConfigPath` or `-SourceListPath` are not specified, the script uses default paths:

     - **ConfigPath**: `C:\Scripts\ArchiveConfig.json`
     - **SourceListPath**: `C:\Scripts\SourceFolders.csv`

4. **Monitor the Execution:**

   - Console output will display the progress.
   - All console output is also logged to the file specified in `LogFilePath`.

---

## Logging

The script maintains comprehensive logging for auditing and troubleshooting purposes.

### 1. Console and Log File Output

- **Console Output:**

  - Displays real-time progress and information about the script's execution.
  - Messages include processing steps, file inclusions/exclusions, and any errors.

- **Log File Output:**

  - All console messages are also written to the log file specified in `LogFilePath`.
  - Each entry in the log file is timestamped.
  - Useful for reviewing past runs and diagnosing issues.

### 2. GeoDrive Audit Log

- **Location:**

  - Specified by `GeoDriveAuditLogPath` in `ArchiveConfig.json`.

- **Content:**

  - Records all file operations with timestamps.
  - Each entry includes:
    - Date and time of the operation.
    - Source file path.
    - Destination file path.
    - Status of the operation (`Initiated`, `Success`, `Failed`).

- **Format:**

  - CSV file for easy import into spreadsheet applications.

### 3. Per-Directory Logs

- **Location:**

  - A CSV log file named as per `PerDirectoryLogFileName` is created in each source directory where files were archived.

- **Content:**

  - Lists all files that were archived from that directory.
  - Includes:
    - Last accessed date.
    - File name.
    - New location in the archive.
  - Header includes contact information from `Business Email` in `SourceFolders.csv`.

- **Purpose:**

  - Provides users with information on archived files.
  - Users can contact the specified email address if they need access to archived files.

---

## Error Handling

- **Retries:**

  - The script attempts to copy each file up to two times in case of transient errors.

- **Error Logging:**

  - Errors are logged to the console, log file, and included in email notifications if enabled.
  - The `changesLog` array collects error messages and summaries of operations.

- **Exception Handling:**

  - Try-catch blocks are used to handle exceptions during file operations, directory access, and configuration loading.

- **Notifications:**

  - Critical errors trigger an email to the administrator specified in `AdminEmail`.

---

## Email Notifications

- **Purpose:**

  - Provides administrators with reports on the script's activities and alerts for any errors.

- **Configuration:**

  - Enabled or disabled via `EnableEmailNotifications` in `ArchiveConfig.json`.
  - Requires SMTP server settings in `EmailSettings`.

- **Emails Sent:**

  - **Success Report:**

    - Sent after the script completes, summarizing the files archived.
    - Subject line specified in `EmailSettings.Subject`.

  - **Error Notifications:**

    - Sent immediately when a critical error occurs.
    - Contains error details for prompt action.

---


## Conclusion

This archive script automates the process of archiving old files, helping you manage storage efficiently.
---

**Note:** Always ensure you have backups and permissions are correctly set before running scripts that modify or delete files.

For any questions or support, please contact the script administrator at `james.gagan@gov.bc.ca`.
