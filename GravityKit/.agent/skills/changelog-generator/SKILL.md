---
name: changelog-generator
description: "Automated changelog generation from git history using conventional commits. Produces structured CHANGELOG.md with version grouping, categories, and release notes. Use when releasing a version or maintaining project history."
user-invocable: true
risk: safe
---

# Changelog Generator

Automate CHANGELOG.md generation from conventional commit history.

## When to Use
- Preparing a new release and need release notes
- Maintaining a structured CHANGELOG.md
- Generating GitHub release descriptions from git log
- Summarizing what changed between two versions

## Tools

### Using `conventional-changelog-cli`
```bash
npx conventional-changelog-cli -p angular -i CHANGELOG.md -s
# -p: preset (angular, atom, ember, eslint, express, jquery)
# -i: input file (existing changelog)
# -s: write to same file
# -r 0: regenerate entire changelog from scratch
```

### Using `git-cliff` (Rust-based, fast)
```bash
# Install
cargo install git-cliff
# or: brew install git-cliff

# Generate
git cliff --output CHANGELOG.md

# For a specific range
git cliff v1.0.0..HEAD --output CHANGELOG.md
```

### Manual Generation (pure git)
```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"- %s (%h)" --no-merges

# Group by type
git log --pretty=format:"%s" | grep "^feat:" | sed 's/^feat: /- /'
```

## Conventional Commits Format
```
feat: add user authentication
fix: resolve login redirect loop
docs: update API reference
chore: bump dependencies
refactor: extract auth middleware
BREAKING CHANGE: rename login endpoint to /auth/signin
```

## Changelog Structure
```markdown
## [1.2.0] - 2024-01-15

### Features
- Add user authentication (#42)

### Bug Fixes
- Resolve login redirect loop (#38)

### Breaking Changes
- Rename login endpoint to /auth/signin
```

## Best Practices
- Use conventional commits for all team members
- Tag releases with `git tag -a v1.2.0 -m "Release 1.2.0"`
- Automate in CI with GitHub Actions on release branch push
