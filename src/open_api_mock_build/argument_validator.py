"""
Command line argument validation module
"""
import argparse
from typing import Tuple
from .logger import get_logger


def validate_registry_format(registry: str) -> Tuple[bool, str]:
    """
    Validate registry URL format and check for common mistakes
    
    Args:
        registry: Registry URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not registry:
        return True, ""
    
    # Split by '/' to check if there are path components after the hostname
    registry_parts = registry.split('/')
    if len(registry_parts) > 1:
        # Check if this looks like a registry hostname
        hostname = registry_parts[0]
        if '.' in hostname and any(service in hostname for service in ['ecr', 'gcr.io', 'azurecr.io', 'pkg.dev']):
            # This looks like a registry URL with image name - common mistake
            suggested_registry = hostname
            suggested_image = '/'.join(registry_parts[1:])
            if ':' not in suggested_image:
                suggested_image += ':latest'
            
            error_msg = f"""
❌ Registry URL should not include image name.

Registry (-r) should only specify the hostname, not the full image path.

Current registry: {registry}
Suggested fix:
  -r {suggested_registry}
  -i {suggested_image}

Example:
  ✗ -r 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app
  ✓ -r 123456789.dkr.ecr.us-east-1.amazonaws.com -i my-app:latest
"""
            return False, error_msg
    
    return True, ""


def validate_image_format(image: str) -> Tuple[bool, str]:
    """
    Validate image name format
    
    Args:
        image: Image name string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not image:
        return False, "Image name cannot be empty"
    
    # Basic validation - more can be added as needed
    if image.startswith('/') or image.endswith('/'):
        return False, "Image name cannot start or end with '/'"
    
    return True, ""


def validate_arguments(args: argparse.Namespace) -> Tuple[bool, str]:
    """
    Validate all command line arguments
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    logger = get_logger("argument_validator")
    
    # Validate registry format
    registry_valid, registry_error = validate_registry_format(args.registry)
    if not registry_valid:
        return False, registry_error
    
    # Validate image format
    image_valid, image_error = validate_image_format(args.image)
    if not image_valid:
        return False, image_error
    
    # Add more validations as needed
    
    if args.verbose:
        logger.info("✓ Command line arguments validation passed")
    
    return True, ""
