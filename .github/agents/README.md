# GitHub Copilot Custom Agents

This directory contains custom agents for GitHub Copilot in VS Code to help with fips-agents-cli development.

## Requirements

- VS Code version 1.106 or later
- GitHub Copilot extension installed and activated
- GitHub Copilot Chat enabled

## Available Agents

### @create-release

**Purpose:** Automate the release process for fips-agents-cli

**Usage:**
```
@create-release I want to release version 0.1.3
```

**What it does:**
1. Prompts you for version number and release notes
2. Updates the changelog in README.md
3. Runs the release script to update version files
4. Creates git tags and triggers PyPI publishing via GitHub Actions

**Example conversation:**
```
You: @create-release prepare version 0.1.3
Agent: What changes are included in version 0.1.3?
You: Added new generator commands and fixed authentication bugs
Agent: [Updates changelog and runs release script]
```

## How to Use Custom Agents

1. **Open GitHub Copilot Chat** in VS Code (Ctrl+Alt+I or Cmd+Alt+I)

2. **Invoke an agent** by typing `@` followed by the agent name:
   - `@create-release` - For release management

3. **Provide context** in your message after the agent name

4. **Follow the agent's prompts** to complete the workflow

## Agent Configuration

Custom agents are defined in `.agent.md` files with:
- **YAML frontmatter** for metadata and configuration
- **Markdown body** for instructions and guidelines

### Adding New Agents

To create a new custom agent:

1. Create a new file: `.github/agents/your-agent-name.agent.md`

2. Add YAML frontmatter:
   ```yaml
   ---
   name: your-agent-name
   description: Brief description
   tools:
     - vscode-files
     - vscode-terminal
   target: vscode
   ---
   ```

3. Add markdown instructions for the agent's behavior

4. Agents are automatically discovered by VS Code

## Troubleshooting

**Agent not showing up?**
- Ensure VS Code is version 1.106+
- Reload VS Code window (Cmd+Shift+P → "Reload Window")
- Check that GitHub Copilot is active

**Agent not working correctly?**
- Verify the `.agent.md` file has valid YAML frontmatter
- Check VS Code Developer Tools for errors (Help → Toggle Developer Tools)

## Equivalent Claude Code Commands

If you're using Claude Code instead of GitHub Copilot, use these slash commands:

| Copilot Agent | Claude Code Command | Description |
|--------------|---------------------|-------------|
| `@create-release` | `/create-release` | Prepare and publish a release |

Both provide similar functionality but use different invocation methods.

## Documentation

- [VS Code Copilot Custom Agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/overview)
