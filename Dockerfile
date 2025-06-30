FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create and activate a virtual environment
RUN python -m venv venv \
    && . venv/bin/activate \
    && pip install --upgrade pip

# Copy dependencies file and install dependencies
COPY requirements.txt .
RUN . venv/bin/activate \
    && pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose the required port
EXPOSE 8056

# Set new working directory
WORKDIR /app/code

# Command to run the application
CMD ["/app/venv/bin/python", "councilcount_dashboard.py", "--docker"]