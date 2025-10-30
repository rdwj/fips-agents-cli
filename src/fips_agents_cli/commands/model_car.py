"""Create command for generating ModelCar container projects."""

import sys

import click
from rich.console import Console
from rich.panel import Panel

from fips_agents_cli.tools.filesystem import resolve_target_path, validate_target_directory
from fips_agents_cli.tools.validation import parse_huggingface_repo, validate_quay_uri

console = Console()


def derive_project_name(hf_repo_id: str) -> str:
    """
    Derive project directory name from HuggingFace repo ID.

    Extracts model name from org/model format and converts to lowercase with hyphens.

    Args:
        hf_repo_id: HuggingFace repository ID (e.g., ibm-granite/granite-3.1-2b-instruct)

    Returns:
        str: Project directory name (e.g., granite-3.1-2b-instruct)

    Example:
        >>> derive_project_name("ibm-granite/granite-3.1-2b-instruct")
        'granite-3.1-2b-instruct'
        >>> derive_project_name("RedHatAI/Qwen3-VL-235B-A22B-Instruct-FP8-dynamic")
        'qwen3-vl-235b-a22b-instruct-fp8-dynamic'
    """
    # Extract model name (everything after the slash)
    model_name = hf_repo_id.split("/")[-1]

    # Convert to lowercase for directory name
    # Keep hyphens as-is, they're valid in directory names
    return model_name.lower()


def generate_download_script(hf_repo_id: str) -> str:
    """Generate download_model.py script content."""
    return f'''#!/usr/bin/env python3
"""Download model from HuggingFace."""

from huggingface_hub import snapshot_download

# Specify the Hugging Face repository containing the model
model_repo = "{hf_repo_id}"

print(f"Downloading model from {{model_repo}}...")
print("This may take a while depending on model size and network speed.")

snapshot_download(
    repo_id=model_repo,
    local_dir="./models",
    allow_patterns=["*.safetensors", "*.json", "*.txt", "*.md"],
)

print("✅ Model downloaded successfully to ./models")
print("Next step: Run ./build-and-push.sh to build and push the container")
'''


def generate_containerfile() -> str:
    """Generate Containerfile content."""
    return """# ModelCar Containerfile
# Uses Red Hat UBI9 micro for minimal footprint

FROM registry.access.redhat.com/ubi9/ubi-micro:9.4

# Copy the model files from the local models directory
COPY /models /models

# Run as non-root user
USER 1001
"""


def generate_build_script(image_tag: str, quay_uri: str) -> str:
    """Generate build-and-push.sh script content."""
    return f"""#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "ModelCar Build and Push Script"
echo "=========================================="
echo ""

# Check if models directory exists and has content
if [ ! -d "./models" ] || [ -z "$(ls -A ./models)" ]; then
    echo "❌ Error: models/ directory is empty or does not exist"
    echo "Please run ./download.sh first to download the model"
    exit 1
fi

# Check available disk space
echo "Checking available disk space..."
if command -v df &> /dev/null; then
    available=$(df -g . 2>/dev/null | awk 'NR==2 {{print $4}}' || df -h . | awk 'NR==2 {{print $4}}')
    echo "Available space: $available"
    echo ""
    echo "⚠️  Warning: Container builds require significant disk space"
    echo "Recommended: 20GB+ available"
    read -p "Continue with build? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Build cancelled"
        exit 0
    fi
fi

# Build container
echo ""
echo "Building container image..."
echo "Image tag: {image_tag}"
podman build . -t {image_tag} --platform linux/amd64

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""

# Push to registry
echo "Pushing to registry..."
echo "URI: {quay_uri}"
podman push {image_tag} {quay_uri}

if [ $? -ne 0 ]; then
    echo "❌ Push failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Successfully pushed to {quay_uri}"
echo "=========================================="
echo ""
echo "💡 To reclaim disk space, run: ./cleanup.sh"
echo ""
echo "Deployment in OpenShift AI:"
echo "  - Model name: {image_tag.split(':')[1] if ':' in image_tag else image_tag}"
echo "  - Runtime: vLLM ServingRuntime"
echo "  - Source type: OCI - v1"
echo "  - URI: oci://{quay_uri}"
"""


def generate_cleanup_script() -> str:
    """Generate cleanup.sh script content."""
    return """#!/bin/bash

echo "=========================================="
echo "ModelCar Cleanup Script"
echo "=========================================="
echo ""
echo "This will delete the models/ directory to reclaim disk space."
echo ""

# Check if models directory exists
if [ ! -d "./models" ]; then
    echo "ℹ️  models/ directory does not exist - nothing to clean up"
    exit 0
fi

# Calculate size
if command -v du &> /dev/null; then
    size=$(du -sh ./models 2>/dev/null | cut -f1 || echo "unknown")
    echo "Current size of models/: $size"
    echo ""
fi

read -p "Delete models/ directory? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

rm -rf ./models

echo "✅ models/ directory deleted"
echo ""
echo "To rebuild the container image, you'll need to run ./download.sh again"
"""


def generate_requirements() -> str:
    """Generate requirements.txt content."""
    return "huggingface-hub\n"


def generate_gitignore() -> str:
    """Generate .gitignore content."""
    return """# Model files (DO NOT COMMIT)
models/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""


def generate_readme(hf_repo_id: str, model_name: str, image_tag: str, quay_uri: str) -> str:
    """Generate README.md content."""
    return f"""# ModelCar: {model_name}

This directory contains scripts to package the **{model_name}** model from HuggingFace into a ModelCar container image for deployment on OpenShift AI.

## ⚠️ Important: Do Not Commit to Git

**This is a temporary workspace for creating ModelCar images.**

- The source of truth is the HuggingFace repository
- Model files can be very large (multi-GB)
- This directory is for building and pushing containers only
- Delete this directory after pushing the image to your registry

## HuggingFace Source

**Repository:** [{hf_repo_id}](https://huggingface.co/{hf_repo_id})

Check the HuggingFace repository for model details, size, and licensing information.

## Usage

### 1. Download the Model

```bash
chmod +x download.sh
./download.sh
```

This downloads the model from HuggingFace to the local `models/` directory. Depending on the model size and your network speed, this may take considerable time.

### 2. Build and Push Container

```bash
chmod +x build-and-push.sh
./build-and-push.sh
```

This script will:
- Check that model files exist
- Warn about disk space requirements
- Build the container image with Podman
- Push the image to your Quay registry

The build uses `--platform linux/amd64` for OpenShift compatibility.

### 3. Clean Up (Optional)

```bash
chmod +x cleanup.sh
./cleanup.sh
```

This deletes the local `models/` directory to reclaim disk space. The model is safely stored in your container registry.

## Container Details

- **Image Tag:** `{image_tag}`
- **Registry URI:** `{quay_uri}`
- **Base Image:** Red Hat UBI9 Micro (minimal footprint)
- **Platform:** linux/amd64

## Deployment on OpenShift AI

To deploy this model in OpenShift AI:

1. Create a new project or select an existing one
2. Select "Single-model serving"
3. Click "Deploy model" and configure:
   - **Model name:** `{model_name}`
   - **Runtime:** vLLM ServingRuntime
   - **Replicas:** 1
   - **Size:** Small (or appropriate for your model)
   - **Accelerator:** nvidia-gpu (quantity: 1 or more)
   - **Enable model route:** Yes

4. For source location, create a URI connection:
   - **Type:** OCI - v1
   - **URI:** `oci://{quay_uri}`

5. Deploy and monitor pod creation

### Handling Timeouts

If deployment exceeds 10 minutes, add this annotation to the InferenceService predictor spec:

```yaml
serving.knative.dev/progress-deadline: 30m
```

## Files in This Directory

| File | Purpose |
|------|---------|
| `download.sh` | Downloads model from HuggingFace |
| `build-and-push.sh` | Builds and pushes container image |
| `cleanup.sh` | Deletes local model files |
| `download_model.py` | Python script called by download.sh |
| `Containerfile` | Container build instructions |
| `requirements.txt` | Python dependencies for downloading |
| `.gitignore` | Excludes model files from git |

## Troubleshooting

**Download fails:**
- Check internet connectivity
- Verify HuggingFace repository is accessible
- Some models require authentication - see HuggingFace docs

**Build fails:**
- Ensure Podman is installed and running
- Check available disk space (20GB+ recommended)
- Verify models/ directory is not empty

**Push fails:**
- Verify you're logged into Quay: `podman login quay.io`
- Check repository permissions
- Ensure repository exists in Quay

## Additional Resources

- [OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/)
- [ModelCar Guide](https://developers.redhat.com/articles/2025/01/30/build-and-deploy-modelcar-container-openshift-ai)
- [HuggingFace Hub Documentation](https://huggingface.co/docs/hub)
- [Podman Documentation](https://podman.io/docs)
"""


@click.command("model-car")
@click.argument("hf_repo")
@click.argument("quay_uri")
@click.option(
    "--target-dir",
    "-t",
    default=None,
    help="Target directory for the project (default: current directory)",
)
def model_car(hf_repo: str, quay_uri: str, target_dir: str | None):
    """
    Create a ModelCar project for packaging HuggingFace models.

    HF_REPO can be a full URL or repository ID:
    - https://huggingface.co/ibm-granite/granite-3.1-2b-instruct
    - ibm-granite/granite-3.1-2b-instruct

    QUAY_URI must include tag:
    - quay.io/wjackson/models:granite-3.1-2b-instruct

    Example:
        fips-agents create model-car ibm-granite/granite-3.1-2b-instruct \\
            quay.io/wjackson/models:granite-3.1-2b-instruct
    """
    try:
        console.print("\n[bold cyan]Creating ModelCar Project[/bold cyan]\n")

        # Step 1: Parse and validate HuggingFace repository
        hf_repo_id, error = parse_huggingface_repo(hf_repo)
        if not hf_repo_id:
            console.print(f"[red]✗[/red] {error}")
            sys.exit(1)

        console.print(f"[green]✓[/green] HuggingFace repository: {hf_repo_id}")

        # Step 2: Validate Quay URI
        is_valid, error, components = validate_quay_uri(quay_uri)
        if not is_valid:
            console.print(f"[red]✗[/red] {error}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Container registry URI: {quay_uri}")

        # Step 3: Derive project name from model name
        project_name = derive_project_name(hf_repo_id)
        model_name = hf_repo_id.split("/")[-1]  # Keep original case for display

        console.print(f"[green]✓[/green] Project directory: {project_name}")

        # Step 4: Resolve and validate target directory
        target_path = resolve_target_path(project_name, target_dir)

        is_valid, error_msg = validate_target_directory(target_path, allow_existing=False)
        if not is_valid:
            console.print(f"[red]✗[/red] {error_msg}")
            console.print(
                "\n[yellow]Hint:[/yellow] Choose a different name or remove the existing directory"
            )
            sys.exit(1)

        console.print(f"[green]✓[/green] Target path: {target_path}")

        # Step 5: Create project directory structure
        console.print("\n[cyan]Creating project structure...[/cyan]")

        target_path.mkdir(parents=True, exist_ok=True)
        models_dir = target_path / "models"
        models_dir.mkdir(exist_ok=True)

        # Generate image tag (use just the tag part from quay_uri)
        image_tag = f"models:{components['tag']}"

        # Step 6: Generate all files
        # Generate download_model.py content separately
        download_py_content = f"""from huggingface_hub import snapshot_download

# Specify the Hugging Face repository containing the model
model_repo = "{hf_repo_id}"

print(f"Downloading model from {{model_repo}}...")
print("This may take a while depending on model size and network speed.")

snapshot_download(
    repo_id=model_repo,
    local_dir="./models",
    allow_patterns=["*.safetensors", "*.json", "*.txt", "*.md"],
)

print("✅ Model downloaded successfully to ./models")
print("Next step: Run ./build-and-push.sh to build and push the container")
"""

        files_to_create = {
            "download.sh": generate_download_script(hf_repo_id),
            "download_model.py": download_py_content,
            "Containerfile": generate_containerfile(),
            "build-and-push.sh": generate_build_script(image_tag, quay_uri),
            "cleanup.sh": generate_cleanup_script(),
            "requirements.txt": generate_requirements(),
            ".gitignore": generate_gitignore(),
            "README.md": generate_readme(hf_repo_id, model_name, image_tag, quay_uri),
        }

        for filename, content in files_to_create.items():
            file_path = target_path / filename
            file_path.write_text(content)

            # Make shell scripts executable
            if filename.endswith(".sh"):
                file_path.chmod(0o755)

            console.print(f"  [green]✓[/green] Created {filename}")

        # Step 7: Success message with instructions
        success_message = f"""
[bold green]✓ ModelCar project created successfully![/bold green]

[bold cyan]Project Details:[/bold cyan]
  • Model: {model_name}
  • HuggingFace: {hf_repo_id}
  • Container: {quay_uri}
  • Location: {target_path}

[bold cyan]Next Steps:[/bold cyan]

  1. Navigate to your project:
     [dim]cd {target_path.name}[/dim]

  2. Download the model (this may take a while):
     [dim]./download.sh[/dim]

  3. Build and push the container:
     [dim]./build-and-push.sh[/dim]

  4. (Optional) Clean up local files:
     [dim]./cleanup.sh[/dim]

[bold cyan]Deployment:[/bold cyan]
  Deploy in OpenShift AI using:
  • Runtime: vLLM ServingRuntime
  • Source type: OCI - v1
  • URI: oci://{quay_uri}

[bold yellow]⚠️  Important:[/bold yellow]
  • Do NOT commit this directory to git
  • The source of truth is the HuggingFace repository
  • Delete this directory after pushing to your registry

Check README.md for detailed instructions! 🚀
"""

        console.print(Panel(success_message, border_style="green", padding=(1, 2)))

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)
