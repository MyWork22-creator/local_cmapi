FROM python:3.9-slim

WORKDIR /var/www/html

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8100

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]