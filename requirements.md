# Branch Purging and Archival Policy

## 1. Branch Categorization

### Protected Branches

- develop
- stage
- master
*(excluded from purging/archival)*

### Feature/Hotfix/Release Branches

- All other branches *(subject to purging/archival)*

## 2. Criteria for Purging and Archival

- **Inactive Period:** No commits or updates in the last 30 days
- **Merged Status:** Branches already merged into develop, stage, or master

## 3. Archival Process

- **Archival Branch Prefix:** Move inactive branches to a prefixed namespace (e.g., `archived/branch-name`)
- **Tagging:** Optional tagging of latest commit before archiving (e.g., `archived-branchname-YYYYMMDD`)

## 4. Purging Process

- **Retention Period:** Keep archived branches for 60 days before permanent deletion
- **Auto-Deletion:** Automatically delete branches that remain archived and inactive for an additional 60 days

## 5. Exclusions

- Branches with active/open PRs
- Branches linked to critical releases or tagged versions

## Implementation Details

### A. Automated Scripts

- Weekly execution of archival script
- Monthly execution of purge script

### B. Notifications and Logging

- Slack/Email notifications before archival and deletion actions
- Action logging in centralized system for audit purposes

#### C. Governance and Approval Workflow

- Optional manual review for critical branches
- Approval process for branch deletion via Pull Requests
