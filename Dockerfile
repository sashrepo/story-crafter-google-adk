# Use Python 3.12 base image
FROM python:3.12-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Streamlit configuration
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures strict adherence to uv.lock
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . .

# Expose the port (default for Cloud Run is 8080)
EXPOSE 8080

# Run the application
# Use shell to allow variable expansion for PORT
CMD ["sh", "-c", "uv run streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]

