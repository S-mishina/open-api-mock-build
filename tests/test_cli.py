import pytest
import argparse
from unittest.mock import patch
from open_api_mock_build.cli import parse_args, create_parser


class TestCLI:
    """Test cases for CLI argument parsing"""

    def test_create_parser(self):
        """Test parser creation"""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'open-api-mock-build'

    def test_parse_args_required_arguments(self):
        """Test parsing with required arguments"""
        args = parse_args(['test.yaml', '-i', 'test-image:latest'])
        assert args.spec_file == 'test.yaml'
        assert args.image == 'test-image:latest'
        assert args.port == 3000  # default
        assert args.registry is None
        assert args.no_push is False
        assert args.verbose is False

    def test_parse_args_all_options(self):
        """Test parsing with all options"""
        args = parse_args([
            'api.yaml',
            '-i', 'my-app:v1.0',
            '-r', 'docker.io',
            '-p', '8080',
            '--no-push',
            '-v'
        ])
        assert args.spec_file == 'api.yaml'
        assert args.image == 'my-app:v1.0'
        assert args.registry == 'docker.io'
        assert args.port == 8080
        assert args.no_push is True
        assert args.verbose is True

    def test_parse_args_port_default(self):
        """Test port default value"""
        args = parse_args(['test.yaml', '-i', 'test:latest'])
        assert args.port == 3000

    def test_parse_args_custom_port(self):
        """Test custom port parsing"""
        args = parse_args(['test.yaml', '-i', 'test:latest', '-p', '9090'])
        assert args.port == 9090
        
        # Test with long form
        args = parse_args(['test.yaml', '-i', 'test:latest', '--port', '8000'])
        assert args.port == 8000

    def test_parse_args_invalid_port(self):
        """Test invalid port handling"""
        with pytest.raises(SystemExit):
            parse_args(['test.yaml', '-i', 'test:latest', '-p', 'invalid'])

    def test_parse_args_missing_required(self):
        """Test missing required arguments"""
        # Missing spec_file
        with pytest.raises(SystemExit):
            parse_args(['-i', 'test:latest'])
        
        # Missing image
        with pytest.raises(SystemExit):
            parse_args(['test.yaml'])

    def test_parse_args_help(self):
        """Test help option"""
        with pytest.raises(SystemExit):
            parse_args(['--help'])

    def test_parse_args_version(self):
        """Test version option"""
        with pytest.raises(SystemExit):
            parse_args(['--version'])

    @patch('sys.argv', ['open-api-mock-build', 'test.yaml', '-i', 'test:latest'])
    def test_parse_args_no_arguments(self):
        """Test parsing without explicit arguments (from sys.argv)"""
        args = parse_args()
        assert args.spec_file == 'test.yaml'
        assert args.image == 'test:latest'
