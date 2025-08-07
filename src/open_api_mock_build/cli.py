import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog='open-api-mock-build',
        description='Validate OpenAPI specification and build/push container image'
    )
    
    # Required argument: OpenAPI specification file path
    parser.add_argument(
        'spec_file',
        help='Path to OpenAPI specification file (JSON or YAML)'
    )
    
    # Required argument: Container image name
    parser.add_argument(
        '-i', '--image',
        required=True,
        help='Container image name (e.g., my-app:latest)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-r', '--registry',
        help='Container registry URL (e.g., docker.io, <account>.dkr.ecr.<region>.amazonaws.com)'
    )
    
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Build image but do not push to registry'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=3000,
        help='Port number for mock server (default: 3000)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    return parser


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = create_parser()
    return parser.parse_args(args)
