# SecureDeal - Professional Bitcoin Contract Management
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (needed for PyO3/maturin)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Create app directory
WORKDIR /app

# Copy Python requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Rust project files
COPY rust_core/ ./rust_core/

# Build and install Rust extension
WORKDIR /app/rust_core
RUN maturin build --release
RUN pip install target/wheels/*.whl

# Go back to app directory
WORKDIR /app

# Copy application code
COPY . .

# Install Node.js for frontend build tools
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install frontend dependencies and build CSS
COPY package.json package-lock.json ./
RUN npm ci
RUN npm run build:css

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:create_app()"]

# Development stage
FROM base as development
USER root
RUN pip install --no-cache-dir pytest coverage black flake8 mypy
USER app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]

# Production stage
FROM base as production
ENV FLASK_ENV=production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
