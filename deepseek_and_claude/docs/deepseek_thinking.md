```

Okay, I need to create a Python project that automates cleaning up inactive GitHub branches according to the given policy. Let's break down the requirements and plan how to approach this.

First, the script has to handle both archiving and purging of branches. The policies mention excluding protected branches like develop, stage, and master. So I need to make sure those are not touched. Then, other branches (feature, hotfix, release) are subject to checks based on inactivity and merged status.

The criteria are: inactive for 30 days (no commits or updates) and already merged into one of the protected branches. Also, branches with open PRs or critical tags shouldn't be purged. For archival, they move to an archived/ namespace and maybe tag the latest commit. After 60 days in archived, they get deleted.

The deployment is on GCP, so maybe using Cloud Functions or Cloud Run with Cloud Scheduler for the weekly/monthly triggers. But for now, focusing on the scripts.

Let's think about the steps each script (archival and purge) needs to do.

For the archival script (weekly):

1. List all repos in the organization.

2. For each repo, list all branches except protected ones.

3. Check each branch's last commit date. If older than 30 days, proceed.

4. Check if the branch is merged into any protected branch.

5. Check if there's an open PR associated with the branch. If yes, skip.

6. Check for critical tags. If present, skip.

7. If all conditions met, move the branch to archived/branch-name (how? Maybe via renaming using GitHub API).

8. Optionally create a tag on the latest commit before moving.

9. Log the action and send a notification.

For the purge script (monthly):

1. List all archived branches (those in archived/ namespace).

2. Check their last activity date (if archived for 60 days).

3. Ensure no open PRs and not critical.

4. Delete the branch.

5. Log and notify.

Now, how to interact with GitHub? Use the GitHub REST API or PyGithub library. PyGithub might be easier for Python.

Need to handle pagination for repos and branches. Also, getting branch details like last commit date, whether it's merged, etc.

For checking if a branch is merged: GitHub API has an endpoint to check if a branch is merged into another. So for each branch, check against develop, stage, master.

Open PRs: List PRs for the repo where the head is the branch name. If any open, skip.

Critical tags: How to determine? Maybe look for tags that match a certain pattern or have specific annotations. Need clarification from the policy. Maybe tags that are linked to releases. So check if the branch has tags that are considered critical. The user might need to define a list of critical tags or a way to detect them.

Handling archival: Rename the branch to archived/branch-name. Wait, but renaming a branch in GitHub isn't straightforward. Branches are pointers to commits. So you can't rename a branch directly; instead, you create a new branch with the desired name pointing to the same commit and delete the old one. But deleting the old branch might be part of the process. Wait, but the original branch would be deleted. Maybe the archival process is to create a new branch in the archived/ namespace and then delete the original branch. But how does that work with existing references? Need to confirm.

Alternatively, maybe the archival is just moving the branch name, which would involve creating the new branch and deleting the old one. So steps would be: create archived/branch-name pointing to the same commit as the original branch, then delete the original branch. But this could cause issues if someone is still using the old branch name. However, according to the policy, these branches are inactive, so maybe it's acceptable.

Another approach: Use Git's native commands to create the archived branch and delete the original. But since this is a script using the GitHub API, perhaps using PyGithub to create the new ref and delete the old one.

So for each branch to archive:

1. Get the commit SHA of the branch.

2. Create a new reference in the repo under refs/heads/archived/branch-name pointing to that SHA.

3. Delete the original branch's reference.

Yes, that's possible via the API. So in PyGithub, maybe something like:

repo.create_git_ref(ref=f"refs/heads/archived/{branch_name}", sha=sha)

repo.get_git_ref(f"heads/{branch_name}").delete()

But need to handle potential conflicts if the archived branch already exists. Maybe check if the archived branch exists before creating it. If it does, skip or handle accordingly.

For the tagging part: create a tag on the latest commit with a name like archived-branchname-YYYYMMDD. Using PyGithub's create_tag method.

Now, authentication: the script needs a GitHub token with sufficient permissions (repo access) for the organization. Storing this securely, maybe in GCP Secret Manager.

Logging and notifications: Use logging module to log actions, and also send messages to Slack/Email. For Slack, use webhooks; for email, maybe SMTP or a third-party service. These would require configuring credentials, which should be stored securely.

Deployment on GCP: The scripts can be deployed as Cloud Functions, triggered by Cloud Scheduler. Each function (archival and purge) would run on their respective schedules. Alternatively, a Cloud Run service that's triggered periodically.

Considering the script's structure, it should be modular. Maybe separate classes or functions for GitHub interaction, checking criteria, handling archival/purge, logging, notifications.

Possible modules:

- github_client.py: Handles API interactions, listing repos, branches, checking merged status, etc.

- criteria_checker.py: Contains functions to check if a branch meets archival or purge criteria.

- archiver.py: Handles the archival process (creating archived branch, tagging, deleting original).

- purger.py: Handles the purge process (deleting archived branches after retention period).

- notifier.py: Sends Slack/Email notifications.

- logger.py: Logs actions to file or centralized logging (maybe Cloud Logging).

Testing is important. Need to mock GitHub API responses to test the criteria checks without hitting the real API.

Now, considering error handling and rate limits. GitHub API has rate limits, so the script should handle that with retries or pagination properly.

Also, dealing with large number of repos and branches efficiently. Maybe async processing, but Python's asyncio might complicate things. Alternatively, use multiprocessing or just sequential processing with proper pagination.

For the archival process:

Loop through each repo in the org.

For each repo:

- Get list of branches, exclude protected ones (develop, stage, master).

- For each branch:

- Check last commit date (last_commit_date = branch.commit.commit.last_modified)

- If last_commit_date < (now - 30 days), proceed.

- Check if branch is merged into any protected branches.

- Check for open PRs associated with the branch.

- Check for critical tags on the branch.

- If all conditions met, proceed to archive.

How to check if a branch is merged? Using the GitHub API's compare endpoint. For example, GET /repos/{owner}/{repo}/compare/{base}...{head} to see if the head branch is ahead or behind. Or using the 'merge' endpoint to check if mergeable.

Alternatively, using PyGithub's get_merge_status method. Wait, the PyGithub's Branch object might have a method to check if it's merged. Alternatively, for each protected branch (develop, stage, master), check if the current branch is merged into it.

Wait, the criteria says "Merged Status: Branches already merged into develop, stage, or master." So if the branch has been merged into any of those, it's a candidate for archival.

So, for a given branch, check if it has been merged into develop, stage, or master.

In the GitHub API, there's an endpoint: GET /repos/{owner}/{repo}/branches/{branch}/merged_into

But I'm not sure. Alternatively, for each protected branch (base), check if the feature branch is merged into it. Using the compare endpoint, if the status is "identical" or "behind", then it's merged. Or use the 'GET /repos/{owner}/{repo}/commits/{commit_sha}/branches-where-head' to find if the branch's HEAD is in the protected branch's history.

Alternatively, using the PyGithub's Repository object to get a commit and check if it's part of the protected branch.

This part might be tricky. Let's think: for a given branch, we can get its HEAD commit. Then, check if that commit exists in any of the protected branches. That's not sufficient, because the commit could be present but not merged via a PR. Maybe using the GitHub API to check if the branch is merged.

Alternatively, for each protected branch (like develop), check if the feature branch is merged into it. The PyGithub method might be:

repo = g.get_repo(full_repo_name)

merge_status = repo.merge(protected_branch, branch_name)

But that's actually performing a merge, which we don't want. Wait, perhaps the correct way is to use the compare API. For example:

compare_result = repo.compare(protected_branch, branch.commit.sha)

If compare_result.behind_by == 0, then the protected branch is up to date with the branch, meaning the branch is merged.

Alternatively, compare_result.status could be 'identical' or 'ahead' (if the branch has commits not in the protected branch). Hmm, this might not be accurate. Another approach: check if the branch's HEAD is reachable from the protected branch. Using the GitHub API, you can check if a commit is in another branch.

So, for a branch to be considered merged into develop, its HEAD commit should be an ancestor of develop's HEAD commit.

Using the GitHub API: GET /repos/{owner}/{repo}/commits/{commit_sha}/branches-where-head

But this endpoint might not exist. Alternatively, use the 'GET /repos/{owner}/{repo}/commits/{commit_sha}' and look at the parents. But this could be complicated.

Alternatively, use the command line git merge-base --is-ancestor <commit> <develop-commit>. But since we're using the API, not local git.

Hmm. Maybe the PyGithub API has a way to check if a branch is merged. Let me check the PyGithub documentation.

Looking at PyGithub's documentation: There's a method on the PullRequest module, but maybe not directly for branches. Alternatively, perhaps using repo.get_commit(sha=commit_sha).get_statuses().

Alternatively, here's a way: for a given branch, check if there's a PR that's merged and the base is one of the protected branches. But that would require checking PRs associated with the branch, which might not cover all cases (like branches merged via squash or without a PR).

This part is a bit challenging. Maybe for the purpose of the script, assume that a branch is considered merged into a protected branch if the GitHub API's compare endpoint returns that the protected branch is ahead of or equal to the branch in question. For example, if the result of comparing protected_branch to feature_branch shows that the protected branch is ahead, then the feature branch has been merged.

Alternatively, perhaps using the list commits on the protected branch and see if the feature branch's HEAD is in that list. But that's inefficient for large repos.

Alternatively, since the branch hasn't been active in 30 days, maybe it's safe to assume that if it's merged into any of the protected branches, it can be archived. But the actual method to check this via the API needs to be accurate.

Alternatively, for each protected branch (develop, stage, master), check if the feature branch's HEAD is part of the protected branch's commit history. This can be done via the GitHub API's GET /repos/{owner}/{repo}/commits?sha={protected_branch}&until={feature_branch_head_sha} to see if that commit is present. But I'm not sure if the 'until' parameter works that way.

Alternatively, use the GitHub API's GET /repos/{owner}/{repo}/commits/{feature_sha}/branches-where-head. This endpoint returns the branches where the commit is the HEAD. Wait, but that would only tell us which branches currently point to that commit. Not helpful for checking if it's merged into another branch.

This is a bit of a hurdle. Maybe we can use the GitHub API to check if the feature branch is merged into the base branch by looking for a merge commit. But that's not reliable.

Alternatively, perhaps the script can check if the branch has been merged via checking the merged attribute in the branch's pull request. But not all merged branches have associated PRs, especially if merged via other means.

Hmm. The policy states "merged into develop, stage, or master". So if the branch was merged into any of those, regardless of method, it should be considered. However, determining this programmatically is difficult.

Maybe the safest way is to check if the branch is behind the protected branch. If the protected branch has all the commits from the feature branch, then it's considered merged.

To check this, use the compare endpoint: GET /repos/{owner}/{repo}/compare/{base}...{head}

Where base is the protected branch (e.g., develop) and head is the feature branch.

If the status is "identical" or "behind", that means the feature branch is either up to date with or behind the protected branch. Which implies that all commits in the feature branch are already in the protected branch, so it's safe to archive.

Wait, if the feature branch is behind the protected branch, that doesn't mean the protected branch has the feature's commits. For example, if the feature branch was created from develop, then develop moves ahead, the feature branch is behind, but the feature hasn't been merged. So comparing develop to feature branch would show that develop is ahead, meaning the feature branch is behind. But that doesn't imply merging.

This approach is not correct. Therefore, comparing the feature branch to the protected branch is not sufficient. What we need is to check if all commits in the feature branch are present in the protected branch.

An alternative way is to check if the latest commit of the feature branch is reachable from the protected branch. In Git terms, if the protected branch contains the feature branch's HEAD commit.

The GitHub API has an endpoint for this: GET /repos/{owner}/{repo}/commits/{commit_sha}

In the response, look at the "commit" object, which has parents. If the commit is part of the protected branch's history, then it's reachable.

But checking this via the API is not straightforward. Another approach is to use the GitHub GraphQL API to query whether the commit exists in the protected branch's history.

Here's a GraphQL query that could be used:

query($owner: String!, $repo: String!, $commitSha: GitObjectID!, $protectedBranch: String!) {

repository(owner: $owner, name: $repo) {

object(oid: $commitSha) {

... on Commit {

history(first: 1, until: "2023-01-01") { # Not sure about the syntax here

nodes {

oid

}

}

}

}

ref(qualifiedName: $protectedBranch) {

target {

... on Commit {

history(first: 100, contains: $commitSha) {

nodes {

oid

}

}

}

}

}

}

}

This is just a rough idea. Alternatively, check if the commit exists in the protected branch's history using the 'contains' parameter. Wait, the 'history' connection has a 'contains' parameter which is a GitObjectID. So, if you query the history of the protected branch and pass the feature branch's commit SHA, you can see if it's present.

But this might require multiple queries, especially if the protected branch has a long history.

Alternatively, use the compare endpoint with the feature branch as the base and the protected branch as the head. For example:

compare_result = repo.compare(feature_branch, protected_branch)

If compare_result.ahead_by is 0, that means the protected branch is not ahead of the feature branch. Wait, no. The compare endpoint shows what's in the head that's not in the base. So comparing protected_branch (head) to feature_branch (base) would show the commits in protected_branch that are not in feature_branch. If the feature branch is merged into protected_branch, then the compare between feature_branch and protected_branch would show that protected_branch has all the feature's commits plus possibly more. So the 'ahead_by' would be the number of commits in protected_branch beyond the feature branch.

But this doesn't directly answer if the feature branch's commits are in the protected branch.

This is getting complicated. Maybe for the purposes of the script, we can assume that if a branch has been inactive for 30 days and it's merged into any protected branch (as per the policy), it can be archived. But how to check merged status.

Alternative Idea: Use the GitHub API to list all merged pull requests where the base is a protected branch and the head is the feature branch. If such a PR exists and is merged, then the branch is considered merged.

But this misses branches that were merged without a PR, which might be possible. However, according to best practices, merging should happen via PRs. If that's the case, then this approach could work.

So, for a given branch, check if there exists a merged PR where the head is the branch and the base is a protected branch.

To do this, for each repo and branch:

List all PRs where head is the branch name, base is a protected branch, and state is 'closed' and merged.

If any such PR exists, then the branch is considered merged.

This approach would work if all merges into protected branches are done via PRs. If not, this check would miss some merged branches.

But given the policy mentions "Merged Status: Branches already merged into develop, stage, or master", perhaps the merged status is determined by PRs being merged. So this check would be appropriate.

So steps for merged check:

For a given branch in a repo:

Loop through each protected branch (develop, stage, master).

For each protected branch, check if there's a merged PR with base as protected branch and head as the feature branch.

If any exists, then the branch is merged.

This can be done using the PyGithub's get_pulls method with parameters.

But GitHub's API for listing PRs allows filtering by head, base, state.

So in PyGithub:

prs = repo.get_pulls(state='closed', base=protected_branch, head=branch_name)

for pr in prs:

if pr.merged:

return True

If any PR is found that is merged, then the branch is considered merged into the protected branch.

This seems manageable. However, the 'head' parameter in the GitHub API requires the format 'user:branch' for cross-repo PRs, but for same repo, it's just 'branch'. So if the branch is in the same repo, the head would be 'branch_name'.

So in code:

pr_list = repo.get_pulls(state='closed', base='develop', head=branch.name)

Then, check if any of these PRs are merged.

But since a branch could have multiple PRs, need to check all of them.

This approach could work, but may have some edge cases. For example, if a branch was merged into develop via a PR, then later another PR was opened and closed without merging. The code would still detect the merged PR.

So this check should work for the intended purpose.

Once we've confirmed merged status, next is checking open PRs. For this, list all open PRs where the head is the branch. If any exist, skip archiving.

For critical tags: The policy says "Branches linked to critical releases or tagged versions." So, if a branch has a tag that is considered critical, skip archiving/purging.

But how to determine which tags are critical? The user needs to define this. Maybe tags that match a certain pattern (e.g., 'v*' for version tags), or tags that are annotated, or tags that are associated with a release.

Alternatively, the script can check if the branch has any tags pointing to its HEAD commit. Then, check if those tags are considered critical. For example, any tag that starts with 'v' or 'release-' could be considered critical.

The user might need to specify a list of critical tag patterns, which can be passed as a configuration to the script.

So, in the script's configuration, there could be a list like CRITICAL_TAG_PATTERNS = ['v*', 'release-*'].

Then, for each branch, check if any of its tags match any of these patterns.

To get the tags pointing to the branch's HEAD commit, use the GitHub API to list tags and check if their commit SHA matches the branch's HEAD SHA.

Alternatively, for a given commit SHA, list all tags that point to it.

In PyGithub:

commit = repo.get_commit(sha=branch.commit.sha)

tags = []

for tag in repo.get_tags():

if tag.commit.sha == commit.sha:

tags.append(tag)

Then, check if any of these tags match the critical patterns.

If any tag matches, skip archiving/purging.

Now, the archival process:

Once a branch meets all criteria, we need to:

1. Create a new branch with the name 'archived/branch-name'.

2. Delete the original branch.

3. Optionally create a tag on the latest commit.

But creating the archived branch might require checking if it already exists. If the branch already exists in the archived namespace, perhaps skip or handle naming conflicts. For example, appending a timestamp if necessary.

Alternatively, the script could check if the archived branch exists, and if so, skip archiving (since it's already archived). But according to the policy, once archived, the branch is subject to purging after 60 days. So maybe the script should only process non-archived branches.

So during archival, only process branches not in the 'archived/' namespace.

Thus, in the initial branch listing, exclude branches that start with 'archived/'.

But during the purge process, list branches in 'archived/' namespace.

So the archival script's branch list excludes protected branches and branches already in 'archived/'.

Now, the archival steps:

For a qualifying branch:

1. Get the current SHA of the branch.

2. Create a new branch in 'archived/branch-name' pointing to the SHA.

3. Delete the original branch.

4. Create a tag if configured.

Handling errors during creation or deletion: For example, if creating the archived branch fails (due to name conflict), log the error and skip. Similarly, if deletion of the original branch fails, log and maybe leave it (but that would leave both branches; need to handle).

But according to the policy, after archiving, the original branch should be moved, so deletion is necessary.

But GitHub does not allow renaming; you can create a new branch and delete the old one. So this process should be atomic: create the new branch first, then delete the old one. If creation succeeds but deletion fails, the old branch remains, which should be handled in the next run (since it's still inactive and would meet criteria again).

Now, the purge process:

For branches in 'archived/' namespace:

Check if they have been archived for 60 days. How to track when they were archived? Because GitHub doesn't store branch creation dates. So the last commit date of the archived branch would be the same as the original branch. But that date is older than 30 days already. Wait, the original branch was inactive for 30 days before archival. Then, after archival, the retention period is 60 days. So the total time from the last commit to purge would be 30 + 60 = 90 days.

Wait, the policy says:

- Inactive for 30 days: archive.

- Archived branches are kept for 60 days, then deleted.

So the purge script checks if the archived branch has been inactive for 60 days since archival. But since the archived branch's last commit is the same as the original, which was already inactive for 30 days before archival. So the purge script needs to check if the branch has been archived for 60 days. But GitHub doesn't track when a branch was created. So how to determine the archival time?

This is a problem. Because the last commit date of the archived branch is the same as the original branch's last commit date, which was already 30 days old at the time of archival. So after archival, the 60 days retention period starts. So the cutoff would be the archival date + 60 days. But we can't track the archival date unless we log it ourselves.

Ah, this is a crucial point. The script must track when a branch was archived to enforce the 60-day retention. Otherwise, it can't rely on the branch's last commit date.

So the script needs to maintain a log of when branches were archived. This log can be stored somewhere, like a database or a file in a storage bucket (GCS). For example, whenever a branch is archived, record the branch name, repo, and archival date. Then, during the purge process, check the log to see if 60 days have passed since archival.

This adds complexity, as the script now needs to maintain state between runs. But without this, there's no way to know when the 60-day period starts.

Therefore, the archival script must log the archival actions with timestamps, and the purge script uses this log to determine which branches are eligible for deletion.

So, the steps for archival:

After moving the branch to archived/, log the repo name, branch name (original and archived), and the current date in a persistent storage (like a GCS bucket file or a Firestore database).

For the purge process:

Read the log entries, check if 60 days have passed since the archival date. For each entry that meets the retention period, check if the archived branch still exists (in case it was manually deleted), then delete it, and remove the entry from the log.

This way, the purge script relies on the log rather than the branch's last activity date.

Alternatively, if using a database, mark entries as purged once deleted.

This adds some infrastructure dependencies (like GCS or Firestore), but it's necessary for accurate retention tracking.

Considering deployment on GCP, using Firestore or a GCS file makes sense. Firestore is a managed NoSQL database, which is suitable for this. Alternatively, a simple GCS file that the script reads and updates. However, concurrent writes could be an issue if multiple instances run, but if the script is scheduled to run as a single instance (like a Cloud Function), it's manageable.

So, during archival:

1. After creating the archived branch, log the archival event with timestamp.

Log entry structure could be:

{

"repo": "repo-name",

"original_branch": "feature-123",

"archived_branch": "archived/feature-123",

"archival_date": "2023-10-01",

"purged": false

}

Store this in Firestore or a GCS file.

During purging:

1. Read all log entries where purged is false and archival_date is older than 60 days.

2. For each entry, check if the archived_branch exists in the repo.

3. If exists, check for open PRs and critical tags (similar to archival checks).

4. If eligible, delete the archived branch.

5. Update the log entry to purged: true or remove it.

But wait, the purge policy says: "Automatically delete branches that remain archived and inactive for an additional 60 days." The 'inactive' here refers to no commits or updates. But since the archived branch is just a pointer and likely not updated, the 60 days is purely time-based from archival.

But according to the policy's wording, it's 60 days after archival. So tracking the archival date is necessary.

Thus, using a log with archival dates is required.

Now, the purge process:

For each archived branch in the log older than 60 days:

- Check if the branch still exists (in case someone manually deleted it).

- Check if the branch has open PRs (but since it's archived, probably not, but need to check).

- Check for critical tags (if any tags on the branch's HEAD are critical, skip deletion).

- If all checks pass, delete the branch and update the log.

But the original branch was already checked for open PRs and critical tags during archival. However, between archival and purge, new PRs could be opened against the archived branch, or new critical tags could be added. So during purge, the script should re-check these conditions.

Therefore, during purging:

For each archived branch in the log:

1. Check if current date - archival_date >= 60 days.

2. Check if the archived branch exists in the repo.

3. Check if the archived branch has any open PRs (head is the archived branch).

4. Check if the archived branch's HEAD has any critical tags.

5. If all conditions met, delete the archived branch and mark as purged in the log.

Now, implementing this requires:

- A data store for the archival log (Firestore, GCS file, etc.).

- During archival, adding entries to the log.

- During purging, querying the log and processing entries.

For the data store, using Firestore is a good choice as it's serverless and scales well. The script can use the Firestore Python SDK to interact with it.

Now, putting it all together.

The overall steps for the archival script:

For each repo in the organization:

For each branch in the repo (excluding protected and archived/):

Check if branch is inactive (last commit > 30 days)

Check if merged into any protected branch

Check for open PRs

Check for critical tags

If all conditions met:

Create archived branch

Delete original branch

Create tag (optional)

Log the archival in Firestore/GCS

Send notification

The purge script:

Read all archival log entries where archival_date < now - 60 days and purged = False

For each entry:

Check if archived branch exists in repo

Check for open PRs against the archived branch

Check for critical tags on the archived branch's HEAD

If all conditions met:

Delete archived branch

Mark log entry as purged

Send notification

Now, error handling:

- GitHub API rate limits: Use retries with exponential backoff, handle 403 errors.

- Network issues: Retry mechanisms.

- Partial failures: Log errors and continue processing other branches.

Notifications and logging:

- Use Python's logging module to log info, warnings, errors.

- Send notifications to Slack/Email via webhooks or APIs.

- For Slack, use incoming webhooks; for email, use SMTP or a service like SendGrid.

Configuration management:

- Store GitHub token, Slack webhook URL, email credentials in GCP Secret Manager.

- Retrieve them at runtime in the script.

Deployment on GCP:

- Use Cloud Functions for archival (weekly) and purge (monthly) scripts.

- Cloud Scheduler to trigger the functions via HTTP on the specified schedules.

- Store the archival log in Firestore.

- Use Secret Manager for credentials.

Potential code structure:

Project layout:

github_branch_cleaner/

├── main.py

├── github_client.py

├── criteria_checker.py

├── archiver.py

├── purger.py

├── notifier.py

├── logger.py

├── firestore_client.py

└── config.py

In main.py, have separate functions for archival and purge, which are triggered by Cloud Functions.

But since Cloud Functions need separate entry points, maybe have two separate functions: one for archival (scheduled weekly) and one for purge (scheduled monthly).

But for code reuse, common modules like github_client, criteria_checker, etc., can be shared.

Now, code examples.

First, github_client.py:

This module handles interactions with the GitHub API using PyGithub.

from github import Github, GithubIntegration

from github.Repository import Repository

from github.Branch import Branch

from github.Commit import Commit

from github.PullRequest import PullRequest

from typing import List, Optional, Dict, Any

import os

import logging

class GitHubClient:

def __init__(self, token: str):

self.github = Github(token)

self.logger = logging.getLogger(__name__)

def get_org_repos(self, org_name: str) -> List[Repository]:

org = self.github.get_organization(org_name)

return list(org.get_repos())

def get_branches(self, repo: Repository, exclude_protected: List[str] = ['master', 'develop', 'stage'], exclude_prefix: str = 'archived/') -> List[Branch]:

branches = []

for branch in repo.get_branches():

if branch.name in exclude_protected:

continue

if branch.name.startswith(exclude_prefix):

continue

branches.append(branch)

return branches

def get_branch_last_commit_date(self, branch: Branch) -> datetime:

commit = branch.commit

return commit.commit.author.date

def is_branch_merged_to_protected(self, repo: Repository, branch: Branch, protected_branches: List[str]) -> bool:

for protected_branch in protected_branches:

prs = repo.get_pulls(state='closed', base=protected_branch, head=branch.name)

for pr in prs:

if pr.merged:

return True

return False

def has_open_prs(self, repo: Repository, branch_name: str) -> bool:

prs = repo.get_pulls(state='open', head=branch_name)

return prs.totalCount > 0

def get_critical_tags(self, repo: Repository, branch: Branch, critical_tag_patterns: List[str]) -> List[str]:

# Get tags pointing to the branch's HEAD commit

commit_sha = branch.commit.sha

tags = []

for tag in repo.get_tags():

if tag.commit.sha == commit_sha:

tags.append(tag.name)

# Check if any tag matches the critical patterns

import fnmatch

critical_tags = []

for pattern in critical_tag_patterns:

critical_tags.extend(fnmatch.filter(tags, pattern))

return critical_tags

def create_archived_branch(self, repo: Repository, original_branch: Branch) -> bool:

archived_branch_name = f"archived/{original_branch.name}"

try:

# Check if archived branch already exists

repo.get_branch(archived_branch_name)

self.logger.warning(f"Archived branch {archived_branch_name} already exists in repo {repo.name}")

return False

except:

# Branch doesn't exist, create it

pass

try:

repo.create_git_ref(ref=f"refs/heads/{archived_branch_name}", sha=original_branch.commit.sha)

return True

except Exception as e:

self.logger.error(f"Failed to create archived branch {archived_branch_name}: {e}")

return False

def delete_branch(self, repo: Repository, branch_name: str) -> bool:

try:

ref = repo.get_git_ref(f"heads/{branch_name}")

ref.delete()

return True

except Exception as e:

self.logger.error(f"Failed to delete branch {branch_name}: {e}")

return False

def create_tag(self, repo: Repository, commit_sha: str, tag_name: str) -> bool:

try:

repo.create_git_tag(tag=tag_name, message=f"Archived branch tag {tag_name}", object=commit_sha, type='commit')

repo.create_git_ref(ref=f"refs/tags/{tag_name}", sha=commit_sha)

return True

except Exception as e:

self.logger.error(f"Failed to create tag {tag_name}: {e}")

return False

This is a rough draft. Need to handle exceptions, logging, and edge cases.

Then, the criteria_checker.py would have functions to check the conditions:

import datetime

from typing import List

from github import Repository, Branch

class CriteriaChecker:

def __init__(self, protected_branches: List[str], critical_tag_patterns: List[str], inactivity_days: int = 30):

self.protected_branches = protected_branches

self.critical_tag_patterns = critical_tag_patterns

self.inactivity_days = inactivity_days

def is_branch_inactive(self, last_commit_date: datetime.datetime) -> bool:

delta = datetime.datetime.now(datetime.timezone.utc) - last_commit_date

return delta.days >= self.inactivity_days

def is_branch_merged_to_protected(self, repo: Repository, branch: Branch) -> bool:

# Implement merged check using GitHubClient's method

pass

def has_open_prs(self, repo: Repository, branch_name: str) -> bool:

# Implement open PR check using GitHubClient's method

pass

def has_critical_tags(self, repo: Repository, branch: Branch) -> bool:

# Implement critical tag check using GitHubClient's method

pass

But perhaps the GitHubClient already handles these checks, so the criteria checker can use the client's methods.

But this modularization might be redundant. Alternatively, the GitHubClient can have the methods, and the criteria checks are done in the main script.

The archiver.py would orchestrate the archival process:

class Archiver:

def __init__(self, github_client: GitHubClient, notifier: Notifier, logger: Logger, config: dict):

self.github_client = github_client

self.notifier = notifier

self.logger = logger

self.config = config

def archive_branches(self, org_name: str):

repos = self.github_client.get_org_repos(org_name)

for repo in repos:

branches = self.github_client.get_branches(repo, self.config['protected_branches'], 'archived/')

for branch in branches:

last_commit_date = self.github_client.get_branch_last_commit_date(branch)

if not self.criteria_checker.is_branch_inactive(last_commit_date):

continue

if not self.github_client.is_branch_merged_to_protected(repo, branch, self.config['protected_branches']):

continue

if self.github_client.has_open_prs(repo, branch.name):

continue

critical_tags = self.github_client.get_critical_tags(repo, branch, self.config['critical_tag_patterns'])

if critical_tags:

self.logger.info(f"Skipping branch {branch.name} in repo {repo.name} due to critical tags: {critical_tags}")

continue

# Proceed to archive

archived_created = self.github_client.create_archived_branch(repo, branch)

if not archived_created:

continue

delete_success = self.github_client.delete_branch(repo, branch.name)

if not delete_success:

self.logger.error(f"Failed to delete original branch {branch.name} in repo {repo.name}")

continue

# Create tag if enabled

if self.config.get('create_tag_on_archive'):

tag_name = f"archived-{branch.name}-{datetime.datetime.now().strftime('%Y%m%d')}"

self.github_client.create_tag(repo, branch.commit.sha, tag_name)

# Log to Firestore

self.logger.log_archive(repo.name, branch.name, f"archived/{branch.name}")

# Send notification

self.notifier.send(f"Archived branch {branch.name} in repo {repo.name}")

But this is a simplified version. Also, error handling needs to be more robust.

The Firestore logging would require a separate module or integration.

For notifications, using a Notifier class that can send Slack/Email messages.

Now, considering configuration, the config can be a dictionary loaded from environment variables or a YAML file. For GCP deployment, environment variables are easier.

Example configuration:

GITHUB_ORG = "my-org"

PROTECTED_BRANCHES = ["master", "develop", "stage"]

CRITICAL_TAG_PATTERNS = ["v*", "release-*"]

INACTIVITY_DAYS = 30

RETENTION_DAYS = 60

CREATE_TAG_ON_ARCHIVE = True

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

EMAIL_NOTIFICATION_ADDRESS = "admin@example.com"

These can be retrieved from environment variables in the Cloud Function.

Putting it all together in the Cloud Function:

For the archival function:

import logging

from github_client import GitHubClient

from firestore_client import FirestoreClient

from notifier import Notifier

import os

from datetime import datetime

def github_archiver(request):

# Setup logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()

# Retrieve config from environment variables

config = {

'github_token': os.getenv('GITHUB_TOKEN'),

'github_org': os.getenv('GITHUB_ORG'),

'protected_branches': os.getenv('PROTECTED_BRANCHES', 'master,develop,stage').split(','),

'critical_tag_patterns': os.getenv('CRITICAL_TAG_PATTERNS', 'v*,release-*').split(','),

'inactivity_days': int(os.getenv('INACTIVITY_DAYS', 30)),

'create_tag_on_archive': os.getenv('CREATE_TAG_ON_ARCHIVE', 'True') == 'True',

'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),

'email_notification_address': os.getenv('EMAIL_NOTIFICATION_ADDRESS'),

}

# Initialize clients

github_client = GitHubClient(config['github_token'])

firestore_client = FirestoreClient()

notifier = Notifier(config['slack_webhook_url'], config['email_notification_address'])

# Process archival

repos = github_client.get_org_repos(config['github_org'])

for repo in repos:

branches = github_client.get_branches(repo, config['protected_branches'], 'archived/')

for branch in branches:

last_commit_date = github_client.get_branch_last_commit_date(branch)

if not is_inactive(last_commit_date, config['inactivity_days']):

continue

if not github_client.is_branch_merged_to_protected(repo, branch, config['protected_branches']):

continue

if github_client.has_open_prs(repo, branch.name):

logger.info(f"Skipping branch {branch.name} in repo {repo.name} due to open PRs")

continue

critical_tags = github_client.get_critical_tags(repo, branch, config['critical_tag_patterns'])

if critical_tags:

logger.info(f"Skipping branch {branch.name} in repo {repo.name} due to critical tags: {critical_tags}")

continue

# Proceed to archive

archived_name = f"archived/{branch.name}"

if github_client.create_archived_branch(repo, branch):

if github_client.delete_branch(repo, branch.name):

# Log to Firestore

firestore_client.log_archive(

repo_name=repo.name,

original_branch=branch.name,

archived_branch=archived_name,

archival_date=datetime.now()

)

# Create tag

if config['create_tag_on_archive']:

tag_name = f"archived-{branch.name}-{datetime.now().strftime('%Y%m%d')}"

github_client.create_tag(repo, branch.commit.sha, tag_name)

# Notify

message = f"Archived branch {branch.name} in repo {repo.name}"

notifier.send_slack(message)

notifier.send_email(message)

else:

logger.error(f"Failed to delete original branch {branch.name} in repo {repo.name}")

else:

logger.error(f"Failed to create archived branch for {branch.name} in repo {repo.name}")

return 'OK'

This is a simplified version. Error handling, pagination, and rate limiting are not fully implemented here.

For the purge function:

def github_purger(request):

# Setup

logger = logging.getLogger()

config = {

'github_token': os.getenv('GITHUB_TOKEN'),

'retention_days': int(os.getenv('RETENTION_DAYS', 60)),

'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),

'email_notification_address': os.getenv('EMAIL_NOTIFICATION_ADDRESS'),

}

github_client = GitHubClient(config['github_token'])

firestore_client = FirestoreClient()

notifier = Notifier(config['slack_webhook_url'], config['email_notification_address'])

# Get all archival entries older than retention_days

cutoff_date = datetime.now() - timedelta(days=config['retention_days'])

entries = firestore_client.get_entries_to_purge(cutoff_date)

for entry in entries:

repo = github_client.get_repo(entry['repo'])

# Check if archived branch exists

try:

branch = repo.get_branch(entry['archived_branch'])

except:

# Branch doesn't exist, mark as purged

firestore_client.mark_purged(entry.id)

continue

# Check open PRs

if github_client.has_open_prs(repo, entry['archived_branch']):

logger.info(f"Skipping purging {entry['archived_branch']} due to open PRs")

continue

# Check critical tags

critical_tags = github_client.get_critical_tags(repo, branch, config['critical_tag_patterns'])

if critical_tags:

logger.info(f"Skipping purging {entry['archived_branch']} due to critical tags: {critical_tags}")

continue

# Delete branch

if github_client.delete_branch(repo, entry['archived_branch']):

firestore_client.mark_purged(entry.id)

message = f"Purged branch {entry['archived_branch']} in repo {entry['repo']}"

notifier.send_slack(message)

notifier.send_email(message)

else:

logger.error(f"Failed to purge branch {entry['archived_branch']} in repo {entry['repo']}")

return 'OK'

This is a rough outline. The firestore_client would have methods to query entries older than cutoff and mark them as purged.

Now, regarding deployment on GCP:

- Create a Cloud Function for each script (archival and purge).

- Use Cloud Scheduler to trigger them weekly/monthly via HTTP.

- Store GitHub token, Slack webhook, etc., in Secret Manager and access them via environment variables in the Cloud Function.

- Use Firestore to track archival logs.

Potential issues and considerations:

1. Rate Limiting: GitHub API has rate limits. For large organizations, the script might hit these. Implementing pagination, using conditional requests, and handling rate limits with retries is essential.

2. Security: The GitHub token needs repo permissions (read/write). Use a fine-grained token with minimal permissions.

3. Idempotency: The script should handle partial failures and be idempotent, so rerunning it doesn't cause issues.

4. Logging and Monitoring: Use Cloud Logging for monitoring and set up alerts for failures.

5. Testing: Test the script on a test repo with sample branches to ensure it behaves as expected.

6. Handle Edge Cases: For example, if a branch is deleted manually between archival and purge steps, the script should handle it gracefully.

In conclusion, the script involves multiple components interacting with GitHub's API, a data store for tracking archival status, and notifications. Careful error handling and logging are crucial for reliability.
```