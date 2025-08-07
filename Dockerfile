# OpenAPI Mock Server Dockerfile
FROM node:18-alpine

# Install @apidevtools/swagger-parser and express-openapi-mock
RUN npm install -g @stoplight/prism-cli

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

# Start the mock server using Prism
CMD sh -c "prism mock ./openapi-spec.yml --host 0.0.0.0 --port ${PORT}"
