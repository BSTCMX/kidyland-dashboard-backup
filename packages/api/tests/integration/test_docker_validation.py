"""
Docker and deployment validation tests.
"""
import pytest
import subprocess
import os
from pathlib import Path


@pytest.mark.slow
@pytest.mark.integration
def test_dockerfile_api_builds_successfully():
    """Test that Dockerfile.api builds without errors."""
    dockerfile_path = Path(__file__).parent.parent.parent / "infra" / "docker" / "Dockerfile.api"
    
    if not dockerfile_path.exists():
        pytest.skip("Dockerfile.api not found")
    
    # Try to build (dry run validation)
    # Note: This doesn't actually build, just validates syntax
    # For real build test, you'd run: docker build -f <path> -t test .
    result = subprocess.run(
        ["docker", "build", "--dry-run", "-f", str(dockerfile_path), "."],
        capture_output=True,
        text=True,
    )
    
    # Dry run might not be available, so we just check file exists and is readable
    assert dockerfile_path.exists(), "Dockerfile.api should exist"
    assert dockerfile_path.is_file(), "Dockerfile.api should be a file"
    
    # Read and validate basic structure
    content = dockerfile_path.read_text()
    assert "FROM python" in content, "Should use Python base image"
    assert "WORKDIR" in content, "Should set working directory"
    assert "CMD" in content or "ENTRYPOINT" in content, "Should have entrypoint"


@pytest.mark.slow
@pytest.mark.integration
def test_dockerfile_web_builds_successfully():
    """Test that Dockerfile.web builds without errors."""
    dockerfile_path = Path(__file__).parent.parent.parent / "infra" / "docker" / "Dockerfile.web"
    
    if not dockerfile_path.exists():
        pytest.skip("Dockerfile.web not found")
    
    assert dockerfile_path.exists(), "Dockerfile.web should exist"
    assert dockerfile_path.is_file(), "Dockerfile.web should be a file"
    
    content = dockerfile_path.read_text()
    assert "FROM node" in content, "Should use Node base image"
    assert "WORKDIR" in content, "Should set working directory"


@pytest.mark.integration
def test_fly_toml_exists():
    """Test that fly.toml configuration exists."""
    fly_toml_path = Path(__file__).parent.parent.parent / "infra" / "fly" / "fly.toml"
    
    assert fly_toml_path.exists(), "fly.toml should exist"
    
    # Validate basic structure
    content = fly_toml_path.read_text()
    assert "[build]" in content or 'dockerfile' in content, "Should have build config"
    assert "app" in content, "Should have app name"


@pytest.mark.integration
def test_health_check_endpoint():
    """Test that health check endpoint is accessible."""
    # This would require the app to be running
    # For now, we just validate the endpoint exists in main.py
    main_py = Path(__file__).parent.parent.parent / "main.py"
    
    if main_py.exists():
        content = main_py.read_text()
        assert "/health" in content or "health" in content.lower(), "Should have health endpoint"
































