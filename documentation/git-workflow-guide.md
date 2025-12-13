# Git Workflow Guide

This document outlines the standard git workflow for this project, including commit message conventions, branching strategy, and pull request guidelines.

## Table of Contents
- [Commit Message Convention](#commit-message-convention)
- [Branching Strategy](#branching-strategy)
- [Commit Process](#commit-process)
- [Push Process](#push-process)
- [Pull Request Guidelines](#pull-request-guidelines)

## Commit Message Convention

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

Must be one of the following:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies (Docker, dependencies, etc)
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

### Scope

The scope should specify the place of the commit change. Examples:

- `airflow`: Changes to Airflow configuration or DAGs
- `spark`: Changes to Spark jobs or configuration
- `docker`: Changes to Docker or docker-compose files
- `docs`: Documentation changes
- `config`: Configuration changes

### Subject

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end
- Maximum 50 characters

### Body (Optional)

- Use the imperative, present tense
- Explain what and why, not how
- Wrap at 72 characters

### Footer (Optional)

- Reference issues or pull requests
- Note breaking changes

### Examples

#### Simple commit:
```
feat(spark): add hello world PySpark job

Add a simple PySpark job that creates a DataFrame and displays a greeting message.
```

#### Commit with breaking change:
```
refactor(docker): update Spark version to 4.0.1

BREAKING CHANGE: Spark version updated from 3.5.7 to 4.0.1
- Update docker-compose.yaml with new Spark image
- Update Dockerfile to download Spark 4.0.1 binaries
- Python 3.12 now supported natively
```

#### Multiple changes:
```
build(docker): configure Airflow-Spark integration

- Install Java 17 in Airflow container
- Add Spark binaries to /opt/spark
- Configure JAVA_HOME and SPARK_HOME environment variables
- Add spark-jobs volume mount for job files

Closes #123
```

## Branching Strategy

### Main Branches

- **main/master**: Production-ready code
  - Always stable
  - Protected branch (requires pull request)
  - Tagged with version numbers

- **develop**: Integration branch for features
  - Latest delivered development changes
  - Base branch for feature branches

### Supporting Branches

#### Feature Branches
- **Naming**: `feature/<feature-name>`
- **Example**: `feature/add-spark-monitoring`
- **Created from**: `develop`
- **Merged back into**: `develop`

#### Fix Branches
- **Naming**: `fix/<bug-name>`
- **Example**: `fix/spark-connection-timeout`
- **Created from**: `develop` or `main` (for hotfixes)
- **Merged back into**: `develop` or `main`

#### Documentation Branches
- **Naming**: `docs/<doc-name>`
- **Example**: `docs/update-readme`
- **Created from**: `develop`
- **Merged back into**: `develop`

## Commit Process

### 1. Check Current Status

```bash
git status
```

Review all changed files to ensure you're committing the right changes.

### 2. Stage Changes

```bash
# Stage specific files
git add <file1> <file2>

# Or stage all changes
git add .
```

### 3. Review Staged Changes

```bash
# See what will be committed
git diff --staged
```

### 4. Create Commit

```bash
git commit -m "<type>(<scope>): <subject>" -m "<body>"
```

**Best Practice**: For complex commits, use an editor:

```bash
git commit
```

This opens your default editor where you can write a detailed commit message.

### 5. Verify Commit

```bash
# View last commit
git log -1

# Or more detailed view
git show
```

## Push Process

### 1. Ensure Local is Up-to-Date

```bash
# Fetch latest changes
git fetch origin

# Check if your branch is behind
git status
```

### 2. Pull Latest Changes (if needed)

```bash
# If on main/master or develop
git pull origin <branch-name>

# Or with rebase to maintain linear history
git pull --rebase origin <branch-name>
```

### 3. Push to Remote

```bash
# First time pushing a new branch
git push -u origin <branch-name>

# Subsequent pushes
git push
```

### 4. Verify Push

```bash
# Check remote branches
git branch -r

# Or view remote status
git remote show origin
```

## Pull Request Guidelines

### Before Creating a Pull Request

1. **Ensure all commits follow the commit message convention**
2. **Update documentation** if necessary
3. **Run tests** (if applicable)
4. **Ensure no merge conflicts** with target branch
5. **Review your own changes** one more time

### Pull Request Title

Use the same convention as commit messages:

```
<type>(<scope>): <brief description>
```

**Example**: `feat(airflow): add Spark monitoring DAG`

### Pull Request Description Template

```markdown
## Description
Brief description of the changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
Describe the tests you ran to verify your changes:
- Test 1
- Test 2

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Related Issues
Closes #<issue-number>
```

### Pull Request Best Practices

1. **Keep PRs focused**: One feature/fix per PR
2. **Keep PRs small**: Easier to review (ideally < 400 lines changed)
3. **Write clear descriptions**: Explain what, why, and how
4. **Reference related issues**: Use "Closes #123" or "Fixes #456"
5. **Respond to feedback**: Address review comments promptly
6. **Keep PR up-to-date**: Rebase or merge from target branch if needed

### Review Process

1. **Self-review**: Review your own PR first
2. **Request reviewers**: Assign appropriate team members
3. **Address feedback**: Make requested changes
4. **Resolve conversations**: Mark conversations as resolved when addressed
5. **Squash commits** (optional): Clean up commit history before merging
6. **Merge**: Use appropriate merge strategy (merge commit, squash, or rebase)

## Complete Workflow Example

### Starting a New Feature

```bash
# 1. Ensure you're on develop and up-to-date
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/add-data-pipeline

# 3. Make changes and commit
git add .
git commit -m "feat(airflow): add data ingestion pipeline

- Create DAG for daily data ingestion
- Add validation tasks
- Configure retry logic and alerts"

# 4. Push feature branch
git push -u origin feature/add-data-pipeline

# 5. Create pull request on GitHub/GitLab
# (Use web interface)

# 6. After PR approval, merge to develop
# (Use web interface or command line)

# 7. Delete feature branch
git branch -d feature/add-data-pipeline
git push origin --delete feature/add-data-pipeline

# 8. Update local develop
git checkout develop
git pull origin develop
```

### Making a Hotfix

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b fix/critical-bug

# 2. Fix the issue and commit
git add .
git commit -m "fix(spark): resolve connection timeout issue

- Increase Spark connection timeout to 30s
- Add retry logic for transient failures
- Update connection configuration

Fixes #789"

# 3. Push and create PR to main
git push -u origin fix/critical-bug

# 4. After merging to main, also merge to develop
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

## Tips and Best Practices

### Commit Frequently
- Make small, logical commits
- Each commit should represent one logical change
- Easier to review, revert, and cherry-pick

### Write Meaningful Messages
- Future you (and others) will thank you
- Good messages explain "why", not just "what"
- Bad: `fix bug`
- Good: `fix(spark): resolve memory leak in worker nodes`

### Use Interactive Rebase
```bash
# Clean up commits before pushing
git rebase -i HEAD~3

# Squash, reword, or reorder commits
```

### Amend Last Commit
```bash
# Fix last commit (before pushing)
git commit --amend

# Add forgotten files to last commit
git add forgotten_file.py
git commit --amend --no-edit
```

### Stash Changes
```bash
# Save work in progress without committing
git stash

# Apply stashed changes later
git stash pop
```

## Common Issues and Solutions

### Accidentally committed to wrong branch
```bash
# Move commit to correct branch
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1
```

### Need to undo last commit (not pushed)
```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes and commit
git reset --hard HEAD~1
```

### Pushed sensitive data
```bash
# Remove from history (use with caution!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <file>" \
  --prune-empty --tag-name-filter cat -- --all

git push --force
```

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
