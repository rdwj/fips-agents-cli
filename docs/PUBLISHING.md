# Publishing to PyPI with GitHub Trusted Publishing

This document explains how to publish `fips-agents-cli` to PyPI using GitHub Actions and trusted publishing (OIDC).

## Overview

We use **GitHub's trusted publishing** feature, which eliminates the need for API tokens. GitHub authenticates directly with PyPI using OpenID Connect (OIDC).

## One-Time Setup Steps

### 1. Push Code to GitHub

First, make sure your code is on GitHub at `https://github.com/rdwj/fips-agents-cli`:

```bash
cd /Users/wjackson/Developer/AGENTS/fips-agents-cli

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: fips-agents-cli v0.1.0"

# Add remote (if not already added)
git remote add origin https://github.com/rdwj/fips-agents-cli.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2. Configure PyPI Trusted Publishing

1. **Go to PyPI** (create account if needed): https://pypi.org/account/register/

2. **Navigate to Publishing Settings**:
   - Go to https://pypi.org/manage/account/publishing/
   - Or: Account → Publishing → Add a new pending publisher

3. **Add GitHub as Trusted Publisher**:
   - **PyPI Project Name**: `fips-agents-cli`
   - **Owner**: `rdwj`
   - **Repository name**: `fips-agents-cli`
   - **Workflow name**: `workflow.yaml`
   - **Environment name**: `pypi`

   Click "Add"

**Important**: You must configure trusted publishing BEFORE creating your first release. PyPI will create the project automatically on first publish.

### 3. Create GitHub Environment (Optional but Recommended)

This adds an extra approval step before publishing:

1. Go to your repository: https://github.com/rdwj/fips-agents-cli
2. Navigate to **Settings → Environments**
3. Click **New environment**
4. Name it: `pypi`
5. Configure protection rules:
   - ✅ **Required reviewers**: Add yourself or team members
   - ✅ **Wait timer**: Optional (e.g., 5 minutes)
   - ✅ **Deployment branches**: Only `main` branch

## Publishing a New Release

### Manual Release (Recommended)

1. **Update version** in `src/fips_agents_cli/version.py`:
   ```python
   __version__ = "0.1.1"  # Increment version
   ```

2. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Bump version to 0.1.1"
   git push
   ```

4. **Create a GitHub Release**:
   - Go to https://github.com/rdwj/fips-agents-cli/releases
   - Click **Draft a new release**
   - **Choose a tag**: Create new tag `v0.1.1`
   - **Release title**: `v0.1.1`
   - **Description**: Document changes (see below)
   - Click **Publish release**

5. **GitHub Actions will automatically**:
   - Run tests
   - Build the package
   - Publish to PyPI (if environment approval granted)

6. **Monitor the workflow**:
   - Go to https://github.com/rdwj/fips-agents-cli/actions
   - Watch the "Publish to PyPI" workflow

### Release Description Template

```markdown
## What's New in v0.1.1

### Features
- Added new command: `fips-agents generate tool`
- Support for custom template directories

### Bug Fixes
- Fixed project name validation regex
- Resolved git initialization errors on Windows

### Documentation
- Updated README with new examples
- Added troubleshooting guide

## Installation

```bash
pipx install fips-agents-cli==0.1.1
```

## Full Changelog
See: https://github.com/rdwj/fips-agents-cli/compare/v0.1.0...v0.1.1
```

## Verifying Publication

After the workflow completes:

1. **Check PyPI**: https://pypi.org/project/fips-agents-cli/
2. **Test installation**:
   ```bash
   pipx install fips-agents-cli
   fips-agents --version
   ```

3. **Test functionality**:
   ```bash
   fips-agents create mcp-server test-server
   ```

## Troubleshooting

### Workflow Fails: "Trusted publishing authentication error"

**Cause**: PyPI trusted publisher not configured correctly.

**Fix**:
1. Verify settings at https://pypi.org/manage/account/publishing/
2. Ensure all fields match exactly:
   - Owner: `rdwj`
   - Repository: `fips-agents-cli`
   - Workflow: `workflow.yaml`
   - Environment: `pypi`

### Workflow Fails: "Environment protection rules"

**Cause**: Waiting for manual approval.

**Fix**:
1. Go to Actions → Workflow run
2. Click "Review deployments"
3. Approve the deployment to `pypi`

### Package Already Exists on PyPI

**Cause**: Version already published.

**Fix**: You cannot re-publish the same version. Increment the version number.

### Workflow Doesn't Trigger

**Cause**: Workflow only triggers on **published releases**, not drafts.

**Fix**: Make sure you clicked "Publish release", not "Save draft".

## Manual Upload (Emergency Fallback)

If trusted publishing fails, you can manually upload:

```bash
# Build package
python -m build

# Upload with token
pip install twine
twine upload dist/*
```

You'll need to:
1. Create API token at https://pypi.org/manage/account/token/
2. Use `__token__` as username
3. Use token (starts with `pypi-`) as password

## Best Practices

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

### Release Checklist

Before creating a release:
- [ ] All tests passing locally (`pytest`)
- [ ] Code formatted (`black src tests`)
- [ ] Linting passes (`ruff check src tests`)
- [ ] Version bumped in both files
- [ ] CHANGELOG updated (or release notes prepared)
- [ ] Documentation updated if needed
- [ ] GitHub Actions tests passing on main branch

### Testing Before Release

Test the package locally before releasing:

```bash
# Build locally
python -m build

# Install in fresh environment
cd /tmp
python -m venv test_env
source test_env/bin/activate
pip install /path/to/fips-agents-cli/dist/fips_agents_cli-0.1.1-py3-none-any.whl
fips-agents --version
fips-agents create mcp-server test-project
```

## GitHub Actions Workflows

### `workflow.yaml`
- **Trigger**: On release published
- **Purpose**: Build and publish to PyPI
- **Permissions**: `id-token: write` for trusted publishing

### `test.yml`
- **Trigger**: On push to main, on pull requests
- **Purpose**: Run tests, linting, and build checks
- **Python versions**: 3.9, 3.10, 3.11, 3.12

## Security Notes

- ✅ No API tokens stored in repository
- ✅ GitHub authenticates directly with PyPI via OIDC
- ✅ Workflow runs in isolated environment
- ✅ Environment protection rules add approval step
- ✅ Only maintainers can create releases

## Additional Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)

## Support

For issues with publishing:
- **PyPI Support**: https://pypi.org/help/
- **GitHub Actions**: https://github.com/rdwj/fips-agents-cli/actions
- **Repository Issues**: https://github.com/rdwj/fips-agents-cli/issues
