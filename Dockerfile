# Define the parent image. Use an official Python runtime image
FROM python:3.9-slim As builder

# Set the working directory
WORKDIR /usr/src/knowledge_map

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && apt-get

# Copy requirements from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application contents
COPY . . 

# Open the public port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "django_app.wsgi:application"]

