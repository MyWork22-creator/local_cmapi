# Stage 1: Build the application with dependencies
# Use a minimal Python image as the base
FROM python:3.9-slim

# Set the working directory in the container to a standard path
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt ./

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application source code into the container
# The '.' here refers to your project's root directory
COPY . .

# Expose the port that the FastAPI application will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# 'main:app' assumes your main file is named main.py and the FastAPI instance is 'app'
# This is the line that would need to be changed if your app is not in an 'app' directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
