# Ignite CLI Architecture Analysis

**Research Date:** October 11, 2025
**Project:** Infinite Red's Ignite CLI (React Native Boilerplate)
**Repository:** https://github.com/infinitered/ignite
**Purpose:** Understanding CLI modality and approach for building similar tooling

---

## Executive Summary

Ignite CLI is a battle-tested React Native project boilerplate and CLI tool that has been continuously developed since 2016 with over 2,000 commits. It demonstrates a mature approach to CLI-based project scaffolding that saves developers an estimated 2-4 weeks of setup time per project.

**Key Architectural Decisions:**
- Built on **Gluegun** framework (a TypeScript-powered CLI toolkit from Infinite Red)
- Distributed via **NPM** with `npx` for zero-installation execution
- Uses **EJS templating** for code generation
- Employs **semantic-release** for automated versioning and publishing
- Provides both **interactive** and **non-interactive** workflows
- Templates are **copied into projects** for easy customization
- Designed for **extension** with custom generators

**Critical Success Factors:**
1. Zero-installation experience via `npx`
2. Flexible workflow (interactive prompts vs CLI flags)
3. Comprehensive, opinionated boilerplate
4. Easy-to-customize generators
5. Excellent documentation and community support
6. Mature testing strategy (integration tests on generated code)

---

## 1. Installation & Distribution Analysis

### Distribution Strategy

**Primary Distribution Method:**
```bash
# Zero-installation via npx (recommended)
npx ignite-cli@latest new PizzaApp

# Can also be installed globally (not recommended)
npm install -g ignite-cli
```

**Key Insights:**
- Uses **npx** as the primary distribution mechanism, avoiding global installation conflicts
- Published to NPM as `ignite-cli` package
- Uses semantic versioning with automated releases
- Maintains backward compatibility across versions

### Package Structure

**Package.json Highlights:**
```json
{
  "name": "ignite-cli",
  "version": "11.3.2",
  "description": "Infinite Red's hottest boilerplate for React Native",
  "bin": {
    "ignite": "bin/ignite",
    "ignite-cli": "bin/ignite"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

**System Requirements:**
- Node.js ≥20.0.0
- React Native development environment
- Xcode command line tools (macOS)
- Platform-specific mobile development tools

**Dependencies:**
- **gluegun**: CLI framework foundation
- **ejs**: Template rendering
- **sharp**: Image processing (for app icons)
- **yaml**: Configuration parsing
- **deepmerge-json**: Configuration merging
- **cross-spawn**: Cross-platform process spawning

**Development Dependencies:**
- TypeScript
- Jest (testing)
- ESLint & Prettier (code quality)
- semantic-release (automated publishing)

### Build & Release Process

**Build Process:**
1. TypeScript compilation (`tsc`) from `src/` to `build/`
2. Excludes boilerplate, templates, and test files from compilation
3. Generates source maps for debugging

**Release Strategy:**
- Uses **semantic-release** for automated versioning
- Commit message conventions determine version bumps
- Automated NPM publishing on successful CI builds
- Manual beta releases supported

**Translation to Python Ecosystem:**
- Use `pyproject.toml` instead of package.json
- Publish to PyPI instead of NPM
- Use `pipx` (Python equivalent of npx) for zero-installation
- Entry points in `pyproject.toml` map to CLI commands
- Consider `poetry` or `hatch` for build tooling

---

## 2. CLI Command Structure

### Command Hierarchy

Ignite CLI provides a focused set of commands organized around workflow stages:

```
ignite-cli
├── new [ProjectName]           # Create new project
├── generate (alias: g)          # Generate code artifacts
├── cache                        # Manage dependency cache
│   ├── path                    # Show cache location
│   └── clear                   # Clear cache
├── doctor                       # Check development environment
├── remove-demo-markup (rdm)     # Remove demo code
├── issue (alias: i)             # Open GitHub issue
├── help (alias: h)              # Display help
└── update                       # Update generators
```

### Command Syntax Patterns

**1. Primary Command: `new`**
```bash
npx ignite-cli new [ProjectName] [OPTIONS]

Options:
  --bundle <identifier>    Custom bundle identifier
  --debug                  Verbose logging
  --git                    Initialize git with commit
  --installDeps            Run package install
  --overwrite              Overwrite existing directory
  --targetPath <path>      Specify creation directory
  --removeDemo             Remove demo code
  --useCache               Use dependency cache
  --no-timeout             Disable timeout protection
  --yes                    Accept all defaults (non-interactive)
  --workflow <type>        Choose initialization method
  --experimental           Enable experimental features
```

**2. Generator Commands:**
```bash
npx ignite-cli generate <type> <name> [OPTIONS]

Types:
  component <Name>         Create component
  screen <Name>            Create screen component
  navigator <Name>         Create React Navigation navigator
  app-icon <platform>      Generate app icons
  splash-screen <color>    Generate splash screens

Options:
  --case <style>           Filename casing (pascal|camel|snake|kebab)
  --dir <path>             Output directory
```

**3. Utility Commands:**
```bash
npx ignite-cli doctor              # Environment diagnostics
npx ignite-cli cache clear         # Clear dependency cache
npx ignite-cli remove-demo-markup  # Strip demo code
npx ignite-cli update <type>       # Update generator templates
npx ignite-cli update --all        # Update all generators
```

### Command Design Patterns

**Key Observations:**
1. **Hierarchical structure** with subcommands (e.g., `cache path`, `cache clear`)
2. **Aliases** for frequently used commands (`g` for `generate`, `i` for `issue`)
3. **Flag-based configuration** with sensible defaults
4. **Escape hatch options** (e.g., `--yes` for CI/CD, `--debug` for troubleshooting)
5. **Contextual help** available at all levels

**Translation to Python:**
- Use `click` or `typer` for command hierarchy
- `click.group()` for command groups
- `click.command()` for individual commands
- Context objects for shared state (similar to Gluegun's toolbox)

---

## 3. Project Scaffolding Approach

### Scaffolding Philosophy

Ignite takes a **comprehensive boilerplate** approach rather than minimal scaffolding:

- Provides a **fully functional React Native app** with demo code
- Includes **production-ready patterns** and best practices
- **Pre-configures** testing, navigation, theming, i18n
- Offers **removal tools** to strip demo code when ready

### Generated Project Structure

```
my-app/
├── .maestro/                    # E2E test scripts
├── android/                     # Android native code
├── ios/                         # iOS native code
├── app/                         # Main application code
│   ├── components/             # Reusable UI components
│   ├── config/                 # Environment configuration
│   ├── devtools/               # Development tools (Reactotron)
│   ├── i18n/                   # Internationalization
│   ├── context/                # React Context providers
│   ├── models/                 # State management (MobX)
│   ├── navigators/             # React Navigation setup
│   ├── screens/                # Screen components
│   ├── services/               # API clients, external services
│   ├── theme/                  # Colors, spacing, typography
│   ├── utils/                  # Helper functions
│   └── app.tsx                 # Application entry point
├── assets/                      # Images, fonts, etc.
│   ├── fonts/
│   └── images/
├── ignite/                      # Generator templates
│   └── templates/
│       ├── component/
│       ├── screen/
│       ├── navigator/
│       └── ...
├── test/                        # Test configuration
│   ├── i18n.test.ts
│   ├── mockFile.ts
│   └── setup.ts
├── app.config.ts                # Expo/app configuration
├── app.json                     # Static app configuration
├── package.json
├── tsconfig.json
└── README.md
```

### Technology Stack Decisions

**Included by Default:**
- **React Native v0.79** (latest stable)
- **TypeScript v5** (type safety)
- **React Navigation v7** (routing)
- **Expo SDK** (optional, but supported)
- **MMKV** (fast storage)
- **Apisauce** (API client wrapper around Axios)
- **i18n-js** (internationalization)
- **Reactotron** (debugging)

**Testing Stack:**
- **Jest** (unit testing)
- **React Native Testing Library** (component testing)
- **Maestro** (E2E testing)

### Configuration Management

**Primary Configuration Files:**

1. **app.json** (static configuration)
   - App name, version
   - Platform-specific settings
   - Expo configuration

2. **app.config.ts** (dynamic configuration)
   - Builds final configuration at runtime
   - Merges app.json with dynamic values
   - Environment-specific settings

3. **Ignite-specific files:**
   - Generator templates in `./ignite/templates/`
   - Customizable after project creation

**Key Insight:** Configuration is **copied into the project**, not kept in the CLI tool. This allows teams to customize without needing to maintain a forked CLI.

---

## 4. Generator & Plugin Architecture

### Generator System Design

**Core Concept:** Generators are **EJS templates** that create code artifacts with consistent patterns.

**Generator Location:**
- Stored in `./ignite/templates/*` within each project
- Copied during project initialization
- **Fully customizable** by project teams

### Built-in Generators

**1. Component Generator**
```bash
npx ignite-cli generate component MyButton
```
Creates: `app/components/MyButton.tsx`

**2. Screen Generator**
```bash
npx ignite-cli generate screen Settings
```
Creates: `app/screens/SettingsScreen.tsx` with navigation setup

**3. Navigator Generator**
```bash
npx ignite-cli generate navigator OrderPizza
```
Creates: `app/navigators/OrderPizzaNavigator.tsx`

**4. App Icon Generator**
```bash
npx ignite-cli generate app-icon ios
```
Generates multi-resolution icons for iOS, Android, and Web

**5. Splash Screen Generator**
```bash
npx ignite-cli generate splash-screen FF0000
```
Configures platform-specific splash screens with color parameter

### Template System (EJS)

**Template File Structure:**
```
./ignite/templates/component/
├── NAME.tsx.ejs              # Template file
└── NAME.test.tsx.ejs         # Test template
```

**Template Example:**
```ejs
---
destinationDir: app/components
---
type <%= props.pascalCaseName %>Props = {
  text: string
}

export function <%= props.pascalCaseName %>(props: <%= props.pascalCaseName %>Props) {
  const { text } = props
  return <Text>{text}</Text>
}
```

**Available Template Props:**
- `props.filename` - Generated filename
- `props.pascalCaseName` - PascalCase version of input
- `props.camelCaseName` - camelCase version
- `props.kebabCaseName` - kebab-case version
- `props.subdirectory` - Target directory path

**Front Matter Features:**
```ejs
---
destinationDir: app/screens
patch: app/navigators/AppNavigator.tsx
---
```
- `destinationDir`: Override default output location
- `patch`: Modify existing files (e.g., register new screen in navigator)

### Extensibility Model

**Creating Custom Generators:**

1. Add template directory: `./ignite/templates/my-generator/`
2. Create `.ejs` template files
3. Use EJS syntax for dynamic content
4. Run: `npx ignite-cli generate my-generator MyName`

**Updating Generators:**
```bash
npx ignite-cli update component     # Update specific generator
npx ignite-cli update --all         # Update all generators
```

**Warning:** Updates overwrite customizations. Teams often fork templates.

### Key Architectural Insights

1. **Templates live in projects**, not in the CLI tool
   - Enables project-specific conventions
   - Teams can customize without CLI changes
   - Version control tracks template changes

2. **Simple templating** (EJS, not complex AST manipulation)
   - Easy for developers to understand and modify
   - Trade-off: Less sophisticated code insertion

3. **Convention-based naming**
   - Uppercase `NAME` in filenames gets replaced
   - Consistent casing transformations

4. **File patching capability**
   - Can modify existing files (e.g., add imports)
   - Limited but sufficient for most use cases

**Translation to Python:**
- Use **Jinja2** instead of EJS (more Pythonic, similar features)
- Store templates in project `.cli/templates/` or similar
- Use **YAML front matter** (per user preferences from CLAUDE.md)
- Consider **LibCST** for more sophisticated code patching

---

## 5. Configuration Management

### Configuration Philosophy

Ignite uses a **layered configuration** approach:

1. **CLI flags** (highest priority)
2. **Interactive prompts** (if flags not provided)
3. **Default values** (sensible defaults)
4. **Project configuration** (app.json, app.config.ts)

### CLI Configuration

**Command-Line Options:**
- Passed as flags: `--bundle com.mycompany.myapp`
- Boolean flags: `--debug`, `--git`, `--removeDemo`
- Accept-all shortcut: `--yes`

**Interactive Prompts:**
- Triggered when options not provided
- Uses **enquirer** (via Gluegun) for rich prompts
- Validates input
- Provides helpful descriptions

### Project Configuration Files

**1. app.json** (Static Configuration)
```json
{
  "name": "PizzaApp",
  "displayName": "PizzaApp",
  "expo": {
    "name": "PizzaApp",
    "slug": "pizzaapp",
    "version": "1.0.0",
    "icon": "./assets/images/icon.png",
    "splash": {
      "image": "./assets/images/splash.png"
    }
  }
}
```

**2. app.config.ts** (Dynamic Configuration)
```typescript
import { ExpoConfig } from "expo/config"

const config: ExpoConfig = {
  ...require("./app.json").expo,
  // Dynamic overrides here
  extra: {
    apiUrl: process.env.API_URL
  }
}

export default config
```

**3. Generator Configuration**
- Templates in `./ignite/templates/`
- No separate generator config file
- Configuration embedded in template front matter

### Cache Management

**Dependency Cache:**
```bash
npx ignite-cli cache path         # Show cache location
npx ignite-cli cache clear        # Clear cache
npx ignite-cli new App --useCache # Use cached dependencies
```

**Purpose:**
- Speeds up project creation
- Reduces network calls
- Useful for CI/CD environments

### Environment Detection

**Development vs Production:**
- CLI detects execution mode
- Uses **ts-node** in dev mode (no build required)
- Uses compiled JavaScript in production

**Debugging Mode:**
```bash
npx ignite-cli new MyApp --debug
```
- Verbose logging
- Shows detailed error messages
- Helps troubleshoot issues

### Key Configuration Insights

1. **Progressive disclosure:** Defaults → Prompts → Flags
2. **No global config file** (unlike many CLIs)
3. **Project-owned configuration** (not CLI-owned)
4. **Environment-aware** (dev vs prod, CI detection)
5. **Cache for performance** (optional but useful)

**Translation to Python:**
- Use **click.prompt()** or **questionary** for interactive prompts
- Store config in `pyproject.toml` or custom YAML
- Support environment variable overrides
- Use **appdirs** for platform-appropriate cache locations
- Implement **--verbose** instead of `--debug`

---

## 6. User Workflow & Experience

### Primary User Journeys

**1. Quick Start Journey (Experienced Users)**
```bash
# One command, zero interaction
npx ignite-cli@latest new PizzaApp --yes
cd PizzaApp
npm run ios
```

**Time to first run:** ~5 minutes (including dependency installation)

**2. Interactive Journey (New Users)**
```bash
npx ignite-cli@latest new PizzaApp

# CLI walks through:
# - Project name confirmation
# - Package manager selection (npm, yarn, pnpm, bun)
# - Navigation library options
# - State management options
# - Demo code inclusion
# - Git initialization
# - Dependency installation
```

**3. Iterative Development Journey**
```bash
# Generate components as needed
npx ignite-cli generate component Button
npx ignite-cli generate screen Profile
npx ignite-cli generate navigator Settings

# Customize generators
vim ignite/templates/component/NAME.tsx.ejs

# Remove demo code when ready
npx ignite-cli remove-demo-markup
```

### Interactive Prompt Design

**Prompt Characteristics:**
- **Helpful descriptions** explain each option
- **Sensible defaults** highlighted
- **Keyboard navigation** (arrow keys, enter)
- **Validation** prevents invalid input
- **Skippable** with flags for automation

**Example Prompt Flow:**
```
? What do you want to name your project? (PizzaApp)
? Which package manager do you want to use?
  ❯ npm
    yarn
    pnpm
    bun
? Do you want to initialize a git repository? (Y/n)
? Remove demo code and markup? (y/N)
```

### Error Handling & User Feedback

**Diagnostic Tools:**
```bash
# Environment check
npx ignite-cli doctor

# Output: Shows Node version, React Native setup, missing dependencies
```

**Issue Reporting:**
```bash
# Pre-filled GitHub issue
npx ignite-cli issue "Error during project creation"
```

**Error Message Patterns:**
- Clear, actionable error messages
- Suggestions for resolution
- Links to documentation
- Debug mode for detailed output

**Example Error:**
```
❌ Error: Node.js version 18.0.0 detected
✓ Solution: Upgrade to Node.js ≥20.0.0
📖 Docs: https://nodejs.org/en/download
```

### Help System

**Multi-level Help:**
```bash
npx ignite-cli help              # Command list
npx ignite-cli new --help        # Command-specific help
npx ignite-cli generate --help   # Generator help
```

**Documentation Strategy:**
- Comprehensive docs site: https://docs.infinite.red/ignite-cli/
- In-CLI help text
- GitHub README with quick start
- Community Slack for support

### Visual Feedback

**Uses Ora (via Gluegun) for spinners:**
```
⠋ Installing dependencies...
✓ Dependencies installed
⠹ Configuring project...
✓ Project configured
🎉 Project created successfully!
```

**Color-coded output:**
- **Green** (success): ✓ Completed
- **Yellow** (warning): ⚠ Warning message
- **Red** (error): ✗ Failed
- **Blue** (info): ℹ Information

### Performance Considerations

**Speed Optimizations:**
- Dependency caching
- Lazy-loading of CLI commands
- Parallel file operations
- Skip unnecessary steps with flags

**User Perception:**
- Progress indicators
- Time estimates (where appropriate)
- Streaming output (not waiting for completion)

### Key UX Insights

1. **Zero friction start:** `npx` eliminates installation
2. **Progressive complexity:** Simple by default, powerful with flags
3. **Escape hatches:** Can skip any step with appropriate flags
4. **Helpful, not annoying:** Prompts have good defaults
5. **Fast feedback:** Spinners, colors, clear messaging
6. **Recovery paths:** Doctor command, issue templates
7. **Documentation-first:** Every feature well-documented

**Translation to Python:**
- Use **rich** library for beautiful terminal output
- Use **yaspin** for spinners
- Use **questionary** for interactive prompts
- Implement `--quiet` flag for CI environments
- Add `check` command equivalent to `doctor`
- Provide issue template generation

---

## 7. Key Architectural Patterns

### Gluegun Framework Architecture

**Foundation:** Ignite is built on **Gluegun**, a CLI toolkit from Infinite Red.

**Gluegun's "Toolbox" Pattern:**
```typescript
module.exports = {
  run: async (toolbox) => {
    const {
      print,
      filesystem,
      template,
      prompt,
      system,
      parameters,
      http,
      strings,
      semver,
      packageManager
    } = toolbox

    // Command implementation
  }
}
```

**Toolbox Components:**

1. **print** (powered by colors, ora)
   - `print.info()`, `print.success()`, `print.error()`
   - `print.warning()`, `print.debug()`
   - Spinners, tables, colors

2. **filesystem** (powered by fs-jetpack)
   - `filesystem.read()`, `filesystem.write()`
   - `filesystem.copy()`, `filesystem.remove()`
   - `filesystem.dir()`, `filesystem.find()`

3. **template** (powered by ejs)
   - `template.generate()` - Render templates
   - Supports EJS syntax
   - Props injection

4. **prompt** (powered by enquirer)
   - `prompt.ask()` - Interactive questions
   - Input validation
   - Multi-select, confirm, input types

5. **system** (powered by execa, cross-spawn)
   - `system.run()` - Execute commands
   - Cross-platform compatibility
   - Streaming output

6. **parameters**
   - `parameters.options` - CLI flags
   - `parameters.array` - Positional arguments
   - Powered by yargs-parser

7. **http** (powered by apisauce/axios)
   - `http.create()` - API client
   - Request/response handling

8. **strings** (powered by lodash)
   - `strings.camelCase()`, `strings.pascalCase()`
   - `strings.kebabCase()`, `strings.snakeCase()`
   - String manipulation utilities

9. **semver**
   - Version comparison
   - Semantic versioning utilities

10. **packageManager**
    - Install/remove packages
    - Supports npm, yarn, pnpm

### Command Structure Pattern

**File-based routing:**
```
src/commands/
├── new.ts              → npx ignite-cli new
├── generate.ts         → npx ignite-cli generate
├── cache.ts            → npx ignite-cli cache
└── doctor.ts           → npx ignite-cli doctor
```

**Command Template:**
```typescript
import { GluegunCommand } from 'gluegun'

const command: GluegunCommand = {
  name: 'new',
  description: 'Create a new React Native app',
  run: async (toolbox) => {
    const { parameters, print, filesystem, template } = toolbox

    // 1. Parse parameters
    const projectName = parameters.first

    // 2. Prompt for missing info
    if (!projectName) {
      const result = await prompt.ask({
        type: 'input',
        name: 'name',
        message: 'What is your project name?'
      })
    }

    // 3. Execute logic
    await filesystem.dir(projectName)
    await template.generate({
      template: 'package.json.ejs',
      target: `${projectName}/package.json`,
      props: { name: projectName }
    })

    // 4. Provide feedback
    print.success(`✓ Created ${projectName}`)
  }
}

export default command
```

### Extension Pattern

**Reusable logic as extensions:**
```typescript
// src/extensions/validation.ts
module.exports = (toolbox) => {
  toolbox.validateProjectName = (name: string) => {
    if (!/^[a-z0-9-]+$/.test(name)) {
      throw new Error('Invalid project name')
    }
  }
}
```

**Load extensions:**
```typescript
// src/cli.ts
const cli = build()
  .brand('ignite')
  .src(__dirname)
  .plugins('./node_modules', { matching: 'ignite-*' })
  .help()
  .version()
  .create()
```

### Project Structure Pattern

**Separation of Concerns:**
```
ignite/
├── bin/
│   └── ignite              # Entry point (dev/prod routing)
├── src/
│   ├── cli.ts              # CLI initialization
│   ├── types.ts            # TypeScript types
│   ├── commands/           # User-facing commands
│   │   ├── new.ts
│   │   ├── generate.ts
│   │   └── doctor.ts
│   ├── tools/              # Reusable utilities
│   │   ├── generator.ts
│   │   ├── filesystem.ts
│   │   └── validation.ts
│   └── extensions/         # Toolbox extensions
├── boilerplate/            # Template project
│   └── (full React Native app)
├── test/                   # Integration tests
└── tsconfig.json
```

### Testing Strategy Pattern

**Focus on integration tests:**
```typescript
// test/generate-component.test.ts
describe('generate component', () => {
  it('creates component file', async () => {
    await run('ignite generate component Button')
    expect(filesystem.exists('app/components/Button.tsx')).toBe(true)
  })

  it('generates valid TypeScript', async () => {
    await run('ignite generate component Button')
    const content = filesystem.read('app/components/Button.tsx')
    // Validate syntax, imports, exports
  })
})
```

**Test the generated app:**
- Run Jest tests on generated code
- Validate build process works
- Ensure app runs on iOS/Android

### Performance Pattern

**Lazy loading:**
```typescript
// Don't load heavy dependencies at top level
module.exports = {
  run: async (toolbox) => {
    // Load only when command executes
    const sharp = require('sharp')
    // Use sharp for image processing
  }
}
```

### Key Architectural Insights

1. **Toolbox pattern** provides consistent API across commands
2. **File-based routing** makes command discovery intuitive
3. **Extension system** enables code reuse without inheritance
4. **Template-driven** generation is simple and maintainable
5. **Integration tests** validate end-to-end functionality
6. **Lazy loading** keeps CLI startup fast
7. **Separation of concerns:** Commands orchestrate, tools implement

**Translation to Python:**
- **Toolbox → Context object** (click.pass_context)
- **Extensions → Click plugins** or utility modules
- **File-based routing → Click command groups**
- **Template engine → Jinja2**
- **Testing → pytest with subprocess testing**
- **Performance → lazy imports with importlib**

---

## 8. Implementation Details

### Entry Point Architecture

**bin/ignite (Entry Point):**
```javascript
#!/usr/bin/env node

// Detect if running in dev or production
const isDev = require('fs').existsSync(__dirname + '/../src')

if (isDev) {
  // Development: Use ts-node for instant feedback
  require('ts-node/register')
  require('../src/cli').run()
} else {
  // Production: Use compiled JavaScript
  require('../build/cli').run()
}
```

**Key Insight:** Seamless dev/prod switching without rebuilding.

### CLI Initialization

**src/cli.ts:**
```typescript
import { build } from 'gluegun'

export async function run(argv?: string[]) {
  const cli = build()
    .brand('ignite')
    .src(__dirname)
    .plugins('./node_modules', { matching: 'ignite-*' })
    .help()
    .version()
    .defaultCommand()
    .create()

  const toolbox = await cli.run(argv)
  return toolbox
}
```

**Configuration:**
- `brand('ignite')` - CLI name
- `src(__dirname)` - Look for commands/extensions here
- `plugins()` - Load external plugins
- `help()` - Add help command
- `version()` - Add version command

### TypeScript Configuration

**tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES6",
    "module": "commonjs",
    "lib": ["ES2015", "ES2016", "DOM"],
    "outDir": "./build",
    "sourceMap": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "noUnusedLocals": true
  },
  "include": ["./src"],
  "exclude": ["./boilerplate", "./ignite", "./test"]
}
```

**Key Decisions:**
- Target ES6 (Node.js compatible)
- CommonJS modules (Node.js ecosystem)
- Source maps for debugging
- Exclude boilerplate from compilation

### Build Process

**Build Commands:**
```json
{
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "test": "jest",
    "lint": "eslint src --ext .ts",
    "format": "prettier --write src",
    "clean": "rm -rf build",
    "prepublishOnly": "npm run build"
  }
}
```

**Build Artifacts:**
```
build/
├── cli.js
├── cli.js.map
├── commands/
│   ├── new.js
│   └── generate.js
└── types.js
```

### Release Automation

**semantic-release Configuration:**
```json
{
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/npm",
    "@semantic-release/github"
  ]
}
```

**Commit Message Convention:**
```
feat: add splash screen generator     → Minor version bump
fix: correct component template        → Patch version bump
BREAKING CHANGE: remove old API        → Major version bump
```

**Automated Workflow:**
1. Developer commits with conventional message
2. CI runs tests
3. semantic-release analyzes commits
4. Version bumped automatically
5. CHANGELOG generated
6. Published to NPM
7. GitHub release created

### Template Processing

**Template Generation Flow:**
```typescript
// 1. Load template
const templatePath = 'ignite/templates/component/NAME.tsx.ejs'

// 2. Prepare props
const props = {
  pascalCaseName: 'Button',
  camelCaseName: 'button',
  kebabCaseName: 'button',
  filename: 'Button.tsx',
  subdirectory: 'app/components'
}

// 3. Render template
const content = await template.generate({
  template: templatePath,
  props: props
})

// 4. Write to target
await filesystem.write('app/components/Button.tsx', content)
```

**Template Caching:**
- Templates parsed once
- Cached for repeated generation
- Invalidated on update

### Dependency Management

**Strategy:**
- Lock file committed (yarn.lock)
- Exact versions in package.json for dependencies
- Caret ranges for devDependencies
- Regular Renovate/Dependabot updates

**Cache Implementation:**
```typescript
const cacheDir = path.join(os.homedir(), '.ignite', 'cache')

async function getCachedDependencies() {
  if (filesystem.exists(cacheDir)) {
    return filesystem.read(cacheDir)
  }
  return null
}
```

### Error Handling Pattern

**Graceful degradation:**
```typescript
try {
  await system.run('pod install', { cwd: iosDir })
} catch (error) {
  print.warning('CocoaPods installation failed')
  print.info('Run `pod install` manually in ios/ directory')
}
```

**User-friendly errors:**
```typescript
if (!filesystem.exists(projectName)) {
  print.error(`Directory ${projectName} not found`)
  print.info('Did you run this in the correct directory?')
  process.exit(1)
}
```

### Key Implementation Insights

1. **Dev/prod entry point** enables fast iteration
2. **TypeScript compilation** to standard Node.js JavaScript
3. **semantic-release** removes manual version management
4. **Template caching** improves performance
5. **Graceful error handling** with helpful messages
6. **Lock files** ensure reproducible builds
7. **Integration testing** validates real-world usage

**Translation to Python:**
```python
# Entry point pattern
# bin/mycli
#!/usr/bin/env python3
import os
import sys

if os.path.exists('src/cli.py'):
    # Development mode
    sys.path.insert(0, os.path.dirname(__file__))
    from src.cli import main
else:
    # Production mode
    from mycli.cli import main

if __name__ == '__main__':
    main()
```

**Python Build & Release:**
- Use **poetry** or **hatch** for build
- Use **setuptools-scm** for version from git tags
- Use **GitHub Actions** for CI/CD
- Publish to PyPI with **twine**
- Consider **conventional commits** → automatic versioning

---

## 9. Key Takeaways & Recommendations

### What Makes Ignite Successful

1. **Zero-friction installation**
   - npx eliminates global installation issues
   - Latest version always used
   - Works in CI/CD without setup

2. **Opinionated but flexible**
   - Provides comprehensive defaults
   - Allows customization at every level
   - Templates live in projects (not CLI)

3. **Excellent developer experience**
   - Interactive prompts for guidance
   - Flags for automation
   - Clear error messages
   - Fast performance

4. **Mature ecosystem integration**
   - Built on Gluegun (battle-tested)
   - Integrates with existing tools (Expo, React Navigation)
   - Comprehensive testing strategy

5. **Community-focused**
   - Extensive documentation
   - Active maintenance (9+ years)
   - Clear contribution guidelines

### Architectural Patterns Worth Adopting

**For a Python/FastAPI/OpenShift Equivalent:**

#### 1. Distribution Strategy
```bash
# Target experience:
pipx run agents-cli new MyProject

# Or after installation:
pipx install agents-cli
agents new MyProject
```

**Implementation:**
- Publish to PyPI
- Use **pipx** for zero-installation execution
- Define entry points in pyproject.toml
- Support Python ≥3.11

#### 2. CLI Framework Choice

**Recommended: Click + Rich + Questionary**
```python
import click
from rich.console import Console
from questionary import prompt

@click.group()
@click.pass_context
def cli(ctx):
    """Agents CLI - Scaffolding for AI agent projects"""
    ctx.obj = Toolbox(console=Console())

@cli.command()
@click.argument('project_name')
@click.option('--yes', is_flag=True, help='Accept defaults')
@click.pass_context
def new(ctx, project_name, yes):
    """Create a new agent project"""
    toolbox = ctx.obj
    # Implementation
```

**Why Click:**
- Mature, well-documented
- Excellent subcommand support
- Context passing (similar to toolbox pattern)
- Type hints support

**Why Rich:**
- Beautiful terminal output
- Progress bars, spinners, tables
- Syntax highlighting
- Panels, trees, markdown rendering

**Why Questionary:**
- Modern interactive prompts
- Validation support
- Fuzzy search, autocomplete
- Keyboard navigation

#### 3. Project Structure

```
agents-cli/
├── pyproject.toml
├── src/
│   └── agents_cli/
│       ├── __init__.py
│       ├── cli.py              # Entry point
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── new.py          # New project command
│       │   ├── generate.py     # Code generators
│       │   ├── check.py        # Environment check
│       │   └── cache.py        # Cache management
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── filesystem.py   # File operations
│       │   ├── templates.py    # Template rendering
│       │   ├── validation.py   # Input validation
│       │   └── openshift.py    # OpenShift utilities
│       ├── templates/          # Built-in templates
│       │   └── project/
│       │       ├── template.yaml
│       │       └── files/
│       └── toolbox.py          # Shared context
├── tests/
│   ├── test_new.py
│   └── test_generate.py
└── README.md
```

**pyproject.toml:**
```toml
[project]
name = "agents-cli"
version = "0.1.0"
description = "CLI for scaffolding AI agent projects"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "questionary>=2.0.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "httpx>=0.24.0",
]

[project.scripts]
agents = "agents_cli.cli:main"
agents-cli = "agents_cli.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 4. Template System

**Use YAML for prompts (per CLAUDE.md guidelines):**
```yaml
# prompts/new-project.yaml
name: "Create New Agent Project"
description: "Scaffolds a new AI agent project with FastAPI and MCP"
questions:
  - type: text
    name: project_name
    message: "What is your project name?"
    validate: "^[a-z][a-z0-9-]*$"

  - type: select
    name: agent_framework
    message: "Which agent framework?"
    choices:
      - LangGraph
      - LlamaStack

  - type: confirm
    name: use_kubernetes
    message: "Deploy to OpenShift?"
    default: true
```

**Use Jinja2 for code templates:**
```jinja2
{# templates/project/main.py.j2 #}
from fastapi import FastAPI
from {{ project_name }}.agents import {{ agent_class }}

app = FastAPI(title="{{ project_name }}")

@app.get("/")
async def root():
    return {"message": "{{ project_description }}"}
```

#### 5. Generator Architecture

**Copy templates into projects:**
```python
# After project creation
shutil.copytree(
    src='agents_cli/templates/generators',
    dst=f'{project_name}/.cli/generators'
)
```

**Allow customization:**
```bash
# Users can modify
vim .cli/generators/agent/template.py.j2

# Then generate
agents generate agent MyAgent
```

#### 6. Command Patterns

**Follow Ignite's command structure:**
```bash
agents new <project-name>           # Create project
agents generate <type> <name>       # Generate code
agents check                         # Environment diagnostics
agents cache clear                   # Clear cache
agents deploy                        # Deploy to OpenShift
```

**Support interactive + non-interactive:**
```bash
# Interactive (prompts for missing info)
agents new

# Non-interactive (for CI/CD)
agents new my-project --yes \
  --framework langraph \
  --openshift true
```

#### 7. Testing Strategy

**Integration tests on generated code:**
```python
def test_new_project(tmp_path):
    result = run_cli(['new', 'test-project', '--yes'])
    assert result.exit_code == 0

    # Validate structure
    assert (tmp_path / 'test-project' / 'src').exists()
    assert (tmp_path / 'test-project' / 'pyproject.toml').exists()

    # Validate generated code works
    subprocess.run(['pytest'], cwd=tmp_path / 'test-project', check=True)
```

#### 8. OpenShift Integration

**Built-in OpenShift support:**
```python
# tools/openshift.py
def generate_manifests(project_name: str, namespace: str):
    """Generate OpenShift manifests"""
    templates = [
        'deployment.yaml.j2',
        'service.yaml.j2',
        'route.yaml.j2',
        'buildconfig.yaml.j2',
    ]

    for template in templates:
        render_template(
            template,
            output=f'manifests/base/{template[:-3]}',
            context={'project_name': project_name, 'namespace': namespace}
        )
```

**Generate Kustomize structure:**
```
manifests/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    ├── staging/
    └── production/
```

#### 9. Configuration Management

**Use multiple config layers:**
```python
# 1. Default config (in CLI)
DEFAULT_CONFIG = {
    'python_version': '3.11',
    'container_runtime': 'podman',
    'base_image': 'registry.redhat.io/ubi9/python-311',
}

# 2. Project config (created in project)
# .agents/config.yaml
python_version: "3.11"
container_runtime: podman
base_image: registry.redhat.io/ubi9/python-311
deploy_target: openshift
namespace: my-agents

# 3. User overrides (via flags)
agents new myproject --python-version 3.12
```

#### 10. Cache Implementation

**Speed up repeated operations:**
```python
import appdirs
from pathlib import Path

CACHE_DIR = Path(appdirs.user_cache_dir('agents-cli'))

def cache_dependencies(requirements: list):
    cache_file = CACHE_DIR / 'requirements.txt'
    cache_file.write_text('\n'.join(requirements))

def load_cached_dependencies():
    cache_file = CACHE_DIR / 'requirements.txt'
    if cache_file.exists():
        return cache_file.read_text().splitlines()
    return None
```

### Specific Recommendations for Your Use Case

Given your context (Python, FastAPI, OpenShift, FIPS, Red Hat ecosystem):

#### 1. Base Images
```yaml
# templates/project/Containerfile.j2
FROM registry.redhat.io/ubi9/python-311
{% if fips_mode %}
# FIPS mode enabled
ENV OPENSSL_FIPS=1
{% endif %}
```

#### 2. MCP Server Support
```python
@cli.command()
def generate_mcp_server(name: str, transport: str = 'http'):
    """Generate MCP server with FastMCP v2"""
    render_template(
        'mcp-server.py.j2',
        output=f'mcp-servers/{name}.py',
        context={'name': name, 'transport': transport}
    )
```

#### 3. OpenShift-Native Commands
```bash
agents deploy               # Deploy to OpenShift
agents logs                 # Stream pod logs
agents scale --replicas 3   # Scale deployment
agents status               # Show deployment status
```

#### 4. FIPS Compliance Check
```python
@cli.command()
def check_fips():
    """Verify FIPS compliance"""
    import subprocess
    result = subprocess.run(['openssl', 'version'], capture_output=True)
    if b'fips' in result.stdout.lower():
        console.print('[green]✓ FIPS mode enabled')
    else:
        console.print('[yellow]⚠ FIPS mode not detected')
```

#### 5. Prompt Management
```bash
# Generate from YAML prompts (per CLAUDE.md)
agents generate prompt data-analysis

# Creates: prompts/data-analysis.yaml
# Also creates: src/prompts.py (loader)
```

### Implementation Roadmap

**Phase 1: Core CLI (Weeks 1-2)**
- [ ] Set up project structure
- [ ] Implement `new` command
- [ ] Basic template system (Jinja2)
- [ ] Interactive prompts (questionary)
- [ ] File operations (pathlib + shutil)

**Phase 2: Generators (Weeks 3-4)**
- [ ] Implement `generate` command
- [ ] Create generator templates
- [ ] Support custom generators in projects
- [ ] Template copying into new projects

**Phase 3: OpenShift Integration (Week 5)**
- [ ] Manifest generation
- [ ] Kustomize structure
- [ ] `deploy` command
- [ ] `logs` and `status` commands

**Phase 4: Polish & Testing (Week 6)**
- [ ] Environment check (`check` command)
- [ ] Cache implementation
- [ ] Integration tests
- [ ] Documentation

**Phase 5: Distribution (Week 7)**
- [ ] PyPI publishing setup
- [ ] CI/CD pipeline
- [ ] Versioning strategy
- [ ] Release automation

### Success Metrics

**Measure what Ignite measures:**
1. **Time saved:** Target 1-2 weeks (vs Ignite's 2-4 weeks)
2. **Adoption rate:** Track project creations
3. **Customization frequency:** How often users modify generators
4. **Issue resolution time:** Fast, helpful error messages
5. **Community engagement:** PRs, issues, discussions

---

## 10. References & Further Reading

### Primary Sources
- **Ignite CLI Repository:** https://github.com/infinitered/ignite
- **Ignite Documentation:** https://docs.infinite.red/ignite-cli/
- **Gluegun Documentation:** https://infinitered.github.io/gluegun/
- **Gluegun Repository:** https://github.com/infinitered/gluegun

### Related Technologies
- **Click (Python):** https://click.palletsprojects.com/
- **Rich (Python):** https://rich.readthedocs.io/
- **Questionary (Python):** https://questionary.readthedocs.io/
- **Jinja2 (Python):** https://jinja.palletsprojects.io/
- **Typer (Alternative to Click):** https://typer.tiangolo.com/

### Patterns & Best Practices
- **12 Factor App:** https://12factor.net/
- **Conventional Commits:** https://www.conventionalcommits.org/
- **Semantic Versioning:** https://semver.org/
- **CLI Guidelines:** https://clig.dev/

### OpenShift & Red Hat
- **OpenShift CLI:** https://docs.openshift.com/container-platform/latest/cli_reference/
- **Red Hat UBI Images:** https://catalog.redhat.com/software/containers/search
- **Kustomize:** https://kustomize.io/

---

## Appendix: Comparison with Other CLI Tools

### Ignite vs Create React App
- **Ignite:** Opinionated, batteries-included, React Native-specific
- **CRA:** Minimal, React web-focused, less opinionated
- **Takeaway:** Ignite's comprehensive approach is better for complex ecosystems

### Ignite vs Yeoman
- **Ignite:** Modern, TypeScript, focused on React Native
- **Yeoman:** Older, JavaScript, language-agnostic
- **Takeaway:** Ignite's focus enables better defaults

### Ignite vs Angular CLI
- **Ignite:** Template-based, flexible generators
- **Angular CLI:** AST-based, sophisticated code modification
- **Takeaway:** Template approach is simpler, AST is more powerful

### Ignite vs Rails Generators
- **Ignite:** Templates copied into projects
- **Rails:** Generators built into framework
- **Takeaway:** Ignite's approach enables customization without framework changes

---

## Final Thoughts

Ignite CLI demonstrates that a well-designed CLI tool can dramatically improve developer productivity. Its success comes from:

1. **Removing friction** at every step
2. **Providing escape hatches** for power users
3. **Enabling customization** without forking
4. **Maintaining simplicity** despite power
5. **Investing in documentation** and community

For building a similar tool in the Python/FastAPI/OpenShift ecosystem, adopt Ignite's:
- **Zero-installation approach** (pipx)
- **Toolbox pattern** (Click context)
- **Template-in-project strategy** (Jinja2 + YAML)
- **Interactive + scripted modes** (questionary + flags)
- **Integration testing philosophy** (pytest on generated code)

The result will be a powerful, flexible CLI that accelerates agent development while maintaining the high standards of the Red Hat ecosystem.
