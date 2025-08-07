# OpenAPI Mock Server Dockerfile
FROM node:18-alpine

# Install openapi-mock-server
RUN npm install -g swagger-mock-api

# Create app directory
WORKDIR /app

# Copy OpenAPI specification file
ARG SPEC_FILE
COPY ${SPEC_FILE} ./openapi-spec.yml

# Set port as build argument
ARG PORT=3000

# Expose port
EXPOSE ${PORT}

# Health check
RUN apk add --no-cache curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start the mock server
CMD sh -c "swagger-mock-api ./openapi-spec.yml --port ${PORT} --host 0.0.0.0"
