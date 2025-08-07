import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import docker.errors
from open_api_mock_build import container_builder


class TestContainerBuilder:
    """Test cases for container builder functions"""

    @patch('open_api_mock_build.container_builder.docker.from_env')
    def test_get_docker_client_success(self, mock_docker):
        """Test successful Docker client creation"""
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        
        client = container_builder.get_docker_client()
        
        assert client == mock_client
        mock_client.ping.assert_called_once()

    @patch('open_api_mock_build.container_builder.docker.from_env')
    def test_get_docker_client_failure(self, mock_docker):
        """Test Docker client creation failure"""
        mock_docker.side_effect = docker.errors.DockerException("Docker not available")
        
        with pytest.raises(RuntimeError, match="Docker is not available or not running"):
            container_builder.get_docker_client()

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('open_api_mock_build.container_builder.get_logger')
    def test_check_docker_available_success(self, mock_get_logger, mock_get_client):
        """Test Docker availability check success"""
        # Setup logger mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_client = MagicMock()
        mock_client.version.return_value = {'Version': '24.0.7'}
        mock_get_client.return_value = mock_client

        # Test without verbose
        result = container_builder.check_docker_available()
        assert result is True

        # Test with verbose
        result = container_builder.check_docker_available(verbose=True)
        assert result is True
        mock_logger.info.assert_called_with("Docker version: 24.0.7")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_check_docker_available_failure(self, mock_get_client):
        """Test Docker availability check failure"""
        mock_get_client.side_effect = RuntimeError("Docker not available")
        
        result = container_builder.check_docker_available()
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_success(self, mock_exists, mock_get_client):
        """Test successful image build"""
        # Setup mocks
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock build logs
        build_logs = [
            {'stream': 'Step 1/5 : FROM node:18-alpine\n'},
            {'stream': 'Successfully built abc123\n'},
        ]
        mock_client.api.build.return_value = build_logs
        
        # Mock image for additional tagging
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        # Test build
        result = container_builder.build_image(
            image_name="test:latest",
            spec_file="api.yaml",
            port=3000,
            verbose=True
        )
        
        assert result is True
        mock_client.api.build.assert_called_once()
        
        # Check build arguments
        call_args = mock_client.api.build.call_args
        assert call_args[1]['buildargs']['SPEC_FILE'] == 'api.yaml'
        assert call_args[1]['buildargs']['PORT'] == '3000'

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_custom_port(self, mock_exists, mock_get_client):
        """Test image build with custom port"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        build_logs = [{'stream': 'Successfully built abc123\n'}]
        mock_client.api.build.return_value = build_logs
        
        result = container_builder.build_image(
            image_name="test:latest",
            spec_file="api.yaml",
            port=8080
        )
        
        assert result is True
        call_args = mock_client.api.build.call_args
        assert call_args[1]['buildargs']['PORT'] == '8080'

    @patch('pathlib.Path.exists')
    def test_build_image_dockerfile_not_found(self, mock_exists):
        """Test build failure when Dockerfile not found"""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="Dockerfile not found"):
            container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml"
            )

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_build_error(self, mock_exists, mock_get_client):
        """Test build failure with build error"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock build error
        build_logs = [
            {'stream': 'Step 1/5 : FROM node:18-alpine\n'},
            {'error': 'Build failed: some error'},
        ]
        mock_client.api.build.return_value = build_logs
        
        with patch('builtins.print'):
            result = container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml",
                verbose=True
            )
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_with_additional_tags(self, mock_exists, mock_get_client):
        """Test build with additional tags"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        build_logs = [{'stream': 'Successfully built abc123\n'}]
        mock_client.api.build.return_value = build_logs
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        result = container_builder.build_image(
            image_name="test:latest",
            spec_file="api.yaml",
            tags=["test:v1.0", "test:stable"]
        )
        
        assert result is True
        # Check that additional tags were applied
        assert mock_image.tag.call_count == 2
        mock_image.tag.assert_any_call("test:v1.0")
        mock_image.tag.assert_any_call("test:stable")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_get_image_info_success(self, mock_get_client):
        """Test getting image info successfully"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_image.id = 'sha256:abc123'
        mock_image.short_id = 'abc123'
        mock_image.tags = ['test:latest']
        mock_image.labels = {}
        mock_image.attrs = {
            'Created': '2023-01-01T00:00:00Z',
            'Size': 123456789,
            'Architecture': 'amd64',
            'Os': 'linux'
        }
        mock_client.images.get.return_value = mock_image
        
        result = container_builder.get_image_info('test:latest')
        
        assert result is not None
        assert result['id'] == 'sha256:abc123'
        assert result['short_id'] == 'abc123'
        assert result['tags'] == ['test:latest']
        assert result['attrs']['size'] == 123456789

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_get_image_info_not_found(self, mock_get_client):
        """Test getting info for non-existent image"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        
        result = container_builder.get_image_info('non_existent:latest')
        assert result is None

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_check_image_exists_success(self, mock_get_client):
        """Test checking if image exists - success"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        
        result = container_builder.check_image_exists('test:latest')
        assert result is True

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_check_image_exists_not_found(self, mock_get_client):
        """Test checking if image exists - not found"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        
        result = container_builder.check_image_exists('non_existent:latest')
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('open_api_mock_build.container_builder.get_logger')
    def test_remove_image_success(self, mock_get_logger, mock_get_client):
        """Test successful image removal"""
        # Setup logger mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        result = container_builder.remove_image('test:latest', verbose=True)
        
        assert result is True
        mock_client.images.remove.assert_called_once_with('test:latest', force=False)
        mock_logger.info.assert_any_call("Removing image: test:latest")
        mock_logger.info.assert_any_call("✓ Successfully removed image: test:latest")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_list_images_success(self, mock_get_client):
        """Test listing images successfully"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image1 = MagicMock()
        mock_image1.id = 'sha256:abc123'
        mock_image1.short_id = 'abc123'
        mock_image1.tags = ['test:latest']
        mock_image1.attrs = {'Created': '2023-01-01T00:00:00Z', 'Size': 123456}
        
        mock_image2 = MagicMock()
        mock_image2.id = 'sha256:def456'
        mock_image2.short_id = 'def456'
        mock_image2.tags = ['app:v1.0']
        mock_image2.attrs = {'Created': '2023-01-02T00:00:00Z', 'Size': 654321}
        
        mock_client.images.list.return_value = [mock_image1, mock_image2]
        
        result = container_builder.list_images()
        
        assert len(result) == 2
        assert result[0]['id'] == 'sha256:abc123'
        assert result[1]['tags'] == ['app:v1.0']

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_list_images_with_repository(self, mock_get_client):
        """Test listing images with repository filter"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_image.id = 'sha256:abc123'
        mock_image.short_id = 'abc123'
        mock_image.tags = ['test:latest']
        mock_image.attrs = {'Created': '2023-01-01T00:00:00Z', 'Size': 123456}
        
        mock_client.images.list.return_value = [mock_image]
        
        result = container_builder.list_images(repository="test")
        
        assert len(result) == 1
        mock_client.images.list.assert_called_once_with(name="test")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_list_images_exception(self, mock_get_client):
        """Test list images with exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.list.side_effect = Exception("List error")
        
        result = container_builder.list_images()
        assert result == []

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('open_api_mock_build.container_builder.get_logger')
    def test_remove_image_not_found_verbose(self, mock_get_logger, mock_get_client):
        """Test removing non-existent image with verbose output"""
        # Setup logger mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.remove.side_effect = docker.errors.ImageNotFound("Image not found")
        
        result = container_builder.remove_image('non_existent:latest', verbose=True)
        
        assert result is False
        mock_logger.info.assert_any_call("Removing image: non_existent:latest")
        mock_logger.warning.assert_any_call("Image not found: non_existent:latest")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_remove_image_api_error(self, mock_get_client):
        """Test removing image with API error"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.remove.side_effect = docker.errors.APIError("API error")
        
        with patch('builtins.print'):
            result = container_builder.remove_image('test:latest')
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_remove_image_generic_exception(self, mock_get_client):
        """Test removing image with generic exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.remove.side_effect = Exception("Generic error")
        
        with patch('builtins.print'):
            result = container_builder.remove_image('test:latest')
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('open_api_mock_build.container_builder.get_logger')
    def test_prune_images_success(self, mock_get_logger, mock_get_client):
        """Test successful image pruning"""
        # Setup logger mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.prune.return_value = {
            'ImagesDeleted': [{'Deleted': 'sha256:abc123'}, {'Deleted': 'sha256:def456'}],
            'SpaceReclaimed': 1234567890
        }
        
        result = container_builder.prune_images(verbose=True)
        
        assert 'ImagesDeleted' in result
        assert result['SpaceReclaimed'] == 1234567890
        mock_logger.info.assert_any_call("Pruning unused Docker images...")
        mock_logger.info.assert_any_call("✓ Deleted 2 images, reclaimed 1234567890 bytes")

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_prune_images_exception(self, mock_get_client):
        """Test image pruning with exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.prune.side_effect = Exception("Prune error")
        
        with patch('builtins.print'):
            result = container_builder.prune_images()
        
        assert result == {}

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_get_image_info_exception(self, mock_get_client):
        """Test getting image info with generic exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = Exception("Generic error")
        
        result = container_builder.get_image_info('test:latest')
        assert result is None

    @patch('open_api_mock_build.container_builder.get_docker_client')
    def test_check_image_exists_generic_exception(self, mock_get_client):
        """Test checking image exists with generic exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = Exception("Generic error")
        
        result = container_builder.check_image_exists('test:latest')
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_build_error_exception(self, mock_exists, mock_get_client):
        """Test build image with BuildError exception"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.api.build.side_effect = docker.errors.BuildError("Build error", "")
        
        with patch('builtins.print'):
            result = container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml"
            )
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_api_error_exception(self, mock_exists, mock_get_client):
        """Test build image with APIError exception"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.api.build.side_effect = docker.errors.APIError("API error")
        
        with patch('builtins.print'):
            result = container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml"
            )
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_generic_exception(self, mock_exists, mock_get_client):
        """Test build image with generic exception"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.api.build.side_effect = Exception("Generic error")
        
        with patch('builtins.print'):
            result = container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml"
            )
        
        assert result is False

    @patch('open_api_mock_build.container_builder.get_docker_client')
    @patch('pathlib.Path.exists')
    def test_build_image_tags_image_not_found(self, mock_exists, mock_get_client):
        """Test build image when tagging fails due to image not found"""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        build_logs = [{'stream': 'Successfully built abc123\n'}]
        mock_client.api.build.return_value = build_logs
        
        # Mock image.get to raise ImageNotFound when tagging
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        
        with patch('builtins.print'):
            result = container_builder.build_image(
                image_name="test:latest",
                spec_file="api.yaml",
                tags=["test:v1.0"]
            )
        
        assert result is False
