# Use an official Python runtime as a parent image
FROM python:3.9-slim


# Set the working directory in the container
WORKDIR /var/www/html
# Install system dependencies required by your Python packages
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

COPY ./var/www/html
# Set the correct permissions
RUN chown -R www-data:www-data /var/www/html

# Change the owner of the application directory to www-data
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache

# Expose the port the app runs on
EXPOSE 8100

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]