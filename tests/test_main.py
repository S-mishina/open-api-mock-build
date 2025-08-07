import pytest
from unittest.mock import patch, MagicMock
from open_api_mock_build.main import main


class TestMain:
    """Test cases for main function"""

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('open_api_mock_build.main.container_pusher')
    @patch('builtins.print')
    def test_main_success_with_push(
        self, mock_print, mock_pusher, mock_builder, mock_validator, mock_parse_args
    ):
        """Test successful main execution with push"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = 'docker.io'
        mock_args.no_push = False
        mock_args.verbose = True
        mock_parse_args.return_value = mock_args

        # Setup validation
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }

        # Setup builder
        mock_builder.check_docker_available.return_value = True
        mock_builder.build_image.return_value = True

        # Setup pusher
        mock_pusher.check_docker_available.return_value = True
        mock_pusher.login_to_registry.return_value = True
        mock_pusher.push_image.return_value = True

        result = main()

        assert result == 0
        mock_validator.validate_file.assert_called_once_with(
            spec_file='test.yaml', verbose=True
        )
        mock_builder.build_image.assert_called_once_with(
            image_name='test:latest',
            spec_file='test.yaml',
            port=3000,
            dockerfile_path='Dockerfile',
            build_context='.',
            verbose=True
        )
        mock_pusher.push_image.assert_called_once_with(
            image_name='test:latest',
            registry='docker.io',
            verbose=True
        )

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('builtins.print')
    def test_main_success_no_push(
        self, mock_print, mock_builder, mock_validator, mock_parse_args
    ):
        """Test successful main execution without push"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 8080
        mock_args.registry = None
        mock_args.no_push = True
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }

        # Setup builder
        mock_builder.check_docker_available.return_value = True
        mock_builder.build_image.return_value = True

        result = main()

        assert result == 0
        mock_builder.build_image.assert_called_once_with(
            image_name='test:latest',
            spec_file='test.yaml',
            port=8080,
            dockerfile_path='Dockerfile',
            build_context='.',
            verbose=False
        )

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('builtins.print')
    def test_main_validation_failure(self, mock_print, mock_validator, mock_parse_args):
        """Test main execution with validation failure"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'invalid.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = None
        mock_args.no_push = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation failure
        mock_validator.validate_file.return_value = {
            'valid': False,
            'message': 'Invalid OpenAPI specification'
        }

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ OpenAPI validation failed: Invalid OpenAPI specification")

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('builtins.print')
    def test_main_docker_not_available(
        self, mock_print, mock_builder, mock_validator, mock_parse_args
    ):
        """Test main execution when Docker not available"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = None
        mock_args.no_push = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation success
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }

        # Setup Docker not available
        mock_builder.check_docker_available.return_value = False

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ Docker is not available or not running")

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('builtins.print')
    def test_main_build_failure(
        self, mock_print, mock_builder, mock_validator, mock_parse_args
    ):
        """Test main execution with build failure"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = None
        mock_args.no_push = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation success
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }

        # Setup builder
        mock_builder.check_docker_available.return_value = True
        mock_builder.build_image.return_value = False

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ Container build failed")

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('open_api_mock_build.main.container_pusher')
    @patch('builtins.print')
    def test_main_push_failure(
        self, mock_print, mock_pusher, mock_builder, mock_validator, mock_parse_args
    ):
        """Test main execution with push failure"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = 'docker.io'
        mock_args.no_push = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation and build success
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }
        mock_builder.check_docker_available.return_value = True
        mock_builder.build_image.return_value = True

        # Setup push failure
        mock_pusher.check_docker_available.return_value = True
        mock_pusher.login_to_registry.return_value = True
        mock_pusher.push_image.return_value = False

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ Container push failed")

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('builtins.print')
    @patch('traceback.print_exc')
    def test_main_exception_handling(self, mock_traceback, mock_print, mock_validator, mock_parse_args):
        """Test main exception handling"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = None
        mock_args.no_push = False
        mock_args.verbose = True
        mock_parse_args.return_value = mock_args

        # Setup exception
        mock_validator.validate_file.side_effect = Exception("Unexpected error")

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ Error: Unexpected error")
        mock_traceback.assert_called_once()

    @patch('open_api_mock_build.main.parse_args')
    @patch('open_api_mock_build.main.openapi_validator')
    @patch('open_api_mock_build.main.container_builder')
    @patch('open_api_mock_build.main.container_pusher')
    @patch('builtins.print')
    def test_main_registry_login_failure(
        self, mock_print, mock_pusher, mock_builder, mock_validator, mock_parse_args
    ):
        """Test main execution with registry login failure"""
        # Setup args
        mock_args = MagicMock()
        mock_args.spec_file = 'test.yaml'
        mock_args.image = 'test:latest'
        mock_args.port = 3000
        mock_args.registry = 'private-registry.com'
        mock_args.no_push = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Setup validation and build success
        mock_validator.validate_file.return_value = {
            'valid': True,
            'validation_result': {
                'title': 'Test API',
                'version': '1.0.0',
                'spec_version': '3.0.0',
                'paths_count': 2
            }
        }
        mock_builder.check_docker_available.return_value = True
        mock_builder.build_image.return_value = True

        # Setup login failure
        mock_pusher.check_docker_available.return_value = True
        mock_pusher.login_to_registry.return_value = False

        result = main()

        assert result == 1
        mock_print.assert_any_call("✗ Registry login failed")
