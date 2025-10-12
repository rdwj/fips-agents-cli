# Release Scripts

This directory contains automation scripts for the fips-agents-cli project.

## release.sh

Automated release script that handles version bumping, tagging, and triggering the release pipeline.

### Usage

```bash
./scripts/release.sh <version> "<commit-message>"
```

### Arguments

- `version`: Version number in format x.y.z (e.g., 0.1.2)
- `commit-message`: Short description of the release changes

### Example

```bash
./scripts/release.sh 0.1.2 "Add middleware generation support"
```

### What It Does

1. **Validates** version format and checks for uncommitted changes
2. **Updates** version numbers in:
   - `src/fips_agents_cli/version.py`
   - `pyproject.toml`
3. **Verifies** both files have matching versions
4. **Commits** changes including README.md (changelog)
5. **Pushes** to main branch
6. **Creates** and pushes version tag (e.g., `v0.1.2`)
7. **Triggers** GitHub Actions workflow for:
   - Creating GitHub Release
   - Building distribution packages
   - Publishing to PyPI

### Prerequisites

- Must be run from project root directory
- Working directory should be clean (no uncommitted changes except version files)
- Git remote configured for push access
- PyPI Trusted Publishing configured on GitHub

### Recommended Usage

Use the `/create-release` slash command in Claude Code, which will:
1. Ask for version and release notes
2. Update changelog in README.md
3. Call this script automatically

### Manual Usage

If you prefer to run manually:

```bash
# 1. Update changelog in README.md first
# 2. Run the script
./scripts/release.sh 0.1.2 "Brief description of changes"
# 3. Monitor GitHub Actions
```

### Error Handling

The script will exit with an error if:
- Version format is invalid
- Not run from project root
- Uncommitted changes exist (excluding version files and README)
- Version verification fails
- Git operations fail

### Success Output

On success, you'll see:
- Green checkmarks for each step
- Links to monitor GitHub Actions
- Link to view the release

### Monitoring

After running the script, monitor:
- GitHub Actions: https://github.com/rdwj/fips-agents-cli/actions
- Releases: https://github.com/rdwj/fips-agents-cli/releases
- PyPI: https://pypi.org/project/fips-agents-cli/

The entire release process typically takes 1-2 minutes.
