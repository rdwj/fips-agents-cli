"""Tests for the model-car command."""

from unittest.mock import patch

from fips_agents_cli.cli import cli


class TestCreateModelCar:
    """Tests for the 'create model-car' command."""

    def test_help_message(self, cli_runner):
        """Test that help message is displayed correctly."""
        result = cli_runner.invoke(cli, ["create", "model-car", "--help"])
        assert result.exit_code == 0
        assert "Create a ModelCar project" in result.output
        assert "HF_REPO" in result.output
        assert "QUAY_URI" in result.output

    def test_successful_creation_with_url(self, cli_runner, temp_dir):
        """Test successful project creation with HuggingFace URL."""
        hf_url = "https://huggingface.co/ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_url, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        assert "ModelCar project created successfully" in result.output
        assert "Logged into quay.io as testuser" in result.output

        # Check project directory was created with lowercase name
        project_dir = temp_dir / "granite-3.1-2b-instruct"
        assert project_dir.exists()

        # Check all required files were created
        assert (project_dir / "download.sh").exists()
        assert (project_dir / "download_model.py").exists()
        assert (project_dir / "Containerfile").exists()
        assert (project_dir / "build-and-push.sh").exists()
        assert (project_dir / "cleanup.sh").exists()
        assert (project_dir / "cleanup-old-images.sh").exists()
        assert (project_dir / "requirements.txt").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / ".fips-agents-cli").exists()
        assert (project_dir / ".fips-agents-cli" / "info.json").exists()
        assert (project_dir / ".fips-agents-cli" / "CLAUDE.md").exists()
        assert (project_dir / "README.md").exists()
        assert (project_dir / "models").exists()
        assert (project_dir / "models").is_dir()

        # Check shell scripts are executable
        assert (project_dir / "download.sh").stat().st_mode & 0o111
        assert (project_dir / "build-and-push.sh").stat().st_mode & 0o111
        assert (project_dir / "cleanup.sh").stat().st_mode & 0o111
        assert (project_dir / "cleanup-old-images.sh").stat().st_mode & 0o111

    def test_successful_creation_with_repo_id(self, cli_runner, temp_dir):
        """Test successful project creation with HuggingFace repo ID."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        assert "ModelCar project created successfully" in result.output

        project_dir = temp_dir / "granite-3.1-2b-instruct"
        assert project_dir.exists()

    def test_quay_uri_with_https_protocol(self, cli_runner, temp_dir):
        """Test that Quay URI with https:// protocol is accepted."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "https://quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        assert "ModelCar project created successfully" in result.output
        assert "Logged into quay.io as testuser" in result.output

        project_dir = temp_dir / "granite-3.1-2b-instruct"
        assert project_dir.exists()

    def test_not_logged_into_registry(self, cli_runner, temp_dir):
        """Test that not being logged into registry shows error."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        # Override the auto-use fixture for this specific test
        with patch(
            "fips_agents_cli.commands.model_car.check_registry_login",
            return_value=(False, "Not logged in to registry"),
        ):
            result = cli_runner.invoke(
                cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
            )

        assert result.exit_code == 1
        assert "Not logged into quay.io" in result.output
        assert "podman login quay.io" in result.output

    def test_mixed_case_model_name(self, cli_runner, temp_dir):
        """Test that mixed case model names are converted to lowercase for directory."""
        hf_repo = "RedHatAI/Qwen3-VL-235B-A22B-Instruct-FP8-dynamic"
        quay_uri = "quay.io/wjackson/models:Qwen3-VL-235B"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        # Directory should be lowercase
        project_dir = temp_dir / "qwen3-vl-235b-a22b-instruct-fp8-dynamic"
        assert project_dir.exists()

    def test_generated_files_contain_correct_info(self, cli_runner, temp_dir):
        """Test that generated files contain the correct parameters."""
        hf_repo = "ibm-granite/granite-docling-258M"
        quay_uri = "quay.io/wjackson/models:granite-docling-258M"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-docling-258m"

        # Check download_model.py contains correct repo
        download_py = (project_dir / "download_model.py").read_text()
        assert hf_repo in download_py
        assert "snapshot_download" in download_py

        # Check Containerfile
        containerfile = (project_dir / "Containerfile").read_text()
        assert "ubi-micro" in containerfile
        assert "COPY models /models" in containerfile

        # Check build-and-push.sh contains correct URIs
        build_script = (project_dir / "build-and-push.sh").read_text()
        assert quay_uri in build_script
        assert "podman build" in build_script
        assert "--platform linux/amd64" in build_script

        # Check README contains correct info
        readme = (project_dir / "README.md").read_text()
        assert hf_repo in readme
        assert quay_uri in readme
        assert "Do Not Commit to Git" in readme

        # Check .gitignore excludes models
        gitignore = (project_dir / ".gitignore").read_text()
        assert "models/" in gitignore

    def test_invalid_hf_url(self, cli_runner, temp_dir):
        """Test that invalid HuggingFace URL is rejected."""
        invalid_url = "https://github.com/some/repo"
        quay_uri = "quay.io/wjackson/models:test"

        result = cli_runner.invoke(
            cli, ["create", "model-car", invalid_url, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Invalid HuggingFace" in result.output

    def test_invalid_hf_repo_id_no_slash(self, cli_runner, temp_dir):
        """Test that HuggingFace repo ID without slash is rejected."""
        invalid_repo = "granite-model"
        quay_uri = "quay.io/wjackson/models:test"

        result = cli_runner.invoke(
            cli, ["create", "model-car", invalid_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Invalid HuggingFace" in result.output

    def test_invalid_hf_repo_id_multiple_slashes(self, cli_runner, temp_dir):
        """Test that HuggingFace repo ID with multiple slashes is rejected."""
        invalid_repo = "org/sub/model"
        quay_uri = "quay.io/wjackson/models:test"

        result = cli_runner.invoke(
            cli, ["create", "model-car", invalid_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Invalid HuggingFace" in result.output

    def test_quay_uri_without_tag(self, cli_runner, temp_dir):
        """Test that Quay URI without tag is rejected."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        invalid_uri = "quay.io/wjackson/models"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, invalid_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Missing tag" in result.output

    def test_quay_uri_with_empty_tag(self, cli_runner, temp_dir):
        """Test that Quay URI with empty tag is rejected."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        invalid_uri = "quay.io/wjackson/models:"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, invalid_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Empty tag" in result.output

    def test_invalid_registry_format(self, cli_runner, temp_dir):
        """Test that invalid registry format is rejected."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        invalid_uri = "wjackson/models:tag"  # Missing registry domain

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, invalid_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "Invalid registry" in result.output

    def test_existing_directory_error(self, cli_runner, temp_dir):
        """Test that existing directory causes an error."""
        existing_dir = temp_dir / "granite-3.1-2b-instruct"
        existing_dir.mkdir()

        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_download_script_instructions(self, cli_runner, temp_dir):
        """Test that download.sh is a bash wrapper script."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        download_script = (project_dir / "download.sh").read_text()
        assert "#!/bin/bash" in download_script
        assert "python3 -m venv venv" in download_script
        assert "source venv/bin/activate" in download_script
        assert "pip install" in download_script
        assert "python3 download_model.py" in download_script

    def test_cleanup_script_functionality(self, cli_runner, temp_dir):
        """Test that cleanup.sh script has proper functionality."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        cleanup_script = (project_dir / "cleanup.sh").read_text()
        assert "rm -rf ./models" in cleanup_script
        assert "Delete models/" in cleanup_script

    def test_cleanup_old_images_script(self, cli_runner, temp_dir):
        """Test that cleanup-old-images.sh script is created with correct content."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        # Check file exists and is executable
        cleanup_old_images = project_dir / "cleanup-old-images.sh"
        assert cleanup_old_images.exists()
        assert cleanup_old_images.stat().st_mode & 0o111

        # Check content
        script_content = cleanup_old_images.read_text()
        assert "#!/bin/bash" in script_content
        assert "ModelCar Image Cleanup" in script_content
        assert 'podman images --filter "reference=models:*"' in script_content
        assert "Only removes ModelCar" in script_content or "models:*" in script_content
        assert "podman rmi" in script_content

    def test_requirements_contains_huggingface_hub(self, cli_runner, temp_dir):
        """Test that requirements.txt contains huggingface-hub."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        requirements = (project_dir / "requirements.txt").read_text()
        assert "huggingface-hub" in requirements

    def test_fips_agents_cli_directory_created(self, cli_runner, temp_dir):
        """Test that .fips-agents-cli directory is created with metadata and CLAUDE.md."""
        import json

        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        # Check directory and files exist
        fips_dir = project_dir / ".fips-agents-cli"
        assert fips_dir.exists()
        assert fips_dir.is_dir()

        info_file = fips_dir / "info.json"
        assert info_file.exists()

        claude_md_file = fips_dir / "CLAUDE.md"
        assert claude_md_file.exists()

        # Check info.json content
        with open(info_file) as f:
            info = json.load(f)

        # Verify structure and content
        assert "generator" in info
        assert info["generator"]["tool"] == "fips-agents-cli"
        assert info["generator"]["command"] == "create model-car"
        assert "version" in info["generator"]

        assert "source" in info
        assert info["source"]["type"] == "huggingface"
        assert info["source"]["repository"] == hf_repo
        assert info["source"]["url"] == f"https://huggingface.co/{hf_repo}"

        assert "destination" in info
        assert info["destination"]["type"] == "container-registry"
        assert info["destination"]["uri"] == quay_uri
        assert info["destination"]["registry"] == "quay.io"

        assert "project" in info
        assert info["project"]["name"] == "granite-3.1-2b-instruct"
        assert "created_at" in info["project"]

        # Check CLAUDE.md content
        claude_md_content = claude_md_file.read_text()
        assert "CLAUDE.md - ModelCar Project" in claude_md_content
        assert hf_repo in claude_md_content
        assert quay_uri in claude_md_content
        assert "granite-3.1-2b-instruct" in claude_md_content
        assert "temporary workspace" in claude_md_content
        assert "OpenShift AI Deployment" in claude_md_content

    def test_build_script_includes_cleanup_prompts(self, cli_runner, temp_dir):
        """Test that build script includes cleanup prompts."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        project_dir = temp_dir / "granite-3.1-2b-instruct"

        build_script = (project_dir / "build-and-push.sh").read_text()
        assert "Delete local container image" in build_script
        assert "Delete models/ directory to reclaim disk space" in build_script
        assert "podman rmi" in build_script
        assert "Cleanup Options" in build_script

    def test_success_message_instructions(self, cli_runner, temp_dir):
        """Test that success message contains proper instructions."""
        hf_repo = "ibm-granite/granite-3.1-2b-instruct"
        quay_uri = "quay.io/wjackson/models:granite-3.1-2b-instruct"

        result = cli_runner.invoke(
            cli, ["create", "model-car", hf_repo, quay_uri, "--target-dir", str(temp_dir)]
        )

        assert result.exit_code == 0
        assert "./download.sh" in result.output
        assert "./build-and-push.sh" in result.output
        assert "Will prompt to delete local image after push" in result.output
        assert "Will prompt to delete models/ directory" in result.output
        assert "Do NOT commit" in result.output
        assert "oci://" in result.output


class TestModelCarValidation:
    """Tests for model-car validation utilities."""

    def test_various_valid_hf_formats(self, cli_runner, temp_dir):
        """Test various valid HuggingFace repository formats."""
        valid_combos = [
            ("ibm-granite/granite-3.1-2b", "quay.io/user/models:tag"),
            ("Org123/Model-Name_123", "quay.io/user/repo:v1.0"),
            (
                "https://huggingface.co/ibm-granite/granite-3.1-2b",
                "registry.example.com/org/repo:latest",
            ),
        ]

        for hf_repo, quay_uri in valid_combos:
            result = cli_runner.invoke(
                cli,
                [
                    "create",
                    "model-car",
                    hf_repo,
                    quay_uri,
                    "--target-dir",
                    str(temp_dir / f"test-{hf_repo.split('/')[-1].lower()}"),
                ],
            )
            # Should not show validation errors for these formats
            assert "Invalid HuggingFace" not in result.output
            assert "Invalid registry" not in result.output
