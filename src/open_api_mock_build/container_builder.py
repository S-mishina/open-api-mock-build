import docker
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from docker.errors import DockerException, APIError, BuildError


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
    try:
        client = get_docker_client()
        if verbose:
            version_info = client.version()
            print(f"Docker version: {version_info['Version']}")
        return True
    except RuntimeError:
        return False


def build_image(
    image_name: str, 
    spec_file: str,
    port: int = 3000,
    dockerfile_path: str = "Dockerfile",
    build_context: str = ".",
    build_args: Optional[dict] = None,
    tags: Optional[List[str]] = None,
    verbose: bool = False
) -> bool:
    """
    Build Docker image
    
    Args:
        image_name: Name of the image to build
        dockerfile_path: Path to Dockerfile
        build_context: Build context directory
        build_args: Build arguments
        tags: Additional tags for the image
        verbose: Enable verbose output
        
    Returns:
        True if build successful, False otherwise
    """
    client = get_docker_client()
    
    # Check if Dockerfile exists
    dockerfile = Path(build_context) / dockerfile_path
    if not dockerfile.exists():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")
    
    if verbose:
        print(f"Building Docker image: {image_name}")
        print(f"Dockerfile: {dockerfile}")
        print(f"Build context: {build_context}")
    
    try:
        # Prepare tags list
        all_tags = [image_name]
        if tags:
            all_tags.extend(tags)
        
        # Set up build arguments with SPEC_FILE and PORT
        final_build_args = build_args or {}
        final_build_args['SPEC_FILE'] = spec_file
        final_build_args['PORT'] = str(port)
        
        # Build image with streaming output
        build_logs = client.api.build(
            path=build_context,
            dockerfile=dockerfile_path,
            tag=image_name,
            buildargs=final_build_args,
            decode=True,
            rm=True  # Remove intermediate containers
        )
        
        # Process build logs
        for log in build_logs:
            if verbose:
                if 'stream' in log:
                    print(log['stream'].strip())
                elif 'error' in log:
                    print(f"Error: {log['error']}")
                    return False
        
        # Tag additional tags if specified
        if tags:
            try:
                image = client.images.get(image_name)
                for tag in tags:
                    image.tag(tag)
                    if verbose:
                        print(f"Tagged image with: {tag}")
            except docker.errors.ImageNotFound:
                print(f"✗ Built image not found: {image_name}")
                return False
        
        if verbose:
            print(f"✓ Successfully built image: {image_name}")
        
        return True
        
    except BuildError as e:
        print(f"✗ Build failed: {e}")
        return False
    except APIError as e:
        print(f"✗ Docker API error during build: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during build: {e}")
        return False


def get_image_info(image_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a Docker image"""
    client = get_docker_client()
    
    try:
        image = client.images.get(image_name)
        
        return {
            'id': image.id,
            'short_id': image.short_id,
            'tags': image.tags,
            'labels': image.labels,
            'attrs': {
                'created': image.attrs.get('Created'),
                'size': image.attrs.get('Size'),
                'architecture': image.attrs.get('Architecture'),
                'os': image.attrs.get('Os')
            }
        }
        
    except docker.errors.ImageNotFound:
        return None
    except Exception:
        return None


def list_images(repository: Optional[str] = None) -> List[Dict[str, Any]]:
    """List Docker images"""
    client = get_docker_client()
    
    try:
        # Get all images or filter by repository
        if repository:
            images = client.images.list(name=repository)
        else:
            images = client.images.list()
        
        image_list = []
        for image in images:
            image_info = {
                'id': image.id,
                'short_id': image.short_id,
                'tags': image.tags,
                'created': image.attrs.get('Created'),
                'size': image.attrs.get('Size')
            }
            image_list.append(image_info)
        
        return image_list
        
    except Exception:
        return []


def remove_image(image_name: str, force: bool = False, verbose: bool = False) -> bool:
    """Remove Docker image"""
    client = get_docker_client()
    
    try:
        if verbose:
            print(f"Removing image: {image_name}")
        
        client.images.remove(image_name, force=force)
        
        if verbose:
            print(f"✓ Successfully removed image: {image_name}")
        
        return True
        
    except docker.errors.ImageNotFound:
        if verbose:
            print(f"Image not found: {image_name}")
        return False
    except APIError as e:
        print(f"✗ Error removing image: {e}")
        return False
    except Exception as e:
        print(f"✗ Error removing image: {e}")
        return False


def prune_images(verbose: bool = False) -> Dict[str, Any]:
    """Remove unused Docker images"""
    client = get_docker_client()
    
    try:
        if verbose:
            print("Pruning unused Docker images...")
        
        result = client.images.prune()
        
        if verbose:
            deleted_count = len(result.get('ImagesDeleted', []))
            reclaimed_space = result.get('SpaceReclaimed', 0)
            print(f"✓ Deleted {deleted_count} images, reclaimed {reclaimed_space} bytes")
        
        return result
        
    except Exception as e:
        print(f"✗ Error pruning images: {e}")
        return {}


def check_image_exists(image_name: str) -> bool:
    """Check if Docker image exists locally"""
    client = get_docker_client()
    
    try:
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception:
        return False
