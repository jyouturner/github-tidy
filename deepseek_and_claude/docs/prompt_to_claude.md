```
I am working on a python project, likely a scheduled job that clean the inactive github branches (we have many repos and even more branches).
here is the policy:
Branch Purging and Archival Policy
1. Branch Categorization
Protected Branches: develop, stage, master (excluded from purging/archival)
Feature/Hotfix/Release Branches: All other branches (subject to purging/archival)
2. Criteria for Purging and Archival
Inactive Period: No commits or updates in the last 30 days.
Merged Status: Branches already merged into develop, stage, or master.
3. Archival Process
Archival Branch Prefix: Move inactive branches to a prefixed namespace for easy tracking, e.g., archived/branch-name.
Tagging: Optionally, tag the latest commit before archiving for reference, e.g., archived-branchname-YYYYMMDD.
4. Purging Process
Retention Period: Keep archived branches for 60 days before permanent deletion.
Auto-Deletion: Automatically delete branches that remain archived and inactive for an additional 60 days.
5. Exclusions
Open Pull Requests (PRs): Do not purge branches with active/open PRs.
Critical Tags: Branches linked to critical releases or tagged versions.

A. Automated Scripts
Schedule the archival script to run weekly and the purge script to run monthly.
B. Notifications and Logging
Slack/Email Notifications before archiving and deleting branches.
Logging actions in a file or centralized log system for audit purposes.
C. Governance and Approval Workflow
Manual Review for critical branches (optional).
Approval Process for deleting certain branches via Pull Requests.

--- 
attached are my train of thoughts 
---
Let's work on the project step by step, and it is planned to be deployed on GCP.

```