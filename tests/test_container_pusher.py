import pytest
from unittest.mock import patch, MagicMock
import docker.errors
from open_api_mock_build import container_pusher


class TestContainerPusher:
    """Test cases for container pusher functions"""

    @patch('open_api_mock_build.container_pusher.docker.from_env')
    def test_get_docker_client_success(self, mock_docker):
        """Test successful Docker client creation"""
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        
        client = container_pusher.get_docker_client()
        
        assert client == mock_client
        mock_client.ping.assert_called_once()

    @patch('open_api_mock_build.container_pusher.docker.from_env')
    def test_get_docker_client_failure(self, mock_docker):
        """Test Docker client creation failure"""
        mock_docker.side_effect = docker.errors.DockerException("Docker not available")
        
        with pytest.raises(RuntimeError, match="Docker is not available or not running"):
            container_pusher.get_docker_client()

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_docker_available_success(self, mock_get_client):
        """Test Docker availability check success"""
        mock_client = MagicMock()
        mock_client.version.return_value = {'Version': '24.0.7'}
        mock_get_client.return_value = mock_client
        
        result = container_pusher.check_docker_available(verbose=True)
        assert result is True

    def test_parse_registry_url_docker_hub(self):
        """Test parsing Docker Hub registry"""
        result = container_pusher.parse_registry_url("")
        assert result['type'] == 'docker_hub'
        assert result['hostname'] == 'docker.io'

    def test_parse_registry_url_aws_ecr(self):
        """Test parsing AWS ECR registry"""
        registry = "123456789.dkr.ecr.us-west-2.amazonaws.com"
        result = container_pusher.parse_registry_url(registry)
        
        assert result['type'] == 'aws_ecr'
        assert result['account_id'] == '123456789'
        assert result['region'] == 'us-west-2'

    def test_parse_registry_url_gcr(self):
        """Test parsing Google Container Registry"""
        registry = "gcr.io"
        result = container_pusher.parse_registry_url(registry)
        assert result['type'] == 'gcr'

    def test_parse_registry_url_gar(self):
        """Test parsing Google Artifact Registry"""
        registry = "us-central1-docker.pkg.dev"
        result = container_pusher.parse_registry_url(registry)
        assert result['type'] == 'gar'

    def test_parse_registry_url_acr(self):
        """Test parsing Azure Container Registry"""
        registry = "myregistry.azurecr.io"
        result = container_pusher.parse_registry_url(registry)
        assert result['type'] == 'acr'

    def test_parse_registry_url_generic(self):
        """Test parsing generic registry"""
        registry = "custom-registry.com"
        result = container_pusher.parse_registry_url(registry)
        assert result['type'] == 'generic'

    def test_build_full_image_name_no_registry(self):
        """Test building image name without registry"""
        result = container_pusher.build_full_image_name("test:latest")
        assert result == "test:latest"

    def test_build_full_image_name_with_registry(self):
        """Test building image name with registry"""
        result = container_pusher.build_full_image_name("test:latest", "myregistry.com")
        assert result == "myregistry.com/test:latest"

    def test_build_full_image_name_docker_hub(self):
        """Test building image name for Docker Hub"""
        result = container_pusher.build_full_image_name("test:latest", "docker.io")
        assert result == "docker.io/test:latest"  # Actually returns with docker.io prefix

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_login_to_registry_no_registry(self, mock_get_client):
        """Test login without registry specified"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        result = container_pusher.login_to_registry()
        assert result is True

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_login_to_registry_with_credentials(self, mock_get_client):
        """Test login with username and password"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.login.return_value = {"Status": "Login Succeeded"}
        
        result = container_pusher.login_to_registry(
            registry="docker.io",
            username="testuser",
            password="testpass",
            verbose=True
        )
        
        assert result is True
        mock_client.login.assert_called_once_with(
            username="testuser",
            password="testpass",
            registry="docker.io"
        )

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_success(self, mock_get_client):
        """Test successful image push"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock image exists
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        # Mock push logs
        push_logs = [
            {'status': 'Pushing repository'},
            {'status': 'Image successfully pushed'},
        ]
        mock_client.api.push.return_value = push_logs
        
        result = container_pusher.push_image(
            image_name="test:latest",
            verbose=True
        )
        
        assert result is True

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_not_found(self, mock_get_client):
        """Test push when image not found"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        
        with patch('builtins.print'):
            result = container_pusher.push_image("non_existent:latest")
        
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_with_registry_and_tags(self, mock_get_client):
        """Test push with registry and additional tags"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        push_logs = [{'status': 'Pushed'}]
        mock_client.api.push.return_value = push_logs
        
        result = container_pusher.push_image(
            image_name="test:latest",
            registry="myregistry.com",
            tags=["v1.0", "stable"],
            verbose=True
        )
        
        assert result is True
        # Check that image was tagged with registry
        mock_image.tag.assert_called()

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_image_exists_success(self, mock_get_client):
        """Test checking if image exists - success"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        
        result = container_pusher.check_image_exists("test:latest")
        assert result is True

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_image_exists_not_found(self, mock_get_client):
        """Test checking if image exists - not found"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        
        result = container_pusher.check_image_exists("non_existent:latest")
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_docker_available_failure(self, mock_get_client):
        """Test Docker availability check failure"""
        mock_get_client.side_effect = RuntimeError("Docker not available")
        
        result = container_pusher.check_docker_available()
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_login_to_registry_failure(self, mock_get_client):
        """Test registry login failure"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.login.side_effect = docker.errors.APIError("Login failed")
        
        with patch('builtins.print'):
            result = container_pusher.login_to_registry(
                registry="docker.io",
                username="testuser", 
                password="wrongpass"
            )
        
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client') 
    def test_push_image_api_error(self, mock_get_client):
        """Test push image with API error"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        mock_client.api.push.side_effect = docker.errors.APIError("Push failed")
        
        with patch('builtins.print'):
            result = container_pusher.push_image("test:latest")
        
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_generic_error(self, mock_get_client):
        """Test push image with generic error"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()  
        mock_client.images.get.return_value = mock_image
        mock_client.api.push.side_effect = Exception("Generic error")
        
        with patch('builtins.print'):
            result = container_pusher.push_image("test:latest")
        
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_with_error_in_logs(self, mock_get_client):
        """Test push image with error in push logs"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        push_logs = [
            {'status': 'Pushing'},
            {'error': 'Push failed', 'errorDetail': {'message': 'Detailed error'}}
        ]
        mock_client.api.push.return_value = push_logs
        
        with patch('builtins.print'):
            result = container_pusher.push_image("test:latest", verbose=True)
        
        # The implementation correctly detects errors in logs and returns False
        assert result is False

    def test_parse_registry_url_edge_cases(self):
        """Test parsing registry URL edge cases"""
        # Empty string
        result = container_pusher.parse_registry_url("")
        assert result['type'] == 'docker_hub'
        
        # None
        result = container_pusher.parse_registry_url(None)
        assert result['type'] == 'docker_hub'
        
        # With port
        result = container_pusher.parse_registry_url("registry.example.com:5000")
        assert result['type'] == 'generic'
        assert result['hostname'] == 'registry.example.com:5000'

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_without_verbose(self, mock_get_client):
        """Test push image without verbose output"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        push_logs = [{'status': 'Successfully pushed'}]
        mock_client.api.push.return_value = push_logs
        
        result = container_pusher.push_image("test:latest", verbose=False)
        
        assert result is True

    @patch('open_api_mock_build.container_pusher.get_docker_client') 
    def test_login_to_registry_generic_exception(self, mock_get_client):
        """Test registry login with generic exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.login.side_effect = Exception("Generic login error")
        
        with patch('builtins.print'):
            result = container_pusher.login_to_registry(
                registry="docker.io",
                username="testuser",
                password="testpass"
            )
        
        assert result is False

    def test_build_full_image_name_edge_cases(self):
        """Test build full image name with edge cases"""
        # Image name already contains registry - implementation returns as-is
        result = container_pusher.build_full_image_name(
            "registry.com/myapp:latest", 
            "otherregistry.com"
        )
        assert result == "registry.com/myapp:latest"  # Returns original when registry detected
        
        # No tag in image name
        result = container_pusher.build_full_image_name("myapp", "registry.com") 
        assert result == "registry.com/myapp"

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_image_exists_generic_exception(self, mock_get_client):
        """Test check image exists with generic exception"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.side_effect = Exception("Generic error")
        
        result = container_pusher.check_image_exists("test:latest")
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    @patch('open_api_mock_build.container_pusher.subprocess.run')
    def test_login_to_registry_aws_ecr_success(self, mock_subprocess, mock_get_client):
        """Test successful AWS ECR login"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock AWS CLI response
        mock_result = MagicMock()
        mock_result.stdout = "AWS_TOKEN_12345"
        mock_subprocess.return_value = mock_result
        
        # Mock Docker login
        mock_client.login.return_value = {"Status": "Login Succeeded"}
        
        result = container_pusher.login_to_registry(
            registry="123456789.dkr.ecr.us-west-2.amazonaws.com",
            verbose=True
        )
        
        assert result is True
        # Check that AWS CLI was called
        mock_subprocess.assert_called_once()
        # Check that docker login was called with AWS credentials
        mock_client.login.assert_called_once_with(
            username="AWS",
            password="AWS_TOKEN_12345",
            registry="123456789.dkr.ecr.us-west-2.amazonaws.com"
        )

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    @patch('open_api_mock_build.container_pusher.subprocess.run')
    def test_login_to_registry_aws_ecr_failure(self, mock_subprocess, mock_get_client):
        """Test AWS ECR login failure"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock AWS CLI failure
        mock_subprocess.side_effect = Exception("AWS CLI error")
        
        with patch('builtins.print'):
            result = container_pusher.login_to_registry(
                registry="123456789.dkr.ecr.us-west-2.amazonaws.com"
            )
        
        assert result is False

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_login_to_registry_no_credentials(self, mock_get_client):
        """Test registry login without credentials"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        with patch('builtins.print'):
            result = container_pusher.login_to_registry(
                registry="private-registry.com",
                verbose=True
            )
        
        # Should return True (assume already logged in)
        assert result is True

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_with_error_logs_detailed(self, mock_get_client):
        """Test push image with detailed error logs"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        push_logs = [
            {'status': 'Pushing'},
            {'error': 'Push failed', 'errorDetail': {'message': 'Authentication required'}},
            {'status': 'Push complete'}
        ]
        mock_client.api.push.return_value = push_logs
        
        with patch('builtins.print'):
            result = container_pusher.push_image("test:latest", verbose=True)
        
        # The implementation correctly detects errors in logs and returns False
        assert result is False

    def test_parse_registry_url_with_none(self):
        """Test parse_registry_url with None input"""
        result = container_pusher.parse_registry_url(None)
        assert result['type'] == 'docker_hub'
        assert result['hostname'] == 'docker.io'
        
    def test_parse_registry_url_empty_string(self):
        """Test parse_registry_url with empty string"""
        result = container_pusher.parse_registry_url("")
        assert result['type'] == 'docker_hub'
        assert result['hostname'] == 'docker.io'

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_push_image_with_logs_containing_id(self, mock_get_client):
        """Test push image with logs containing ID field"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image
        
        push_logs = [
            {'status': 'Pushing', 'id': 'layer1'},
            {'status': 'Pushed', 'id': 'layer1'},
            {'status': 'Push complete'}
        ]
        mock_client.api.push.return_value = push_logs
        
        with patch('open_api_mock_build.container_pusher.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = container_pusher.push_image("test:latest", verbose=True)
        
        assert result is True
        # Check that ID was included in debug output
        mock_logger.debug.assert_any_call("layer1: Pushing")

    def test_build_full_image_name_with_port_registry(self):
        """Test building image name with registry that has port"""
        result = container_pusher.build_full_image_name(
            "test:latest", 
            "localhost:5000"
        )
        assert result == "localhost:5000/test:latest"

    @patch('open_api_mock_build.container_pusher.get_docker_client')
    def test_check_image_exists_with_registry(self, mock_get_client):
        """Test check image exists with registry"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        
        result = container_pusher.check_image_exists("test:latest", "registry.com")
        assert result is True
        # Should check for registry.com/test:latest
        mock_client.images.get.assert_called_once_with("registry.com/test:latest")
