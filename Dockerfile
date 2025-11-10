FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for Alpine
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    curl

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY garmin_mcp_server_http.py .
COPY modules/ ./modules/

# Create directory for Garmin tokens (matching docker-compose volume mount)
RUN mkdir -p /data/.garminconnect

# Expose port for MCP server (using HTTP transport)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GARMINTOKENS=/data/.garminconnect

# Run the server using FastMCP CLI (required for host/port binding)
CMD ["fastmcp", "run", "garmin_mcp_server_http.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
