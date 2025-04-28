# Use an official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if your project needs additional system libs, add them here)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential git \
       libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
# Assumes you have a requirements.txt generated via `pip freeze` or `kedro pipeline package` step
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire Kedro project into the container
COPY . .

# (Optional) Pre-compile your Kedro pipelines or run any build steps
# e.g., RUN kedro build-reqs

# Expose port if you plan to serve a Kedro API or UI
EXPOSE 4141

# Set the Kedro environment for configuration
ENV KEDRO_ENV=local

# Default entrypoint: run the Kedro pipeline
ENTRYPOINT ["kedro"]
CMD ["run"]
