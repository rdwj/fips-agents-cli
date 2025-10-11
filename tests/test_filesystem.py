"""Tests for filesystem utilities."""

from pathlib import Path

from fips_agents_cli.tools.filesystem import (
    check_directory_empty,
    ensure_directory_exists,
    resolve_target_path,
    validate_target_directory,
)


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_existing_directory(self, temp_dir):
        """Test with an existing directory."""
        assert ensure_directory_exists(temp_dir, create=False)

    def test_nonexistent_directory_no_create(self, temp_dir):
        """Test with nonexistent directory when create=False."""
        new_dir = temp_dir / "nonexistent"
        assert not ensure_directory_exists(new_dir, create=False)

    def test_nonexistent_directory_with_create(self, temp_dir):
        """Test creating a nonexistent directory."""
        new_dir = temp_dir / "new_directory"
        assert ensure_directory_exists(new_dir, create=True)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_file_not_directory(self, temp_dir):
        """Test with a file path instead of directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")
        assert not ensure_directory_exists(file_path, create=False)


class TestCheckDirectoryEmpty:
    """Tests for check_directory_empty function."""

    def test_empty_directory(self, temp_dir):
        """Test with an empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        assert check_directory_empty(empty_dir)

    def test_directory_with_files(self, temp_dir):
        """Test with directory containing files."""
        dir_with_files = temp_dir / "with_files"
        dir_with_files.mkdir()
        (dir_with_files / "file.txt").write_text("test")
        assert not check_directory_empty(dir_with_files)

    def test_directory_with_subdirs(self, temp_dir):
        """Test with directory containing subdirectories."""
        dir_with_subdirs = temp_dir / "with_subdirs"
        dir_with_subdirs.mkdir()
        (dir_with_subdirs / "subdir").mkdir()
        assert not check_directory_empty(dir_with_subdirs)

    def test_nonexistent_directory(self, temp_dir):
        """Test with nonexistent directory (should return True)."""
        nonexistent = temp_dir / "nonexistent"
        assert check_directory_empty(nonexistent)

    def test_file_instead_of_directory(self, temp_dir):
        """Test with a file path."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")
        assert not check_directory_empty(file_path)


class TestValidateTargetDirectory:
    """Tests for validate_target_directory function."""

    def test_valid_nonexistent_directory(self, temp_dir):
        """Test with a valid nonexistent directory."""
        target = temp_dir / "new_project"
        is_valid, error = validate_target_directory(target)
        assert is_valid
        assert error is None

    def test_existing_directory_not_allowed(self, temp_dir):
        """Test with existing directory when not allowed."""
        existing = temp_dir / "existing"
        existing.mkdir()
        is_valid, error = validate_target_directory(existing, allow_existing=False)
        assert not is_valid
        assert "already exists" in error

    def test_existing_empty_directory_allowed(self, temp_dir):
        """Test with existing empty directory when allowed."""
        existing = temp_dir / "existing"
        existing.mkdir()
        is_valid, error = validate_target_directory(existing, allow_existing=True)
        assert is_valid
        assert error is None

    def test_existing_nonempty_directory(self, temp_dir):
        """Test with existing non-empty directory."""
        existing = temp_dir / "existing"
        existing.mkdir()
        (existing / "file.txt").write_text("test")
        is_valid, error = validate_target_directory(existing, allow_existing=True)
        assert not is_valid
        assert "not empty" in error

    def test_file_instead_of_directory(self, temp_dir):
        """Test with a file path instead of directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")
        is_valid, error = validate_target_directory(file_path, allow_existing=True)
        assert not is_valid
        assert "not a directory" in error


class TestResolveTargetPath:
    """Tests for resolve_target_path function."""

    def test_with_target_dir(self, temp_dir):
        """Test with explicit target directory."""
        result = resolve_target_path("my-project", str(temp_dir))
        expected = temp_dir / "my-project"
        # Use resolve() to handle symlinks like /var -> /private/var on macOS
        assert result.resolve() == expected.resolve()

    def test_without_target_dir(self):
        """Test without target directory (defaults to cwd)."""
        result = resolve_target_path("my-project")
        expected = Path.cwd() / "my-project"
        assert result == expected

    def test_absolute_path_resolution(self, temp_dir):
        """Test that result is absolute path."""
        result = resolve_target_path("my-project", str(temp_dir))
        assert result.is_absolute()
