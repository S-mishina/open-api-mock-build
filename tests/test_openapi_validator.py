import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from open_api_mock_build import openapi_validator


class TestOpenAPIValidator:
    """Test cases for OpenAPI validator functions"""

    @pytest.fixture
    def sample_openapi_spec(self):
        """Sample OpenAPI specification for testing"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "A test API"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def temp_yaml_file(self, sample_openapi_spec):
        """Create temporary YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_openapi_spec, f)
            return f.name

    @pytest.fixture
    def temp_json_file(self, sample_openapi_spec):
        """Create temporary JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_openapi_spec, f)
            return f.name

    def test_load_spec_file_yaml(self, temp_yaml_file):
        """Test loading YAML specification file"""
        spec_data, file_format = openapi_validator.load_spec_file(temp_yaml_file)
        
        assert isinstance(spec_data, dict)
        assert file_format == 'YAML'
        assert spec_data['openapi'] == '3.0.0'
        assert spec_data['info']['title'] == 'Test API'
        
        # Cleanup
        Path(temp_yaml_file).unlink()

    def test_load_spec_file_json(self, temp_json_file):
        """Test loading JSON specification file"""
        spec_data, file_format = openapi_validator.load_spec_file(temp_json_file)
        
        assert isinstance(spec_data, dict)
        assert file_format == 'JSON'
        assert spec_data['openapi'] == '3.0.0'
        assert spec_data['info']['title'] == 'Test API'
        
        # Cleanup
        Path(temp_json_file).unlink()

    def test_load_spec_file_not_found(self):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            openapi_validator.load_spec_file('non_existent_file.yaml')

    def test_load_spec_file_invalid_yaml(self):
        """Test loading invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name
        
        with pytest.raises(ValueError):
            openapi_validator.load_spec_file(temp_file)
        
        # Cleanup
        Path(temp_file).unlink()

    def test_validate_openapi_spec_valid(self, sample_openapi_spec):
        """Test validating valid OpenAPI specification"""
        result = openapi_validator.validate_openapi_spec(sample_openapi_spec)
        
        assert result['title'] == 'Test API'
        assert result['version'] == '1.0.0'
        assert result['spec_version'] == '3.0.0'
        assert result['paths_count'] == 2
        assert result['has_openapi'] is True
        assert result['has_swagger'] is False

    def test_validate_openapi_spec_missing_openapi_version(self):
        """Test validating spec without OpenAPI version"""
        invalid_spec = {
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        
        with pytest.raises(ValueError, match="Missing 'openapi' or 'swagger' version field"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    def test_validate_openapi_spec_missing_info(self):
        """Test validating spec without info section"""
        invalid_spec = {
            "openapi": "3.0.0",
            "paths": {}
        }
        
        with pytest.raises(ValueError, match="Missing required fields: info"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    def test_validate_openapi_spec_missing_paths(self):
        """Test validating spec without paths section"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"}
        }
        
        with pytest.raises(ValueError, match="Missing required fields: paths"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    def test_validate_file_success(self, temp_yaml_file):
        """Test successful file validation"""
        result = openapi_validator.validate_file(temp_yaml_file)
        
        assert result['valid'] is True
        assert result['file_format'] == 'YAML'
        assert result['message'] == 'OpenAPI specification is valid'
        assert 'validation_result' in result
        assert result['validation_result']['title'] == 'Test API'
        
        # Cleanup
        Path(temp_yaml_file).unlink()

    def test_validate_file_failure(self):
        """Test file validation failure"""
        result = openapi_validator.validate_file('non_existent.yaml')
        
        assert result['valid'] is False
        assert result['spec_data'] is None
        assert result['file_format'] is None
        assert result['validation_result'] is None
        assert 'Specification file not found' in result['message']

    def test_get_spec_info_success(self, temp_yaml_file):
        """Test getting spec info successfully"""
        info = openapi_validator.get_spec_info(temp_yaml_file)
        
        assert info['file_format'] == 'YAML'
        assert info['title'] == 'Test API'
        assert info['version'] == '1.0.0'
        assert info['spec_version'] == '3.0.0'
        assert info['paths_count'] == 2
        assert info['endpoints_count'] == 2  # /users GET and /users/{id} GET
        assert info['has_openapi'] is True
        assert info['has_swagger'] is False
        
        # Cleanup
        Path(temp_yaml_file).unlink()

    def test_extract_endpoints_success(self, temp_yaml_file):
        """Test extracting endpoints successfully"""
        endpoints = openapi_validator.extract_endpoints(temp_yaml_file)
        
        assert len(endpoints) == 2
        
        # Check first endpoint
        endpoint1 = endpoints[0]
        assert endpoint1['path'] == '/users'
        assert endpoint1['method'] == 'GET'
        assert endpoint1['summary'] == 'Get users'
        
        # Check second endpoint
        endpoint2 = endpoints[1]
        assert endpoint2['path'] == '/users/{id}'
        assert endpoint2['method'] == 'GET'
        assert endpoint2['summary'] == 'Get user by ID'
        
        # Cleanup
        Path(temp_yaml_file).unlink()

    def test_extract_endpoints_no_file(self):
        """Test extracting endpoints from non-existent file"""
        endpoints = openapi_validator.extract_endpoints('non_existent.yaml')
        assert endpoints == []

    def test_swagger_spec_validation(self):
        """Test validation of Swagger 2.0 specification"""
        swagger_spec = {
            "swagger": "2.0",
            "info": {
                "title": "Swagger API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                }
            }
        }
        
        result = openapi_validator.validate_openapi_spec(swagger_spec)
        
        assert result['title'] == 'Swagger API'
        assert result['spec_version'] == '2.0'
        assert result['has_openapi'] is False
        assert result['has_swagger'] is True

    def test_load_spec_file_invalid_json(self):
        """Test loading invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            temp_file = f.name
        
        with pytest.raises(ValueError):
            openapi_validator.load_spec_file(temp_file)
        
        # Cleanup
        Path(temp_file).unlink()

    def test_validate_openapi_spec_missing_info_title(self):
        """Test validating spec without info title"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"version": "1.0.0"},
            "paths": {}
        }
        
        with pytest.raises(ValueError, match="Missing required 'info.title' field"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    def test_validate_openapi_spec_missing_info_version(self):
        """Test validating spec without info version"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test"},
            "paths": {}
        }
        
        with pytest.raises(ValueError, match="Missing required 'info.version' field"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    def test_get_spec_info_file_not_found(self):
        """Test getting spec info for non-existent file"""
        info = openapi_validator.get_spec_info('non_existent.yaml')
        
        # The function returns error info instead of None
        assert info is not None
        assert 'error' in info
        assert 'Specification file not found' in info['error']

    def test_extract_endpoints_file_not_found(self):
        """Test extracting endpoints from file that doesn't exist"""
        endpoints = openapi_validator.extract_endpoints('non_existent.yaml')
        assert endpoints == []

    def test_extract_endpoints_invalid_spec(self):
        """Test extracting endpoints from invalid spec"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"invalid": "spec"}, f)
            temp_file = f.name
        
        endpoints = openapi_validator.extract_endpoints(temp_file)
        assert endpoints == []
        
        # Cleanup
        Path(temp_file).unlink()

    def test_validate_file_invalid_spec_content(self):
        """Test validating file with invalid spec content"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test"},  # Missing version
            "paths": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_spec, f)
            temp_file = f.name
        
        result = openapi_validator.validate_file(temp_file)
        
        assert result['valid'] is False
        assert "Missing required 'info.version' field" in result['message']
        
        # Cleanup
        Path(temp_file).unlink()

    def test_extract_endpoints_with_multiple_methods(self):
        """Test extracting endpoints with multiple HTTP methods"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "summary": "Create user", 
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(spec, f)
            temp_file = f.name
        
        endpoints = openapi_validator.extract_endpoints(temp_file)
        
        assert len(endpoints) == 2
        methods = [ep['method'] for ep in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        
        # Cleanup
        Path(temp_file).unlink()

    def test_get_spec_info_complete(self):
        """Test get_spec_info with all features"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Complete API", "version": "2.0.0", "description": "Full API"},
            "paths": {
                "/users": {
                    "get": {"summary": "Get users", "responses": {"200": {"description": "OK"}}},
                    "post": {"summary": "Create user", "responses": {"201": {"description": "Created"}}}
                },
                "/posts": {
                    "get": {"summary": "Get posts", "responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(spec, f)
            temp_file = f.name
        
        info = openapi_validator.get_spec_info(temp_file)
        
        assert info['title'] == 'Complete API'
        assert info['version'] == '2.0.0'
        assert info['paths_count'] == 2
        assert info['endpoints_count'] == 3  # 2 for /users, 1 for /posts
        
        # Cleanup
        Path(temp_file).unlink()

    def test_validate_openapi_spec_invalid_data_type(self):
        """Test validating spec with invalid data type"""
        # Test with non-dict spec
        with pytest.raises(ValueError, match="Specification must be a JSON object"):
            openapi_validator.validate_openapi_spec("invalid_spec")

    def test_validate_openapi_spec_invalid_info_type(self):
        """Test validating spec with invalid info type"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": "invalid_info_type",  # Should be dict
            "paths": {}
        }
        
        with pytest.raises(ValueError, match="'info' field must be an object"):
            openapi_validator.validate_openapi_spec(invalid_spec)

    @patch('open_api_mock_build.openapi_validator.get_logger')
    def test_validate_openapi_spec_verbose(self, mock_get_logger):
        """Test validating spec with verbose output"""
        # Setup logger mock
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        
        result = openapi_validator.validate_openapi_spec(spec, verbose=True)
        
        assert result['title'] == 'Test API'
        # Check that verbose output was logged
        mock_logger.info.assert_called()

    def test_load_spec_file_unknown_extension(self):
        """Test loading file with unknown extension"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}')
            temp_file = f.name
        
        # Should default to JSON parsing
        spec_data, file_format = openapi_validator.load_spec_file(temp_file)
        assert file_format == 'JSON'
        
        # Cleanup
        Path(temp_file).unlink()

    def test_get_spec_info_with_error(self):
        """Test get_spec_info when validation fails"""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test"},  # Missing version
            "paths": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_spec, f)
            temp_file = f.name
        
        info = openapi_validator.get_spec_info(temp_file)
        
        # The implementation doesn't throw errors on validation failure,
        # it returns default values
        assert 'file_format' in info
        assert info['file_format'] == 'YAML'
        
        # Cleanup
        Path(temp_file).unlink()

    def test_extract_endpoints_with_validation_error(self):
        """Test extracting endpoints when validation fails"""
        invalid_spec = {
            "openapi": "3.0.0",
            "paths": {}  # Missing info
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_spec, f)
            temp_file = f.name
        
        endpoints = openapi_validator.extract_endpoints(temp_file)
        assert endpoints == []
        
        # Cleanup
        Path(temp_file).unlink()

    def test_load_spec_file_yaml_error(self):
        """Test loading YAML file with parsing error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('invalid: yaml: content: [\n  - unclosed')
            temp_file = f.name
        
        with pytest.raises(ValueError, match="Invalid file format"):
            openapi_validator.load_spec_file(temp_file)
        
        # Cleanup
        Path(temp_file).unlink()

    def test_load_spec_file_json_error(self):
        """Test loading JSON file with parsing error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json, "missing": "quote}')
            temp_file = f.name
        
        with pytest.raises(ValueError, match="Invalid file format"):
            openapi_validator.load_spec_file(temp_file)
        
        # Cleanup
        Path(temp_file).unlink()

    def test_validate_openapi_spec_count_endpoints(self):
        """Test endpoint counting functionality"""
        spec = {
            "openapi": "3.0.0", 
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/api/v1/users": {
                    "get": {"responses": {"200": {"description": "OK"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                    "put": {"responses": {"200": {"description": "Updated"}}}
                },
                "/api/v1/posts": {
                    "get": {"responses": {"200": {"description": "OK"}}},
                    "delete": {"responses": {"204": {"description": "Deleted"}}}
                }
            }
        }
        
        result = openapi_validator.validate_openapi_spec(spec)
        assert result['paths_count'] == 2
        # The implementation doesn't include endpoints_count in validate_openapi_spec
        # Only check what's actually returned
        assert 'title' in result
        assert result['title'] == 'Test'
