"""
Tests for argument_validator module
"""
import pytest
import argparse
from unittest.mock import Mock, patch
from src.open_api_mock_build.argument_validator import (
    validate_registry_format,
    validate_image_format,
    validate_arguments
)


class TestValidateRegistryFormat:
    """Test cases for validate_registry_format function"""

    def test_valid_registry_formats(self):
        """Test valid registry formats"""
        valid_registries = [
            None,
            "",
            "docker.io",
            "registry.example.com",
            "123456789.dkr.ecr.us-east-1.amazonaws.com",
            "gcr.io",
            "us.gcr.io",
            "example.azurecr.io",
            "us-central1-docker.pkg.dev"
        ]
        
        for registry in valid_registries:
            is_valid, error_msg = validate_registry_format(registry)
            assert is_valid, f"Registry '{registry}' should be valid, but got error: {error_msg}"
            assert error_msg == ""

    def test_invalid_ecr_registry_with_image_name(self):
        """Test ECR registry with image name (should be invalid)"""
        registry = "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app"
        is_valid, error_msg = validate_registry_format(registry)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg
        assert "123456789.dkr.ecr.us-east-1.amazonaws.com" in error_msg
        assert "my-app:latest" in error_msg

    def test_invalid_gcr_registry_with_image_name(self):
        """Test GCR registry with image name (should be invalid)"""
        registry = "gcr.io/project-id/my-app"
        is_valid, error_msg = validate_registry_format(registry)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg
        assert "gcr.io" in error_msg
        assert "project-id/my-app:latest" in error_msg

    def test_invalid_acr_registry_with_image_name(self):
        """Test ACR registry with image name (should be invalid)"""
        registry = "example.azurecr.io/my-app"
        is_valid, error_msg = validate_registry_format(registry)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg
        assert "example.azurecr.io" in error_msg
        assert "my-app:latest" in error_msg

    def test_invalid_gar_registry_with_image_name(self):
        """Test GAR registry with image name (should be invalid)"""
        registry = "us-central1-docker.pkg.dev/project-id/repo/my-app"
        is_valid, error_msg = validate_registry_format(registry)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg
        assert "us-central1-docker.pkg.dev" in error_msg
        assert "project-id/repo/my-app:latest" in error_msg

    def test_registry_with_complex_path(self):
        """Test registry with complex path structure"""
        registry = "123456789.dkr.ecr.ap-northeast-1.amazonaws.com/test-mock-sandbox/my-app"
        is_valid, error_msg = validate_registry_format(registry)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg
        assert "123456789.dkr.ecr.ap-northeast-1.amazonaws.com" in error_msg
        assert "test-mock-sandbox/my-app:latest" in error_msg


class TestValidateImageFormat:
    """Test cases for validate_image_format function"""

    def test_valid_image_formats(self):
        """Test valid image formats"""
        valid_images = [
            "my-app",
            "my-app:latest",
            "my-app:1.0.0",
            "namespace/my-app",
            "namespace/my-app:latest",
            "registry.com/namespace/my-app:v1.0.0"
        ]
        
        for image in valid_images:
            is_valid, error_msg = validate_image_format(image)
            assert is_valid, f"Image '{image}' should be valid, but got error: {error_msg}"
            assert error_msg == ""

    def test_empty_image_name(self):
        """Test empty image name"""
        is_valid, error_msg = validate_image_format("")
        assert not is_valid
        assert "Image name cannot be empty" in error_msg

    def test_none_image_name(self):
        """Test None image name"""
        is_valid, error_msg = validate_image_format(None)
        assert not is_valid
        assert "Image name cannot be empty" in error_msg

    def test_image_name_with_leading_slash(self):
        """Test image name starting with slash"""
        is_valid, error_msg = validate_image_format("/my-app")
        assert not is_valid
        assert "Image name cannot start or end with '/'" in error_msg

    def test_image_name_with_trailing_slash(self):
        """Test image name ending with slash"""
        is_valid, error_msg = validate_image_format("my-app/")
        assert not is_valid
        assert "Image name cannot start or end with '/'" in error_msg


class TestValidateArguments:
    """Test cases for validate_arguments function"""

    def create_mock_args(self, registry=None, image="my-app:latest", verbose=False):
        """Helper method to create mock arguments"""
        args = Mock(spec=argparse.Namespace)
        args.registry = registry
        args.image = image
        args.verbose = verbose
        return args

    @patch('src.open_api_mock_build.argument_validator.get_logger')
    def test_valid_arguments(self, mock_get_logger):
        """Test valid arguments"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = self.create_mock_args(
            registry="123456789.dkr.ecr.us-east-1.amazonaws.com",
            image="my-app:latest",
            verbose=True
        )
        
        is_valid, error_msg = validate_arguments(args)
        
        assert is_valid
        assert error_msg == ""
        mock_logger.info.assert_called_once_with("✓ Command line arguments validation passed")

    @patch('src.open_api_mock_build.argument_validator.get_logger')
    def test_invalid_registry_in_arguments(self, mock_get_logger):
        """Test invalid registry format in arguments"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = self.create_mock_args(
            registry="123456789.dkr.ecr.us-east-1.amazonaws.com/my-app",
            image="my-app:latest"
        )
        
        is_valid, error_msg = validate_arguments(args)
        
        assert not is_valid
        assert "Registry URL should not include image name" in error_msg

    @patch('src.open_api_mock_build.argument_validator.get_logger')
    def test_invalid_image_in_arguments(self, mock_get_logger):
        """Test invalid image format in arguments"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = self.create_mock_args(
            registry="123456789.dkr.ecr.us-east-1.amazonaws.com",
            image=""
        )
        
        is_valid, error_msg = validate_arguments(args)
        
        assert not is_valid
        assert "Image name cannot be empty" in error_msg

    @patch('src.open_api_mock_build.argument_validator.get_logger')
    def test_verbose_false_no_log(self, mock_get_logger):
        """Test that no success log is printed when verbose=False"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = self.create_mock_args(
            registry="123456789.dkr.ecr.us-east-1.amazonaws.com",
            image="my-app:latest",
            verbose=False
        )
        
        is_valid, error_msg = validate_arguments(args)
        
        assert is_valid
        assert error_msg == ""
        mock_logger.info.assert_not_called()

    @patch('src.open_api_mock_build.argument_validator.get_logger')
    def test_no_registry_specified(self, mock_get_logger):
        """Test validation with no registry specified"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        args = self.create_mock_args(
            registry=None,
            image="my-app:latest",
            verbose=True
        )
        
        is_valid, error_msg = validate_arguments(args)
        
        assert is_valid
        assert error_msg == ""
        mock_logger.info.assert_called_once_with("✓ Command line arguments validation passed")


if __name__ == "__main__":
    pytest.main([__file__])
