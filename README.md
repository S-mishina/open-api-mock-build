# OpenAPI Mock Build Tool

A tool to validate OpenAPI specifications and build/push container images with openapi-mock-server.

## Features

- Validate OpenAPI 3.0+ specifications
- Build Docker images with swagger-mock-api
- Push to various container registries (Docker Hub, AWS ECR, GCR, ACR)
- Function-based modular design
- Detailed logging and error handling

## Installation

```bash
xxx
```

## Usage

```bash
# Basic usage
open-api-mock-build sample-api.yaml -i my-mock-api:latest

# With registry
open-api-mock-build sample-api.yaml -i my-mock-api:latest -r my-registry.com

# Build only (no push)
open-api-mock-build sample-api.yaml -i my-mock-api:latest --no-push

# Verbose output
open-api-mock-build sample-api.yaml -i my-mock-api:latest -v
```

## Requirements

- Python 3.10+
- Docker
- PyYAML
- docker-py
