# Release Checklist

This document outlines the manual and automated steps for releasing a new version of fips-agents-cli.

## Automated Release Process (Recommended)

With GitHub Actions configured, releases are fully automated via version tags:

### 1. Prepare Release

```bash
# 1. Update version number
# Edit: src/fips_agents_cli/version.py
__version__ = "0.1.2"  # Increment version

# 2. Update changelog
# Edit: README.md under ## Changelog section
# Add new version section:
### Version 0.1.2
- Feature: Description
- Fix: Description

# 3. Commit changes
git add src/fips_agents_cli/version.py README.md
git commit -m "Bump version to 0.1.2"
git push origin main
```

### 2. Tag and Push

```bash
# Create and push version tag
git tag v0.1.2
git push origin v0.1.2
```

**GitHub Actions will automatically:**
1. Verify tag version matches `version.py`
2. Extract changelog from README.md
3. Create GitHub Release with release notes
4. Build distribution packages
5. Publish to PyPI (using trusted publishing)

### 3. Verify Release

1. Check GitHub Actions: https://github.com/rdwj/fips-agents-cli/actions
2. Verify GitHub Release: https://github.com/rdwj/fips-agents-cli/releases
3. Verify on PyPI: https://pypi.org/project/fips-agents-cli/
4. Test installation:
   ```bash
   pip install --upgrade fips-agents-cli
   fips-agents --version
   ```

---

## Manual Release Process (Fallback)

If automated release fails or you need to release manually:

### 1. Prepare Release

```bash
# 1. Ensure working directory is clean
git status

# 2. Update version
# Edit: src/fips_agents_cli/version.py
__version__ = "0.1.2"

# 3. Update changelog
# Edit: README.md

# 4. Commit changes
git add src/fips_agents_cli/version.py README.md
git commit -m "Bump version to 0.1.2"
git push origin main
```

### 2. Run Tests

```bash
# Run full test suite
pytest

# Check code quality
black src tests --check
ruff check src tests

# Verify all tests pass before proceeding
```

### 3. Clean Build Artifacts

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info src/*.egg-info
```

### 4. Build Distribution Packages

```bash
# Build wheel and source distribution
python -m build
```

This creates:
- `dist/fips_agents_cli-0.1.2-py3-none-any.whl`
- `dist/fips_agents_cli-0.1.2.tar.gz`

### 5. Verify Build

```bash
# Check packages are valid
twine check dist/*

# Should output:
# Checking dist/fips_agents_cli-0.1.2-py3-none-any.whl: PASSED
# Checking dist/fips_agents_cli-0.1.2.tar.gz: PASSED
```

### 6. Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Enter credentials when prompted (or use token)
```

### 7. Create Git Tag

```bash
# Create and push tag
git tag -a v0.1.2 -m "Release version 0.1.2"
git push origin v0.1.2
```

### 8. Create GitHub Release

1. Go to: https://github.com/rdwj/fips-agents-cli/releases/new
2. Select tag: `v0.1.2`
3. Set release title: `v0.1.2`
4. Add release notes from changelog
5. Attach distribution files (optional):
   - `dist/fips_agents_cli-0.1.2-py3-none-any.whl`
   - `dist/fips_agents_cli-0.1.2.tar.gz`
6. Click "Publish release"

### 9. Verify Release

```bash
# Test installation from PyPI
pip install --upgrade fips-agents-cli

# Verify version
fips-agents --version
# Should output: fips-agents, version 0.1.2

# Run basic smoke test
fips-agents --help
```

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **Major (1.0.0)**: Breaking changes
- **Minor (0.1.0)**: New features, backward compatible
- **Patch (0.1.1)**: Bug fixes, backward compatible

### Examples:
- `0.1.0` → `0.1.1`: Bug fixes only
- `0.1.0` → `0.2.0`: New features added
- `0.9.0` → `1.0.0`: First stable release or breaking changes

---

## Pre-release Checklist

Before any release:

- [ ] All tests pass locally: `pytest`
- [ ] Code is formatted: `black src tests`
- [ ] No linting errors: `ruff check src tests`
- [ ] Version updated in `src/fips_agents_cli/version.py`
- [ ] Changelog updated in `README.md`
- [ ] Documentation is current
- [ ] No uncommitted changes: `git status`
- [ ] On main branch: `git branch`

---

## Post-release Checklist

After release:

- [ ] GitHub release created with tag
- [ ] PyPI package updated: https://pypi.org/project/fips-agents-cli/
- [ ] GitHub Actions succeeded (if using automated release)
- [ ] Installation tested: `pip install --upgrade fips-agents-cli`
- [ ] Version verified: `fips-agents --version`
- [ ] Basic functionality tested
- [ ] Consider announcing release (if major)

---

## Troubleshooting

### "File already exists" on PyPI

**Cause**: Trying to re-upload same version.

**Solution**: PyPI doesn't allow re-uploading. Increment version and rebuild:
```bash
# Update version.py
# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*
```

### Build fails

**Cause**: Missing dependencies or invalid package structure.

**Solution**:
```bash
# Install build dependencies
pip install --upgrade build twine

# Verify pyproject.toml is valid
python -m build --help
```

### Tests fail

**Cause**: Code issues or environment problems.

**Solution**:
```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests with verbose output
pytest -v

# Check specific failing test
pytest tests/test_specific.py::test_name -v
```

### GitHub Actions fail

**Cause**: Various reasons - check workflow logs.

**Solution**:
1. Go to Actions tab: https://github.com/rdwj/fips-agents-cli/actions
2. Click failed workflow run
3. Check logs for error details
4. Fix issue and push again or re-run workflow

### PyPI upload authentication fails

**Cause**: Invalid credentials or token.

**Solution**:
- Use API token instead of password
- Create token at: https://pypi.org/manage/account/token/
- Configure in `~/.pypirc` or use `twine upload --username __token__ --password <token>`
- For GitHub Actions, configure as repository secret

---

## GitHub Actions Setup

See `.github/workflows/` directory for:
- `ci.yml` - Runs tests on every push/PR
- `release.yml` - Builds and publishes on GitHub release

### Required GitHub Secrets

For automated PyPI publishing:
- `PYPI_API_TOKEN` - PyPI API token

Or use PyPI Trusted Publishing (recommended):
- No secrets needed
- Configure at: https://pypi.org/manage/project/fips-agents-cli/settings/publishing/

---

## Quick Reference

```bash
# Automated release (preferred)
# 1. Update version in version.py
# 2. Update changelog in README.md
# 3. Commit and push to main
git add src/fips_agents_cli/version.py README.md
git commit -m "Bump version to 0.1.x"
git push origin main
# 4. Create and push tag
git tag v0.1.x
git push origin v0.1.x
# 5. GitHub Actions handles the rest (release creation + PyPI publishing)

# Manual release
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*
twine upload dist/*
git tag -a v0.1.x -m "Release version 0.1.x"
git push origin v0.1.x

# Verify
pip install --upgrade fips-agents-cli
fips-agents --version
```
