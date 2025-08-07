from .cli import parse_args
from . import openapi_validator
from . import container_builder
from . import container_pusher


def main():
    """Main entry point for the application"""
    args = parse_args()
    
    print(f"OpenAPI Container Build Tool")
    print(f"Spec file: {args.spec_file}")
    print(f"Image: {args.image}")
    print(f"Port: {args.port}")
    print(f"Registry: {args.registry}")
    print(f"Push to registry: {not args.no_push}")
    print(f"Verbose: {args.verbose}")
    print()
    
    try:
        # Step 1: Validate OpenAPI specification
        print("Step 1: Validating OpenAPI specification...")
        validation_result = openapi_validator.validate_file(
            spec_file=args.spec_file,
            verbose=args.verbose
        )
        
        if not validation_result['valid']:
            print(f"✗ OpenAPI validation failed: {validation_result['message']}")
            return 1
        
        print("✓ OpenAPI specification validation passed")
        
        if args.verbose:
            info = validation_result['validation_result']
            print(f"  Title: {info['title']}")
            print(f"  Version: {info['version']}")
            print(f"  Spec Version: {info['spec_version']}")
            print(f"  Paths: {info['paths_count']}")
        print()
        
        # Step 2: Build container image
        print("Step 2: Building container image...")
        
        # Check docker availability
        if not container_builder.check_docker_available(verbose=args.verbose):
            print("✗ Docker is not available or not running")
            return 1
        
        build_success = container_builder.build_image(
            image_name=args.image,
            spec_file=args.spec_file,  # OpenAPI specification file
            port=args.port,  # Port number for mock server
            dockerfile_path="Dockerfile",  # Fixed application setting
            build_context=".",  # Fixed application setting
            verbose=args.verbose
        )
        
        if not build_success:
            print("✗ Container build failed")
            return 1
        
        print("✓ Container image built successfully")
        print()
        
        # Step 3: Push container image (if not disabled)
        if not args.no_push:
            print("Step 3: Pushing container image...")
            
            # Check docker availability
            if not container_pusher.check_docker_available(verbose=args.verbose):
                print("✗ Docker is not available or not running")
                return 1
            
            # Login to registry if specified
            if args.registry:
                login_success = container_pusher.login_to_registry(
                    registry=args.registry,
                    verbose=args.verbose
                )
                if not login_success:
                    print("✗ Registry login failed")
                    return 1
            
            # Push image
            push_success = container_pusher.push_image(
                image_name=args.image,
                registry=args.registry,
                verbose=args.verbose
            )
            
            if not push_success:
                print("✗ Container push failed")
                return 1
            
            print("✓ Container image pushed successfully")
        else:
            print("Step 3: Skipping push (--no-push specified)")
        
        print()
        print("🎉 All steps completed successfully!")
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    

if __name__ == "__main__":
    main()
