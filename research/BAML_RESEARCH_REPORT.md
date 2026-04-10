# BAML Research Report for fips-agents-cli

**Date:** 2025-10-14
**Prepared For:** fips-agents-cli project
**Research Focus:** Evaluating BAML (BoundaryML) for prompt generation system

---

## Executive Summary

**Recommendation: DO NOT ADOPT BAML at this time**

After comprehensive research, I recommend **maintaining the current YAML-based prompt management approach** for fips-agents-cli. While BAML offers compelling benefits for type-safe structured outputs and runtime LLM interactions, it fundamentally solves a different problem than what fips-agents-cli needs.

**Key Reasoning:**
1. **Different Use Cases**: BAML is designed for runtime LLM function calling with structured outputs. fips-agents-cli generates static MCP server scaffolding - the prompts are templates, not runtime LLM invocations.
2. **Increased Complexity**: BAML adds a compilation step, Rust-based toolchain, and learning curve that doesn't provide value for static code generation.
3. **YAML Advantage for Templates**: For developer-editable prompt templates used in code generation, YAML is simpler, more transparent, and easier to maintain than BAML's DSL.
4. **FIPS/OpenShift Concerns**: BAML's Rust compilation and additional dependencies introduce potential compatibility issues with FIPS-validated environments.
5. **Current Approach Works Well**: The existing YAML + Jinja2 system is simple, maintainable, and well-suited for the CLI's scaffolding use case.

**When BAML Would Be Valuable**: If fips-agents-cli evolves to include runtime AI features (e.g., AI-assisted component generation, intelligent code analysis), BAML should be reconsidered.

---

## 1. BAML Overview

### What is BAML?

BAML (Basically a Made-up Language) is a domain-specific language (DSL) for building reliable AI workflows with structured LLM outputs. It's a programming language that treats LLM prompts as typed functions, transforming prompt engineering into "schema engineering."

**Core Philosophy:**
- Prompts are functions with defined inputs and outputs
- Type safety and schema validation are first-class concerns
- Structured output parsing with automatic error correction
- Multi-language support (Python, TypeScript, Ruby, Go, Java, C#, Rust)

### Key Features

1. **Type System**: Strong typing for LLM inputs/outputs with classes, enums, optionals, unions
2. **Schema-Aligned Parsing (SAP)**: Rust-based parser that automatically corrects LLM outputs to match schemas in <10ms
3. **Multi-Provider Support**: Works with OpenAI, Anthropic, Google, etc. with easy model switching
4. **IDE Integration**: VSCode/Cursor/JetBrains extensions with syntax highlighting and inline testing
5. **Generated Clients**: Auto-generates type-safe client code in target languages
6. **Testing Infrastructure**: First-class testing support with parallel execution
7. **Streaming Support**: Type-safe streaming interfaces for UI integration

### How BAML Works

1. **Define**: Write `.baml` files with function and type definitions
2. **Generate**: Run `baml-cli generate` to create language-specific client code
3. **Use**: Import and call generated functions from your application
4. **Runtime**: BAML handles prompt construction, LLM calls, and output parsing

**Example BAML Code:**

```baml
// Type definition
class Book {
  title string
  authors string[]
  rating int?
  date string? @description("format as yyyy-mm if possible")
}

// Function with prompt
function ExtractBook(book_text: string) -> Book {
  client ClaudeHaiku

  prompt #"
    Your task is to extract structured information from the book and format it as JSON.

    Book:
    ---
    {{ book_text }}
    ---

    {{ ctx.output_format }}

    JSON:
  "#
}

// Test case
test Test_complete {
  functions [ExtractBook]
  args {
    book_text #"Les feux de Cibola - The Expanse - Tome 4/7 - James S.A. Corey"#
  }
}
```

**Python Usage:**

```python
from baml_client.sync_client import b
from baml_client.types import Book

# Call the function
book: Book = b.ExtractBook("The Martian - Andy Weir")

# Use strongly-typed result
print(book.title)  # Type-checked
print(book.authors)  # List[str]
```

---

## 2. Integration Analysis

### BAML with FastMCP

**Current State:**
- BAML and FastMCP can be used together but serve different purposes
- Community project `baml-agents` demonstrates integration patterns
- No official integration or FastMCP-specific BAML features
- Integration is manual and requires understanding both frameworks

**Integration Pattern:**

```python
# BAML defines structured agent actions
class AgentAction {
  tool_name string
  parameters dict
  reasoning string
}

function SelectAction(goal: string, available_tools: string[]) -> AgentAction {
  client GPT4
  prompt #"
    Given the goal: {{ goal }}
    Available tools: {{ available_tools }}

    Select the best tool and parameters.
    {{ ctx.output_format }}
  "#
}

# FastMCP provides the tools
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def calculator(operation: str, a: float, b: float) -> float:
    """Perform calculations"""
    # Implementation

# BAML decides which tool to call, FastMCP executes it
```

### Dependencies and Runtime Requirements

**Build-time Dependencies:**
- `baml-cli` - Command-line tool for code generation (Rust-based)
- VSCode/IDE extension (optional but recommended)

**Runtime Dependencies:**
- `baml-py` package (~79KB npm equivalent, Python package size varies)
- Generated `baml_client` code (auto-generated Python modules)
- Pydantic (for type validation in Python)

**Build Process:**
1. Write `.baml` files in `baml_src/` directory
2. Run `baml-cli generate` to generate `baml_client/` code
3. Import and use generated client in application code

**Important:** The `baml-cli` tool is required in the development environment and CI/CD pipeline. This adds a compilation step that doesn't exist in the current YAML approach.

### FIPS/OpenShift/Container Compatibility

**Potential Concerns:**

1. **Rust Dependency**: BAML's core compiler is written in Rust
   - May require Rust toolchain for some operations
   - Binary compatibility across architectures (ARM vs x86_64)
   - FIPS validation status of Rust cryptographic libraries (if used)

2. **Build Complexity**:
   - Additional compilation step in CI/CD
   - Generated code needs to be committed or built in container
   - Version synchronization between CLI, VSCode extension, and package

3. **Container Build Process**:
   - Need to install `baml-cli` in container build stage
   - Generated code increases image size
   - Red Hat UBI compatibility needs verification

4. **FIPS Compliance**:
   - BAML's Rust runtime may use cryptographic libraries for HTTP/TLS
   - No explicit FIPS compliance documentation found
   - Would require validation of all Rust dependencies

**Mitigation Strategies:**
- Pre-generate BAML client code and commit to repository (adds generated code to git)
- Use multi-stage container builds to minimize runtime dependencies
- Verify all dependencies against FIPS requirements
- Test thoroughly on OpenShift before production use

---

## 3. Benefits Assessment

### Type Safety for Prompt Inputs/Outputs

**BAML Approach:**
```baml
class SearchParams {
  query string @description("Search query")
  limit int @description("Max results") @min(1) @max(100)
  filters string[]?
}

function SearchDocuments(params: SearchParams) -> list[SearchResult] {
  client GPT4
  prompt #"Search for: {{ params.query }}"#
}
```

**Benefits:**
- Compile-time type checking
- Auto-generated Pydantic models
- IDE autocomplete and type hints
- Automatic validation of inputs/outputs

**Current YAML Approach:**
```yaml
name: "search_documents"
description: "Search through documents"
parameters:
  - name: "query"
    type: "string"
    description: "Search query"
    required: true
  - name: "limit"
    type: "int"
    description: "Maximum results"
    default: 10
    ge: 1
    le: 100
template: |
  Search for: {query}
  Return up to {limit} results
```

**Reality Check for fips-agents-cli:**
- ❌ **Not Applicable**: Our YAML files are templates for *generating code*, not runtime prompts
- ❌ **Type safety needed at generation time, not in YAML**: Jinja2 handles variable substitution during code generation
- ✅ **Current approach**: Generated code already includes Pydantic validation in the scaffolded FastMCP tools

### Structured Output Parsing

**BAML's Strength:**
```baml
class CodeReview {
  issues list[Issue]
  overall_quality "excellent" | "good" | "fair" | "poor"
  recommendations string[]
}

function ReviewCode(code: string) -> CodeReview {
  client ClaudeOpus
  prompt #"Review this code: {{ code }}"#
}
```

BAML automatically:
- Parses LLM response into structured objects
- Corrects formatting errors (e.g., "approximately 5" → 5)
- Validates against schema
- Retries with fixes if validation fails

**Reality Check for fips-agents-cli:**
- ❌ **Not Applicable**: fips-agents-cli doesn't make runtime LLM calls
- ❌ **Structured outputs not needed**: We're generating static Python code, not parsing LLM responses
- ✅ **Current approach**: Jinja2 templates generate properly structured Python code directly

### Prompt Versioning and Testing

**BAML Approach:**
```baml
test ValidateExtraction {
  functions [ExtractBook]
  args {
    book_text #"The Martian - Andy Weir"#
  }
}
```

Benefits:
- Test cases live alongside prompt definitions
- Parallel test execution across multiple cases
- Easy regression testing when prompts change
- Version control of prompts and tests together

**Reality Check for fips-agents-cli:**
- ⚠️ **Partially Applicable**: Testing generated code is valuable
- ✅ **Current approach works**: YAML templates are version-controlled; pytest tests generated code
- ❌ **BAML testing not needed**: We test the *generated code*, not prompt responses

### Developer Experience Improvements

**BAML's DX Features:**
1. **Interactive IDE**: Run prompts directly in VSCode
2. **Type autocomplete**: Full IntelliSense for BAML types
3. **Inline errors**: Syntax and type errors shown in editor
4. **Prompt visualization**: See full prompts before execution
5. **Request inspection**: View exact API requests to LLMs

**Reality Check for fips-agents-cli:**
- ✅ **YAML has good DX**: Easy to read, edit, and understand
- ✅ **No IDE needed**: Developers can edit YAML in any text editor
- ❌ **BAML features not relevant**: No runtime LLM calls to inspect/debug
- ⚠️ **Learning curve**: BAML DSL requires learning; YAML is universal

### FastMCP-Specific Advantages

**Potential Synergies:**
- ❌ **None Found**: No official FastMCP + BAML integration
- ❌ **Different layers**: FastMCP defines MCP server structure; BAML handles LLM I/O
- ⚠️ **Community experiments**: `baml-agents` shows it's possible but requires custom glue code
- ❌ **Not complementary for our use case**: fips-agents-cli generates FastMCP servers but doesn't run them

---

## 4. Drawbacks Assessment

### Learning Curve for Developers

**BAML DSL:**
- New language syntax to learn
- Compilation process to understand
- Generator configuration and versioning
- Different mental model (functions vs. templates)

**Estimated Learning Time:**
- Basic usage: 2-4 hours
- Proficient: 1-2 weeks
- Advanced features: 1-2 months

**Current YAML Approach:**
- Familiar format (YAML is universal)
- Simple variable substitution with `{variable}`
- No compilation or build steps
- Easy to onboard new developers

**Impact on fips-agents-cli:**
- 📈 **Increased barrier**: Contributors need to learn BAML DSL
- 📈 **Documentation burden**: Need to explain BAML in addition to tool itself
- 📉 **Reduced accessibility**: YAML is more approachable for quick edits

### Build/Deployment Complexity

**BAML Requirements:**

1. **Development Workflow:**
   ```bash
   # Write .baml files
   vim baml_src/prompts.baml

   # Generate client code
   baml-cli generate

   # Use generated code
   python -m fips_agents_cli generate tool my_tool
   ```

2. **CI/CD Pipeline:**
   - Install `baml-cli` in CI environment
   - Run `baml-cli generate` before tests
   - Ensure generated code is up-to-date
   - Version sync between CLI, extension, and package

3. **Container Build:**
   ```dockerfile
   FROM registry.redhat.io/ubi9/python-311

   # Install baml-cli (how? pip? binary? compile from source?)
   RUN pip install baml-py

   # Copy BAML source
   COPY baml_src/ /app/baml_src/

   # Generate client code
   RUN baml-cli generate

   # ... rest of build
   ```

**Current Approach:**
- No build step for YAML files
- No additional CLI tools required
- Direct Jinja2 rendering at runtime
- Simpler container builds

**Impact Assessment:**
- 📈 **Increased complexity**: New build step, dependency, tooling
- 📈 **Failure points**: Generation can fail; version mismatches
- 📈 **CI/CD changes**: All pipelines need `baml-cli`
- ⚠️ **OpenShift impact**: BuildConfig needs baml-cli in builder image

### Lock-in and Vendor Concerns

**BAML Ecosystem:**
- Developed by BoundaryML (venture-backed startup)
- Open source (Apache 2.0 license)
- Active development but relatively young (2024)
- Small but growing community

**Concerns:**
1. **Proprietary DSL**: BAML syntax is unique; no standard
2. **Migration cost**: Converting BAML → another format requires rewriting
3. **Maintenance risk**: If BoundaryML pivots/closes, community continuation uncertain
4. **Limited tooling**: Only BoundaryML provides official IDE extensions

**Current YAML Approach:**
- Industry-standard format
- Works with any text editor
- Easy to migrate to other systems
- No vendor dependency

**Risk Assessment:**
- ⚠️ **Moderate lock-in**: Open source mitigates risk but DSL is proprietary
- ✅ **Active community**: Growing adoption reduces abandonment risk
- ❌ **Unnecessary risk for our use case**: YAML provides same value without lock-in

### Performance Overhead

**BAML Runtime:**
- Rust-based parser (<10ms for schema alignment)
- HTTP calls to LLM providers
- Pydantic validation overhead
- Generated client code adds to package size

**Reality Check:**
- ❌ **Not applicable**: fips-agents-cli doesn't run BAML at runtime
- ❌ **Generation time only**: Only matters during code generation, not user execution
- ✅ **Current approach**: Jinja2 rendering is fast and lightweight

### YAML vs BAML Editability

**YAML Strengths:**
```yaml
# Easy to edit, read, and understand
name: "code_review"
description: "Review code for best practices"
template: |
  Review the following code:

  {code}

  Provide feedback on:
  - Code quality
  - Best practices
  - Security issues
```

**BAML Requirements:**
```baml
// More structured but less flexible
class ReviewFeedback {
  code_quality string
  best_practices string[]
  security_issues string[]
}

function CodeReview(code: string) -> ReviewFeedback {
  client ClaudeOpus

  prompt #"
    Review the following code:
    {{ code }}

    Provide feedback on:
    - Code quality
    - Best practices
    - Security issues

    {{ ctx.output_format }}
  "#
}
```

**For Developer Onboarding (Our Use Case):**
- ✅ **YAML wins**: Easy to show developers what prompts the tool uses
- ✅ **YAML is self-documenting**: Format is immediately understandable
- ❌ **BAML requires explanation**: Need to explain DSL, compilation, generated code
- ✅ **YAML for templates**: Better suited for code generation templates

---

## 5. Comparison to Current Approach

### YAML Files vs BAML Syntax

**Current fips-agents-cli YAML (for prompt generation):**

```yaml
name: "code_review"
description: "Review code for best practices"
variables:
  - name: "code"
    type: "string"
    description: "Code to review"
    required: true
  - name: "language"
    type: "string"
    description: "Programming language"
    required: true
template: |
  You are a code reviewer for {language} code.

  Review the following code:
  {code}

  Provide:
  1. Overall assessment
  2. Specific issues
  3. Recommendations
```

**Equivalent BAML:**

```baml
class CodeReviewRequest {
  code string @description("Code to review")
  language string @description("Programming language")
}

class CodeReviewResponse {
  overall_assessment string
  issues string[]
  recommendations string[]
}

function CodeReview(request: CodeReviewRequest) -> CodeReviewResponse {
  client ClaudeOpus

  prompt #"
    You are a code reviewer for {{ request.language }} code.

    Review the following code:
    {{ request.code }}

    Provide:
    1. Overall assessment
    2. Specific issues
    3. Recommendations

    {{ ctx.output_format }}
  "#
}
```

### Jinja2 Variable Substitution vs BAML's Approach

**Current Approach (YAML + Jinja2):**

```python
# In fips_agents_cli/commands/generate.py
from jinja2 import Template
import yaml

# Load YAML template
with open("prompts/code_review.yaml") as f:
    prompt_config = yaml.safe_load(f)

# Render with Jinja2
template = Template(prompt_config["template"])
rendered = template.render(code=user_code, language="python")

# Generate Python code that uses this prompt
tool_code = generate_tool_code(
    name="code_review",
    prompt=rendered,
    parameters=prompt_config["variables"]
)
```

**BAML Approach:**

```python
# After running `baml-cli generate`
from baml_client.sync_client import b
from baml_client.types import CodeReviewRequest

# Create request object
request = CodeReviewRequest(
    code=user_code,
    language="python"
)

# Call BAML function (makes LLM API call)
response = b.CodeReview(request)

# Use structured response
print(response.overall_assessment)
print(response.issues)
```

**Key Difference:**
- **YAML + Jinja2**: Templates are rendered into code *at generation time*
- **BAML**: Functions are called *at runtime* to interact with LLMs

**This is the fundamental mismatch**: fips-agents-cli generates static code; BAML executes dynamic LLM calls.

### Runtime Flexibility vs Compile-time Checking

**YAML Flexibility:**
- ✅ Edit and reload without recompilation
- ✅ Hot-reload possible for prompt updates
- ✅ No build step required
- ✅ Works with any template engine

**BAML Compile-time Safety:**
- ✅ Type errors caught before runtime
- ✅ Schema validation ensures correct structure
- ❌ Requires regeneration after changes
- ❌ Additional build step in workflow

**For fips-agents-cli:**
- ✅ **YAML flexibility is valuable**: Developers can quickly iterate on templates
- ❌ **BAML compile-time checking not needed**: We're generating code, not running prompts
- ✅ **Current approach**: Fast iteration, simple workflow

### Developer Onboarding Complexity

**Current YAML Approach:**

1. **View a template:**
   ```bash
   cat prompts/tool_template.yaml
   ```

2. **Understand immediately:**
   - YAML is self-explanatory
   - Variable names are clear
   - Template structure is visible

3. **Modify if needed:**
   - Edit YAML in any editor
   - Change template text
   - Add/remove variables
   - No recompilation needed

**BAML Approach:**

1. **View BAML file:**
   ```bash
   cat baml_src/tools.baml
   ```

2. **Learn BAML syntax:**
   - Understand class definitions
   - Learn function syntax
   - Understand client configuration
   - Learn Jinja-like templating in BAML

3. **Modify:**
   - Edit `.baml` file
   - Run `baml-cli generate`
   - Check generated code
   - Debug if generation fails

4. **Understand generated code:**
   - Review `baml_client/` directory
   - Understand how to import and use
   - Learn version synchronization

**Complexity Comparison:**
- **YAML**: ~5 minutes to understand
- **BAML**: ~2-4 hours for basic proficiency

**For Project Documentation (CLAUDE.md states this is a goal):**
> "Rationale: Keep prompts easily editable rather than baking into MCP servers"
> "Developer onboarding: YAML format makes it easy to brief other developers on prompt functionality"

✅ **Current approach aligns with project goals**
❌ **BAML adds complexity counter to project philosophy**

---

## 6. Recommendation

### Should We Adopt BAML?

**NO - Not at this time**

### Why Stick with YAML?

1. **Use Case Mismatch**:
   - fips-agents-cli generates static code from templates
   - BAML is designed for runtime LLM function calling
   - We don't need structured output parsing (we're not calling LLMs)

2. **Simplicity is Valuable**:
   - YAML is universally understood
   - No compilation step needed
   - Faster development iteration
   - Lower barrier to contribution

3. **Project Philosophy Alignment**:
   - CLAUDE.md emphasizes: "Keep prompts easily editable"
   - CLAUDE.md emphasizes: "Easy to brief other developers"
   - YAML achieves both; BAML adds complexity

4. **FIPS/OpenShift Concerns**:
   - BAML adds Rust dependencies
   - Build complexity increases
   - FIPS validation uncertain
   - Container builds become more complex

5. **No Clear Benefit**:
   - Type safety: Not needed for static templates
   - Structured outputs: Not parsing LLM responses
   - Testing: Already have pytest for generated code
   - IDE features: Not relevant for template editing

### Integration Roadmap (If Adoption Were Recommended)

**Since we're NOT adopting BAML, this section is hypothetical for future reference:**

<details>
<summary>Click to expand hypothetical integration plan</summary>

**Phase 1: Proof of Concept (2 weeks)**
1. Create BAML versions of existing YAML prompts
2. Modify code generation to use BAML-generated clients
3. Test on sample MCP server projects
4. Evaluate developer experience

**Phase 2: Parallel Implementation (4 weeks)**
5. Support both YAML and BAML prompts
6. Add `--use-baml` flag to generate command
7. Update documentation with BAML examples
8. Create migration guide for existing projects

**Phase 3: Full Migration (6 weeks)**
9. Migrate all templates to BAML
10. Update CI/CD pipelines
11. Update container builds
12. Deprecate YAML prompts (with grace period)

**Phase 4: Optimization (ongoing)**
13. Fine-tune BAML schemas for optimal token usage
14. Add advanced type validations
15. Create reusable BAML libraries for common patterns

**Total Estimated Effort**: 12+ weeks of development time

</details>

### Why YAML is Better for Our Use Case

| Criteria | YAML | BAML | Winner |
|----------|------|------|--------|
| **Ease of editing** | ✅ Any text editor | ⚠️ IDE recommended | YAML |
| **Learning curve** | ✅ ~5 minutes | ❌ 2-4 hours | YAML |
| **Build complexity** | ✅ None | ❌ Requires baml-cli | YAML |
| **Type safety** | ⚠️ Runtime only | ✅ Compile-time | N/A (not needed) |
| **Structured outputs** | ❌ Manual parsing | ✅ Automatic | N/A (not needed) |
| **Template flexibility** | ✅ Jinja2 powerful | ⚠️ BAML Jinja-like | YAML |
| **Version control** | ✅ Simple diffs | ✅ Simple diffs | Tie |
| **Documentation value** | ✅ Self-explanatory | ⚠️ Needs explanation | YAML |
| **FIPS compliance** | ✅ No concerns | ⚠️ Needs validation | YAML |
| **Container builds** | ✅ Simple | ❌ Complex | YAML |
| **Use case fit** | ✅ Perfect for templates | ❌ Designed for runtime | YAML |

**Overall Winner: YAML** (8 wins vs 2 wins, 3 N/A)

---

## 7. When to Reconsider BAML

BAML should be reconsidered if fips-agents-cli evolves to include:

### Future Features That Would Benefit from BAML

1. **AI-Assisted Code Generation**:
   ```python
   # Instead of templates, use AI to generate code
   fips-agents generate tool my_tool --ai-assisted

   # BAML would provide:
   # - Structured code output
   # - Type-safe parameters
   # - Consistent formatting
   ```

2. **Intelligent Code Analysis**:
   ```python
   # Analyze existing code for improvements
   fips-agents analyze my_mcp_server

   # BAML would provide:
   # - Structured analysis results
   # - Categorized recommendations
   # - Actionable insights
   ```

3. **Interactive Project Configuration**:
   ```python
   # Chat-based project setup
   fips-agents create mcp-server --interactive

   # BAML would provide:
   # - Structured conversation flow
   # - Validated user inputs
   # - Type-safe configuration
   ```

4. **Runtime MCP Features**:
   - If the CLI evolves to run MCP servers (not just generate them)
   - If we add AI-powered debugging or testing tools
   - If we build a hosted MCP server platform

### Hybrid Approach to Consider

If runtime AI features are added:

1. **Keep YAML for Templates**: Continue using YAML for code generation templates
2. **Add BAML for AI Features**: Use BAML for new AI-assisted features
3. **Clear Separation**: YAML in `prompts/`, BAML in `baml_src/`
4. **Gradual Adoption**: Introduce BAML only where it provides clear value

**Example:**
```
fips-agents-cli/
├── prompts/              # YAML templates for code generation
│   ├── tool.yaml
│   ├── resource.yaml
│   └── prompt.yaml
├── baml_src/             # BAML for AI features (future)
│   ├── code_generator.baml
│   ├── code_analyzer.baml
│   └── config_assistant.baml
└── src/
    └── fips_agents_cli/
        ├── generate.py   # Uses YAML templates
        └── ai_assist.py  # Uses BAML functions
```

---

## 8. Risks and Mitigation Strategies

### If We Were to Adopt BAML (Not Recommended)

**Risk 1: Increased Complexity**
- **Impact**: Higher barrier to contribution, slower development
- **Mitigation**: Comprehensive documentation, example projects, video tutorials
- **Likelihood**: High
- **Severity**: Medium

**Risk 2: FIPS Compliance Issues**
- **Impact**: Unable to deploy in FIPS-enabled OpenShift environments
- **Mitigation**: Thorough FIPS validation of all dependencies, Rust library audit
- **Likelihood**: Medium
- **Severity**: Critical (blocker for enterprise adoption)

**Risk 3: Build Pipeline Failures**
- **Impact**: CI/CD failures, deployment delays
- **Mitigation**: Robust error handling, fallback mechanisms, pre-commit hooks
- **Likelihood**: Medium
- **Severity**: Medium

**Risk 4: Container Build Complexity**
- **Impact**: Larger images, slower builds, platform compatibility issues
- **Mitigation**: Multi-stage builds, builder image optimization, platform testing
- **Likelihood**: High
- **Severity**: Low-Medium

**Risk 5: Developer Onboarding Friction**
- **Impact**: Slower contributor ramp-up, fewer contributions
- **Mitigation**: Interactive tutorials, simplified examples, optional BAML features
- **Likelihood**: High
- **Severity**: Medium

**Risk 6: Ecosystem Lock-in**
- **Impact**: Difficult migration if BAML is discontinued or changes direction
- **Mitigation**: Abstraction layer, fallback to YAML, monitoring project health
- **Likelihood**: Low
- **Severity**: High

### Current YAML Approach Risks (Minimal)

**Risk 1: Limited Type Safety**
- **Impact**: Runtime errors in generated code
- **Mitigation**: Already have: Comprehensive test suite, Pydantic validation in generated code
- **Likelihood**: Low
- **Severity**: Low

**Risk 2: Template Complexity**
- **Impact**: Jinja2 templates become hard to maintain
- **Mitigation**: Keep templates simple, modular structure, documentation
- **Likelihood**: Low
- **Severity**: Low

---

## 9. Concrete Examples: YAML vs BAML

### Example 1: Simple Tool Prompt

**Current YAML Template:**
```yaml
# prompts/tool.yaml
name: "{{ tool_name }}"
description: "{{ tool_description }}"
parameters:
  {% for param in parameters %}
  - name: "{{ param.name }}"
    type: "{{ param.type }}"
    description: "{{ param.description }}"
    {% if param.required %}required: true{% endif %}
  {% endfor %}

template: |
  @mcp.tool()
  {% if async_mode %}async {% endif %}def {{ tool_name }}(
      {% for param in parameters %}
      {{ param.name }}: {{ param.type }}{% if param.description %},  # {{ param.description }}{% endif %}
      {% endfor %}
  ) -> {{ return_type }}:
      """{{ tool_description }}"""
      # TODO: Implement tool logic
      pass
```

**Equivalent BAML:**
```baml
// baml_src/tool_generator.baml

class ToolParameter {
  name string
  type string
  description string
  required bool
}

class ToolDefinition {
  tool_name string
  tool_description string
  parameters ToolParameter[]
  async_mode bool
  return_type string
}

class GeneratedToolCode {
  decorator string
  function_signature string
  docstring string
  implementation string
}

function GenerateToolCode(definition: ToolDefinition) -> GeneratedToolCode {
  client GPT4

  prompt #"
    Generate a FastMCP tool function with:
    - Name: {{ definition.tool_name }}
    - Description: {{ definition.tool_description }}
    - Async: {{ definition.async_mode }}
    - Parameters: {{ definition.parameters }}
    - Return type: {{ definition.return_type }}

    {{ ctx.output_format }}
  "#
}
```

**Analysis:**
- ✅ **YAML**: Direct template, no LLM call needed, predictable output
- ❌ **BAML**: Requires LLM call to generate code (unpredictable, costs money, slower)
- **Winner**: YAML (for static code generation)

### Example 2: Prompt with Complex Logic

**Current YAML Template:**
```yaml
# prompts/code_review.yaml
name: "code_review_prompt"
description: "Generate a code review prompt"
variables:
  - name: "code"
    type: "string"
  - name: "language"
    type: "string"
  - name: "focus_areas"
    type: "list[str]"

template: |
  # Code Review Prompt

  You are reviewing {{ language }} code.

  Code to review:
  ```{{ language }}
  {{ code }}
  ```

  Focus areas:
  {% for area in focus_areas %}
  - {{ area }}
  {% endfor %}

  Provide detailed feedback.
```

**BAML Equivalent:**
```baml
class CodeReviewRequest {
  code string
  language string
  focus_areas string[]
}

class CodeReviewPrompt {
  prompt_text string
}

function GenerateCodeReviewPrompt(request: CodeReviewRequest) -> CodeReviewPrompt {
  client GPT4

  prompt #"
    Create a code review prompt for {{ request.language }} code.

    Code:
    {{ request.code }}

    Focus on: {{ request.focus_areas }}

    {{ ctx.output_format }}
  "#
}
```

**Analysis:**
- ✅ **YAML**: Simple Jinja2 logic, renders instantly, no API costs
- ❌ **BAML**: Uses LLM to generate a prompt (meta-prompting), expensive, complex
- **Winner**: YAML (BAML is overkill here)

### Example 3: Structured Data Extraction (Where BAML Shines)

**Hypothetical Future Feature: Extract MCP Server Config from Description**

**BAML Approach:**
```baml
class MCPServerConfig {
  name string
  description string
  tools ToolDefinition[]
  resources ResourceDefinition[]
  prompts PromptDefinition[]
}

function ExtractServerConfig(user_description: string) -> MCPServerConfig {
  client ClaudeOpus

  prompt #"
    User wants to create an MCP server:
    {{ user_description }}

    Extract the server configuration.
    {{ ctx.output_format }}
  "#
}

// Usage
config = b.ExtractServerConfig(
    "Create a weather server with a get_forecast tool and current_weather resource"
)

// Guaranteed structured output
print(config.name)
print(config.tools[0].name)
```

**YAML Approach Would Be:**
```python
# Would need manual parsing
prompt = f"""
Extract server config from: {user_description}

Return JSON:
{{
    "name": "server_name",
    "tools": [...],
    ...
}}
"""

response = llm_call(prompt)
config = json.loads(response)  # Hope it's valid JSON!
```

**Analysis:**
- ❌ **YAML**: Would need manual prompt construction and response parsing
- ✅ **BAML**: Automatic structured output, type-safe, error correction
- **Winner**: BAML (for this use case)

**But**: fips-agents-cli doesn't do this yet! If we add AI-assisted features, reconsider BAML.

---

## 10. Final Recommendation Summary

### DO NOT ADOPT BAML

**Reasons:**

1. **Fundamental Use Case Mismatch**:
   - fips-agents-cli: Static code generation from templates
   - BAML: Runtime LLM function calling with structured outputs
   - These are different problems requiring different tools

2. **Current Approach is Optimal**:
   - YAML + Jinja2 is perfect for template-based code generation
   - Simple, fast, predictable, no external API calls
   - No build complexity, no dependencies, no learning curve

3. **BAML Would Add Complexity Without Value**:
   - Compilation step (baml-cli generate)
   - Learning curve (BAML DSL syntax)
   - Build pipeline changes
   - Container build complexity
   - Potential FIPS issues
   - **Zero benefit for our current use case**

4. **Project Philosophy Alignment**:
   - "Keep prompts easily editable" → YAML ✅, BAML ⚠️
   - "Easy to brief other developers" → YAML ✅, BAML ❌
   - "NEVER mock functionality" → Using BAML when we don't need it would be mock functionality

5. **Future Flexibility**:
   - If we add AI-assisted features, we can adopt BAML then
   - Hybrid approach (YAML + BAML) is possible
   - No need to change what works now

### What to Do Instead

**Short Term (Now):**
1. ✅ Continue using YAML for prompt templates
2. ✅ Enhance Jinja2 template library as needed
3. ✅ Document YAML template structure in CLAUDE.md
4. ✅ Create examples for common prompt patterns

**Medium Term (Next 6-12 months):**
1. Monitor BAML ecosystem maturation
2. Watch for BAML + FastMCP integration developments
3. Evaluate if fips-agents-cli adds AI-assisted features
4. Reassess if use case changes

**Long Term (12+ months):**
1. If adding runtime AI features, prototype BAML integration
2. Conduct pilot project with BAML for new features
3. Validate FIPS compliance if adoption is considered
4. Consider hybrid approach (YAML for templates, BAML for AI features)

### Success Criteria for Future BAML Reconsideration

Only reconsider BAML if **ALL** of these are true:

- [ ] fips-agents-cli adds features requiring runtime LLM calls
- [ ] Structured output parsing provides clear value
- [ ] BAML has proven FIPS compliance
- [ ] Team is willing to accept increased complexity
- [ ] Benefits outweigh costs (measured, not assumed)
- [ ] Hybrid YAML+BAML approach is architecturally sound

**Until then: Stick with YAML.** ✅

---

## Appendix A: BAML Resources

### Official Documentation
- **Website**: https://boundaryml.com/
- **Docs**: https://docs.boundaryml.com/
- **GitHub**: https://github.com/BoundaryML/baml
- **Examples**: https://github.com/BoundaryML/baml-examples

### Community Resources
- **baml-agents**: https://github.com/Elijas/baml-agents (MCP integration examples)
- **MCP Integration Notebook**: https://github.com/Elijas/baml-agents/blob/main/notebooks/03_baml_with_mcp_tools.ipynb

### Articles and Guides
- "BAML vs YAML vs JSON for LLM Prompts": https://www.augmentcode.com/guides/baml-vs-poml-vs-yaml-vs-json-for-llm-prompts
- "Seven Features That Make BAML Ideal": https://gradientflow.com/seven-features-that-make-baml-ideal-for-ai-developers/
- "BAML and Future of Agentic Workflows": https://thedataquarry.com/blog/baml-and-future-agentic-workflows/

---

## Appendix B: Questions for Further Research

If reconsidering BAML in the future, investigate:

1. **FIPS Compliance**:
   - Has BAML runtime been FIPS-validated?
   - What cryptographic libraries does the Rust core use?
   - Are there FIPS-compliant builds available?

2. **FastMCP Integration**:
   - Has official BAML + FastMCP integration emerged?
   - Are there recommended patterns from FastMCP maintainers?
   - Does FastMCP 3.0+ include BAML support?

3. **Enterprise Adoption**:
   - Are any Red Hat customers using BAML in production?
   - What are the lessons learned from enterprise BAML deployments?
   - Are there OpenShift-specific BAML deployment guides?

4. **Tooling Maturity**:
   - Is baml-cli available as Red Hat RPM or UBI package?
   - Does JetBrains support improve?
   - Are there vim/emacs plugins?

5. **Performance Characteristics**:
   - What is the memory footprint of baml_client?
   - How large are generated client packages?
   - What is the compilation time for large BAML projects?

---

## Appendix C: Glossary

- **BAML**: Basically a Made-up Language - DSL for typed LLM interactions
- **DSL**: Domain-Specific Language
- **FastMCP**: Python framework for building MCP servers
- **MCP**: Model Context Protocol - standard for LLM tool integration
- **SAP**: Schema-Aligned Parsing - BAML's output correction technique
- **baml-cli**: Command-line tool for generating BAML client code
- **baml_client**: Auto-generated Python package from .baml files
- **Jinja2**: Python templating engine (used in current approach)
- **Pydantic**: Python data validation library (used by both approaches)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Reviewed By**: Claude Code (Subagent)
**Status**: Final Recommendation
