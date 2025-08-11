from .cli import parse_args
from . import openapi_validator
from . import container_builder
from . import container_pusher
from .argument_validator import validate_arguments
from .logger import get_logger, log_operation_start, log_operation_success, log_operation_failure


def main():
    """Main entry point for the application"""
    args = parse_args()
    
    # Setup logger
    logger = get_logger("main")
    
    # Validate arguments
    is_valid, error_message = validate_arguments(args)
    if not is_valid:
        logger.error(error_message)
        return 1
    
    logger.info("OpenAPI Container Build Tool")
    logger.info(f"Spec file: {args.spec_file}")
    logger.info(f"Image: {args.image}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Registry: {args.registry}")
    logger.info(f"Push to registry: {not args.no_push}")
    logger.info(f"Verbose: {args.verbose}")
    
    try:
        # Step 1: Validate OpenAPI specification
        log_operation_start(logger, "OpenAPI specification validation")
        validation_result = openapi_validator.validate_file(
            spec_file=args.spec_file,
            verbose=args.verbose
        )
        
        if not validation_result['valid']:
            logger.error(f"✗ OpenAPI validation failed: {validation_result['message']}")
            return 1
        
        log_operation_success(logger, "OpenAPI specification validation")
        
        if args.verbose:
            info = validation_result['validation_result']
            logger.debug(f"  Title: {info['title']}")
            logger.debug(f"  Version: {info['version']}")
            logger.debug(f"  Spec Version: {info['spec_version']}")
            logger.debug(f"  Paths: {info['paths_count']}")
        
        # Step 2: Build container image
        log_operation_start(logger, "container image build")
        
        # Check docker availability
        if not container_builder.check_docker_available(verbose=args.verbose):
            logger.error("✗ Docker is not available or not running")
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
            logger.error("✗ Container build failed")
            return 1
        
        log_operation_success(logger, "container image build")
        
        # Step 3: Push container image (if not disabled)
        if not args.no_push:
            log_operation_start(logger, "container image push")
            
            # Check docker availability
            if not container_pusher.check_docker_available(verbose=args.verbose):
                logger.error("✗ Docker is not available or not running")
                return 1
            
            # Login to registry if specified
            if args.registry:
                login_success = container_pusher.login_to_registry(
                    registry=args.registry,
                    verbose=args.verbose
                )
                if not login_success:
                    logger.error("✗ Registry login failed")
                    return 1
            
            # Push image
            push_success = container_pusher.push_image(
                image_name=args.image,
                registry=args.registry,
                verbose=args.verbose
            )
            
            if not push_success:
                logger.error("✗ Container push failed")
                return 1
            
            log_operation_success(logger, "container image push")
        else:
            logger.info("Step 3: Skipping push (--no-push specified)")
        
        logger.info("🎉 All steps completed successfully!")
        return 0
        
    except Exception as e:
        log_operation_failure(logger, "main execution", e)
        return 1
    

if __name__ == "__main__":
    main()
