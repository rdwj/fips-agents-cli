# Quick Start: Publishing fips-agents-cli to PyPI

## Prerequisites
- [x] GitHub repository: https://github.com/rdwj/fips-agents-cli
- [x] PyPI account (create at https://pypi.org/account/register/)
- [x] Package built and tested locally

## Step-by-Step Guide

### 1. Push to GitHub (5 minutes)

```bash
cd /Users/wjackson/Developer/AGENTS/fips-agents-cli

# If not already initialized
git init
git add .
git commit -m "Initial commit: fips-agents-cli v0.1.0"

# Add remote and push
git remote add origin https://github.com/rdwj/fips-agents-cli.git
git branch -M main
git push -u origin main
```

### 2. Configure PyPI Trusted Publishing (3 minutes)

1. Go to: https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name**: `fips-agents-cli`
   - **Owner**: `rdwj`
   - **Repository name**: `fips-agents-cli`
   - **Workflow name**: `workflow.yaml`
   - **Environment name**: `pypi`
4. Click "Add"

**Screenshot guide**: See PUBLISHING.md for detailed screenshots

### 3. (Optional) Set up GitHub Environment

For added security, create an environment that requires approval:

1. Go to: https://github.com/rdwj/fips-agents-cli/settings/environments
2. Click "New environment"
3. Name: `pypi`
4. Add yourself as required reviewer
5. Save

### 4. Create Your First Release (2 minutes)

1. Go to: https://github.com/rdwj/fips-agents-cli/releases
2. Click "Draft a new release"
3. Click "Choose a tag" → Type `v0.1.0` → Click "Create new tag: v0.1.0 on publish"
4. Release title: `v0.1.0 - Initial Release`
5. Description:
   ```markdown
   ## 🎉 Initial Release

   First public release of fips-agents-cli!

   ### Features
   - Create MCP server projects from templates
   - Git integration
   - Beautiful CLI with Rich output
   - Comprehensive test suite

   ### Installation
   ```bash
   pipx install fips-agents-cli
   ```

   ### Usage
   ```bash
   fips-agents create mcp-server my-server
   ```
   ```
6. Click "Publish release"

### 5. Monitor the Workflow (2 minutes)

1. Go to: https://github.com/rdwj/fips-agents-cli/actions
2. Click on the "Publish to PyPI" workflow
3. Watch it run:
   - Build distribution → Should complete in ~1 minute
   - Publish to PyPI → May wait for approval if environment configured
4. If approval required:
   - Click "Review deployments"
   - Check "pypi"
   - Click "Approve and deploy"

### 6. Verify Publication (1 minute)

```bash
# Check PyPI
open https://pypi.org/project/fips-agents-cli/

# Test installation
pipx install fips-agents-cli

# Verify it works
fips-agents --version
fips-agents create mcp-server test-project
```

## That's It!

Total time: ~10-15 minutes

Your package is now live on PyPI and anyone can install it with:
```bash
pipx install fips-agents-cli
```

## For Future Releases

1. Update version in `src/fips_agents_cli/version.py` and `pyproject.toml`
2. Commit and push changes
3. Create new GitHub release with new tag (e.g., `v0.1.1`)
4. Workflow automatically publishes to PyPI

## Troubleshooting

### "Trusted publishing authentication error"
- Double-check PyPI settings match exactly
- Make sure you completed Step 2 BEFORE creating the release

### "Waiting for approval"
- Go to Actions → Click workflow → "Review deployments" → Approve

### "Version already exists"
- You can't republish the same version
- Bump version number and create new release

## Need Help?

- **Detailed guide**: See PUBLISHING.md
- **GitHub Actions**: https://github.com/rdwj/fips-agents-cli/actions
- **PyPI project**: https://pypi.org/project/fips-agents-cli/
- **Issues**: https://github.com/rdwj/fips-agents-cli/issues
