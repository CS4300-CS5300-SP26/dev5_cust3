## Stage 1: Base build
# Define the parent image. Use an official Python runtime image
FROM python:3.13-slim As builder

# Create and Set the working directory
WORKDIR /app

# Set environment variables to optimize python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Updgrade pip
RUN pip install --upgrade pip 

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

## Stage 2: Production
FROM python:3.13-slim As production

# Create the dev user
RUN useradd -m -r knowledgeUser && mkdir /app && chown -R knowledgeUser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Set the working directory
WORKDIR /app
 
# Copy application code
COPY --chown=knowledgeUser:knowledgeUser . .

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Need to figure out what this is
ARG SECRET_KEY=build-time-placeholder
ENV SECRET_KEY=$SECRET_KEY

# collectstatic runs at build time; migrations should run at deploy time
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER knowledgeUser

# Open the public port
EXPOSE 8000

# Start the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "knowledge_map.wsgi:application"]

