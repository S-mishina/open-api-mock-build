# OpenAPI Mock Build Tool

A comprehensive tool to validate OpenAPI specifications and build/push container images with mock API servers. Features robust error handling, argument validation, and support for multiple container registries.

## Features

- ✅ **OpenAPI Validation**: Validate OpenAPI 3.0+ specifications with detailed error reporting
- 🐳 **Container Building**: Build Docker images with swagger-mock-api server
- 🚀 **Multi-Registry Support**: Push to Docker Hub, AWS ECR, Google Container Registry (GCR), Azure Container Registry (ACR), and more
- 🔍 **Intelligent Validation**: Pre-flight checks for common mistakes like incorrect registry URL format
- 📝 **Comprehensive Logging**: Detailed logging with verbose mode for troubleshooting
- 🛠️ **Error Handling**: Robust error detection and user-friendly error messages
- 🏗️ **Modular Design**: Function-based architecture with comprehensive test coverage

## Installation

```bash
xxx
```

## Usage

### Basic Usage

```bash
# Validate, build, and push to Docker Hub
open-api-mock-build api.yaml -i my-mock-api:latest

# Build only (no push)
open-api-mock-build api.yaml -i my-mock-api:latest --no-push

# Verbose output for debugging
open-api-mock-build api.yaml -i my-mock-api:latest -v
```

### Registry Examples

```bash
# AWS ECR
open-api-mock-build api.yaml -i my-mock-api:latest -r 123456789.dkr.ecr.us-east-1.amazonaws.com

# Google Container Registry
open-api-mock-build api.yaml -i my-mock-api:latest -r gcr.io

# Azure Container Registry
open-api-mock-build api.yaml -i my-mock-api:latest -r myregistry.azurecr.io

# Custom registry with port
open-api-mock-build api.yaml -i my-mock-api:latest -r registry.example.com:5000
```

### Important: Registry URL Format

⚠️ **Common Mistake**: Do not include the image name in the registry URL.

```bash
# ❌ Incorrect - includes image name in registry URL
open-api-mock-build api.yaml -i my-api:latest -r registry.com/my-namespace/my-api

# ✅ Correct - separate registry and image name
open-api-mock-build api.yaml -i my-namespace/my-api:latest -r registry.com
```

The tool will detect this mistake and provide helpful correction suggestions.

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `spec_file` | - | Path to OpenAPI specification file (JSON or YAML) | Required |
| `--image` | `-i` | Container image name (e.g., my-app:latest) | Required |
| `--registry` | `-r` | Container registry URL (hostname only) | None |
| `--no-push` | - | Build image but do not push to registry | False |
| `--port` | `-p` | Port number for mock server | 3000 |
| `--verbose` | `-v` | Enable verbose output | False |
| `--version` | - | Show version information | - |

## Error Handling

The tool provides intelligent error detection and user-friendly messages:

- **Registry Format Validation**: Detects common registry URL mistakes
- **Push Error Detection**: Properly identifies and reports Docker push failures
- **OpenAPI Validation**: Comprehensive validation with detailed error messages
- **Docker Availability**: Checks Docker daemon availability before operations

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_argument_validator.py -v
```

## Requirements

- Python 3.10+
- Docker Engine
- AWS CLI (for ECR authentication)

### Python Dependencies

- PyYAML
- docker
- jsonschema
- openapi-spec-validator
