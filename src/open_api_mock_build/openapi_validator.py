import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List


def load_spec_file(spec_file: str, verbose: bool = False) -> Tuple[Dict[Any, Any], str]:
    """
    Load OpenAPI specification file (JSON or YAML)
    
    Args:
        spec_file: Path to the specification file
        verbose: Enable verbose output
        
    Returns:
        Tuple of (loaded spec dict, file format)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported or invalid
    """
    spec_path = Path(spec_file)
    
    if not spec_path.exists():
        raise FileNotFoundError(f"Specification file not found: {spec_file}")
    
    if verbose:
        print(f"Loading specification file: {spec_file}")
    
    file_extension = spec_path.suffix.lower()
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            if file_extension in ['.yaml', '.yml']:
                spec_data = yaml.safe_load(f)
                file_format = 'YAML'
            elif file_extension == '.json':
                spec_data = json.load(f)
                file_format = 'JSON'
            else:
                # Try to detect format by content
                content = f.read()
                f.seek(0)
                
                # Try JSON first
                try:
                    spec_data = json.load(f)
                    file_format = 'JSON'
                except json.JSONDecodeError:
                    # Try YAML
                    try:
                        spec_data = yaml.safe_load(content)
                        file_format = 'YAML'
                    except yaml.YAMLError:
                        raise ValueError(f"Unable to parse file as JSON or YAML: {spec_file}")
                        
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Invalid file format: {e}")
    
    if spec_data is None:
        raise ValueError(f"Empty or invalid specification file: {spec_file}")
    
    return spec_data, file_format


def validate_openapi_spec(spec_data: Dict[Any, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Validate OpenAPI specification structure
    
    Args:
        spec_data: The loaded specification data
        verbose: Enable verbose output
        
    Returns:
        Dictionary with validation results
    """
    if not isinstance(spec_data, dict):
        raise ValueError("Specification must be a JSON object")
    
    # Check for OpenAPI version
    if 'openapi' not in spec_data and 'swagger' not in spec_data:
        raise ValueError("Missing 'openapi' or 'swagger' version field")
    
    # Check required fields
    required_fields = ['info', 'paths']
    missing_fields = [field for field in required_fields if field not in spec_data]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate info section
    info = spec_data.get('info', {})
    if not isinstance(info, dict):
        raise ValueError("'info' field must be an object")
    
    if 'title' not in info:
        raise ValueError("Missing required 'info.title' field")
    
    if 'version' not in info:
        raise ValueError("Missing required 'info.version' field")
    
    # Validate paths section
    paths = spec_data.get('paths', {})
    if not isinstance(paths, dict):
        raise ValueError("'paths' field must be an object")
    
    # Extract metadata
    version = spec_data.get('openapi') or spec_data.get('swagger')
    
    result = {
        'title': info.get('title'),
        'version': info.get('version'),
        'spec_version': version,
        'paths_count': len(paths),
        'has_openapi': 'openapi' in spec_data,
        'has_swagger': 'swagger' in spec_data
    }
    
    if verbose:
        print(f"✓ OpenAPI specification validation passed")
        print(f"  Title: {result['title']}")
        print(f"  Version: {result['version']}")
        print(f"  Spec Version: {result['spec_version']}")
        print(f"  Paths: {result['paths_count']}")
    
    return result


def validate_file(spec_file: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Load and validate OpenAPI specification file
    
    Args:
        spec_file: Path to the specification file
        verbose: Enable verbose output
        
    Returns:
        Dictionary with validation results
    """
    try:
        spec_data, file_format = load_spec_file(spec_file, verbose)
        validation_result = validate_openapi_spec(spec_data, verbose)
        
        return {
            'valid': True,
            'spec_data': spec_data,
            'file_format': file_format,
            'validation_result': validation_result,
            'message': 'OpenAPI specification is valid'
        }
        
    except Exception as e:
        return {
            'valid': False,
            'spec_data': None,
            'file_format': None,
            'validation_result': None,
            'message': str(e),
            'error': e
        }


def get_spec_info(spec_file: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Get basic information about OpenAPI specification file
    
    Args:
        spec_file: Path to the specification file
        verbose: Enable verbose output
        
    Returns:
        Dictionary with spec information
    """
    try:
        spec_data, file_format = load_spec_file(spec_file, verbose)
        
        # Basic info extraction
        info = spec_data.get('info', {})
        version = spec_data.get('openapi') or spec_data.get('swagger')
        paths = spec_data.get('paths', {})
        
        # Count endpoints
        endpoint_count = 0
        for path, methods in paths.items():
            if isinstance(methods, dict):
                endpoint_count += len([m for m in methods.keys() if m.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']])
        
        return {
            'file_format': file_format,
            'title': info.get('title', 'Unknown'),
            'version': info.get('version', 'Unknown'),
            'description': info.get('description', ''),
            'spec_version': version,
            'paths_count': len(paths),
            'endpoints_count': endpoint_count,
            'has_openapi': 'openapi' in spec_data,
            'has_swagger': 'swagger' in spec_data
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'file_format': None
        }


def extract_endpoints(spec_file: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Extract endpoint information from OpenAPI specification
    
    Args:
        spec_file: Path to the specification file
        verbose: Enable verbose output
        
    Returns:
        List of endpoint information
    """
    try:
        spec_data, _ = load_spec_file(spec_file, verbose)
        paths = spec_data.get('paths', {})
        
        endpoints = []
        for path, methods in paths.items():
            if isinstance(methods, dict):
                for method, details in methods.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                        endpoint = {
                            'path': path,
                            'method': method.upper(),
                            'summary': details.get('summary', ''),
                            'description': details.get('description', ''),
                            'operation_id': details.get('operationId', ''),
                            'tags': details.get('tags', [])
                        }
                        endpoints.append(endpoint)
        
        if verbose:
            print(f"Found {len(endpoints)} endpoints")
        
        return endpoints
        
    except Exception as e:
        if verbose:
            print(f"Error extracting endpoints: {e}")
        return []
