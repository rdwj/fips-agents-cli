---
description: Prepare and publish a new release version
tags: [release, publish, version]
---

You are assisting with creating a new release for the fips-agents-cli project.

## Your Task

1. **Ask the user for release information:**
   - New version number (format: x.y.z, e.g., 0.1.2)
   - Release notes/description of changes

2. **Update the README.md changelog:**
   - Read the current README.md file
   - Add a new version section under the `## Changelog` heading
   - Format as:
     ```markdown
     ### Version X.Y.Z

     - Feature/Fix: Description of change
     - Feature/Fix: Description of change
     ```
   - Place the new version ABOVE older versions (newest first)
   - Use the release notes provided by the user to populate the changelog

3. **Run the release script:**
   - After updating the changelog, run the release script:
     ```bash
     ./scripts/release.sh <version> "<commit-message>"
     ```
   - The commit message should be a concise summary of the release (e.g., "Add generator commands")

## Important Notes

- The release script will:
  - Update version in `version.py` and `pyproject.toml`
  - Commit all changes (including the changelog you updated)
  - Create and push a git tag
  - Trigger automated GitHub Actions for PyPI publishing

- Version format must be x.y.z (three numbers separated by dots)
- Follow semantic versioning:
  - Major (1.0.0): Breaking changes
  - Minor (0.1.0): New features, backward compatible
  - Patch (0.1.1): Bug fixes, backward compatible

- The changelog should be clear and user-focused
- Group related changes together
- Use consistent formatting

## Example Interaction

User: "I want to release version 0.1.2"

You should:
1. Ask: "What changes are included in version 0.1.2? Please describe the new features, fixes, or improvements."
2. User provides: "Added support for middleware generation, fixed bug in tool validation, improved error messages"
3. You update README.md changelog:
   ```markdown
   ### Version 0.1.2

   - Feature: Added support for middleware generation
   - Fix: Fixed bug in tool validation
   - Improvement: Improved error messages
   ```
4. You run: `./scripts/release.sh 0.1.2 "Add middleware generation support"`
5. Confirm success and provide links to monitor the release

## Validation

Before running the script, verify:
- Version number is in correct format (x.y.z)
- Changelog is properly formatted
- User has confirmed the changes are ready to release
