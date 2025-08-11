import docker
import re
import subprocess
from typing import Optional, Dict, Any, List
from docker.errors import DockerException, APIError
from .logger import get_logger, log_operation_start, log_operation_success, log_operation_failure


def get_docker_client() -> docker.DockerClient:
    """Get Docker client instance"""
    try:
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except DockerException as e:
        raise RuntimeError(f"Docker is not available or not running: {e}")


def check_docker_available(verbose: bool = False) -> bool:
    """Check if Docker is available and running"""
    logger = get_logger("container_pusher")
    try:
        client = get_docker_client()
        if verbose:
            version_info = client.version()
            logger.info(f"Docker version: {version_info['Version']}")
        return True
    except RuntimeError:
        return False


def parse_registry_url(registry: str) -> Dict[str, str]:
    """Parse registry URL and determine registry type"""
    if not registry:
        return {
            'type': 'docker_hub',
            'url': 'docker.io',
            'hostname': 'docker.io'
        }
    
    # AWS ECR pattern
    ecr_pattern = r'(\d+)\.dkr\.ecr\.([a-zA-Z0-9-]+)\.amazonaws\.com'
    if re.match(ecr_pattern, registry):
        return {
            'type': 'aws_ecr',
            'url': registry,
            'hostname': registry,
            'account_id': registry.split('.')[0],
            'region': registry.split('.')[3]
        }
    
    # Google Container Registry patterns
    if registry.startswith('gcr.io') or registry.startswith('us.gcr.io') or registry.startswith('eu.gcr.io') or registry.startswith('asia.gcr.io'):
        return {
            'type': 'gcr',
            'url': registry,
            'hostname': registry
        }
    
    # Google Artifact Registry pattern
    if '.pkg.dev' in registry:
        return {
            'type': 'gar',
            'url': registry,
            'hostname': registry
        }
    
    # Azure Container Registry pattern
    if registry.endswith('.azurecr.io'):
        return {
            'type': 'acr',
            'url': registry,
            'hostname': registry
        }
    
    # Generic/custom registry
    return {
        'type': 'generic',
        'url': registry,
        'hostname': registry
    }


def build_full_image_name(image_name: str, registry: Optional[str] = None) -> str:
    """Build full image name with registry prefix"""
    if not registry:
        return image_name
    
    # If image_name already contains registry, return as is
    if '/' in image_name and ('.' in image_name.split('/')[0] or ':' in image_name.split('/')[0]):
        return image_name
    
    registry_info = parse_registry_url(registry)
    
    if registry_info['type'] == 'docker_hub':
        # For Docker Hub, we might not need to prefix if it's already a simple name
        return image_name
    else:
        return f"{registry_info['hostname']}/{image_name}"


def login_to_registry(registry: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None, verbose: bool = False) -> bool:
    """Login to container registry"""
    logger = get_logger("container_pusher")
    client = get_docker_client()
    
    if not registry:
        if verbose:
            logger.info("No registry specified, assuming Docker Hub or already logged in")
        return True
    
    registry_info = parse_registry_url(registry)
    
    # For AWS ECR, use aws ecr get-login-password
    if registry_info['type'] == 'aws_ecr':
        if verbose:
            logger.info(f"Attempting AWS ECR login to {registry}")
        try:
            # Get login token from AWS CLI
            aws_cmd = [
                "aws", "ecr", "get-login-password",
                "--region", registry_info['region']
            ]
            
            aws_result = subprocess.run(
                aws_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Use docker client to login
            login_result = client.login(
                username="AWS",
                password=aws_result.stdout.strip(),
                registry=registry
            )
            
            if verbose:
                logger.info(f"✓ Successfully logged in to AWS ECR: {registry}")
            return True
                
        except Exception as e:
            logger.error(f"✗ Error during AWS ECR login: {e}")
            return False
    
    # For other registries, use username/password if provided
    elif username and password:
        try:
            login_result = client.login(
                username=username,
                password=password,
                registry=registry
            )
            
            if verbose:
                logger.info(f"✓ Successfully logged in to {registry}")
            return True
                
        except Exception as e:
            logger.error(f"✗ Error during login: {e}")
            return False
    
    # Assume already logged in
    if verbose:
        logger.info(f"Assuming already logged in to {registry}")
    return True


def push_image(image_name: str, registry: Optional[str] = None, tags: Optional[List[str]] = None, verbose: bool = False) -> bool:
    """
    Push Docker image to registry
    
    Args:
        image_name: Local image name
        registry: Registry URL
        tags: Additional tags to push
        verbose: Enable verbose output
        
    Returns:
        True if push successful, False otherwise
    """
    logger = get_logger("container_pusher")
    client = get_docker_client()
    
    # Build full image name
    full_image_name = build_full_image_name(image_name, registry)
    
    try:
        # Get the image
        try:
            image = client.images.get(image_name)
        except docker.errors.ImageNotFound:
            logger.error(f"✗ Image not found: {image_name}")
            return False
        
        # Tag image if registry is specified
        if registry and full_image_name != image_name:
            if verbose:
                logger.info(f"Tagging image: {image_name} -> {full_image_name}")
            
            # Tag the image
            image.tag(full_image_name)
        
        # Push main image
        if verbose:
            logger.info(f"Pushing image: {full_image_name}")
        
        # Push with streaming output
        push_logs = client.api.push(
            full_image_name, 
            stream=True, 
            decode=True
        )
        
        push_error = None
        for log in push_logs:
            # Check for errors in push logs
            if 'errorDetail' in log or 'error' in log:
                error_msg = log.get('error') or log.get('errorDetail', {}).get('message', 'Unknown error')
                push_error = error_msg
                logger.error(f"✗ Push error: {error_msg}")
                break
                
            if verbose and 'status' in log:
                status = log['status']
                if 'id' in log:
                    logger.debug(f"{log['id']}: {status}")
                else:
                    logger.debug(status)
        
        # Check if push was successful
        if push_error:
            logger.error(f"✗ Failed to push image: {full_image_name}")
            return False
            
        if verbose:
            logger.info(f"✓ Successfully pushed image: {full_image_name}")
        
        # Push additional tags if specified
        if tags:
            for tag in tags:
                tag_full_name = build_full_image_name(f"{image_name}:{tag}", registry)
                if verbose:
                    logger.info(f"Pushing additional tag: {tag_full_name}")
                
                # Tag and push
                image.tag(tag_full_name)
                
                push_logs = client.api.push(
                    tag_full_name, 
                    stream=True, 
                    decode=True
                )
                
                tag_push_error = None
                for log in push_logs:
                    # Check for errors in push logs
                    if 'errorDetail' in log or 'error' in log:
                        error_msg = log.get('error') or log.get('errorDetail', {}).get('message', 'Unknown error')
                        tag_push_error = error_msg
                        logger.error(f"✗ Push error for tag {tag}: {error_msg}")
                        break
                        
                    if verbose and 'status' in log:
                        status = log['status']
                        if 'id' in log:
                            logger.debug(f"{log['id']}: {status}")
                        else:
                            logger.debug(status)
                
                # Check if tag push was successful
                if tag_push_error:
                    logger.error(f"✗ Failed to push tag: {tag_full_name}")
                    return False
        
        return True
        
    except APIError as e:
        logger.error(f"✗ Docker API error during push: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error during push: {e}")
        return False


def check_image_exists(image_name: str, registry: Optional[str] = None) -> bool:
    """Check if image exists locally"""
    client = get_docker_client()
    full_image_name = build_full_image_name(image_name, registry)
    
    try:
        client.images.get(full_image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception:
        return False
