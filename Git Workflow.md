# Git Workflow: From New Change To Main

Use this workflow for every new fix, feature, setup change, or documentation update.

## 1. Start From Main

```bash
git checkout main
```

## 2. Get The Latest Version

```bash
git pull origin main
```

If Git says your branches have diverged, stop and ask the team before continuing.

## 3. Create A New Branch

Use a branch name that describes the work.

```bash
git checkout -b fix/example-name
```

Examples:

```bash
git checkout -b fix/navbar-dropdown
git checkout -b feature/login-page
git checkout -b setup/docker
git checkout -b docs/update-readme
```

## 4. Make Your Changes

Edit the project files for the fix or feature.

## 5. Check What Changed

```bash
git status
```

Optional:

```bash
git diff
```

## 6. Stage Your Changes

Stage all changed files:

```bash
git add .
```

Or stage specific files:

```bash
git add path/to/file
```

## 7. Commit Your Changes

```bash
git commit -m "Short description of the change"
```

Examples:

```bash
git commit -m "Fix navbar dropdown styling"
git commit -m "Add Docker setup"
git commit -m "Update Django CI workflow"
```

## 8. Push Your Branch To GitHub

For a new branch:

```bash
git push -u origin branch-name
```

Example:

```bash
git push -u origin fix/navbar-dropdown
```

After the branch already exists on GitHub, use:

```bash
git push
```

## 9. Open A Pull Request

Go to GitHub and open a pull request.

Set:

```text
base: main
compare: your-branch-name
```

Example:

```text
base: main
compare: fix/navbar-dropdown
```

## 10. Fill Out The Pull Request

Use a clear title:

```text
Fix navbar dropdown styling
```

Use a short description:

```md
## Summary

- Explain what changed
- Mention any files or areas affected
- Note anything reviewers should check

## Testing

- Ran the project locally
- Checked the changed page or feature
- Confirmed GitHub Actions passed
```

## 11. Wait For GitHub Actions

The Django CI check should run automatically.

Before merging, make sure it says:

```text
All checks passed
```

If it fails:

1. Click the failed check.
2. Read the error.
3. Fix the problem locally.
4. Commit the fix.
5. Push again.

```bash
git add .
git commit -m "Fix CI issue"
git push
```

The pull request will update automatically.

## 12. Get A Review

At least one other teammate must review and approve the pull request.

The reviewer should check:

- The code works
- The change matches the goal
- No unrelated files were changed
- The app still runs
- GitHub Actions passed

## 13. Resolve Comments

If the reviewer leaves comments, fix them on the same branch.

```bash
git add .
git commit -m "Address review feedback"
git push
```

Then ask for another review.

## 14. Merge Into Main

After approval and passing checks, merge the pull request into `main`.

Recommended option:

```text
Squash and merge
```

This keeps the `main` branch cleaner.

## 15. Update Your Local Main

After the pull request is merged:

```bash
git checkout main
git pull origin main
```

## 16. Delete The Old Branch

Delete the local branch:

```bash
git branch -d branch-name
```

Example:

```bash
git branch -d fix/navbar-dropdown
```

If GitHub did not delete the remote branch automatically:

```bash
git push origin --delete branch-name
```

## Full Example

```bash
git checkout main
git pull origin main
git checkout -b fix/navbar-dropdown

# Make changes

git status
git add .
git commit -m "Fix navbar dropdown styling"
git push -u origin fix/navbar-dropdown
```

Then:

1. Open a pull request on GitHub.
2. Wait for GitHub Actions to pass.
3. Get one teammate review.
4. Resolve any comments.
5. Squash and merge into `main`.
6. Pull the updated `main`.

## Important Rules

- Do not work directly on `main`.
- Do not push directly to `main`.
- Do not force push to `main`.
- Always create a branch for each fix or feature.
- Always open a pull request.
- Always get at least one review before merging.
- Always make sure GitHub Actions passes before merging.