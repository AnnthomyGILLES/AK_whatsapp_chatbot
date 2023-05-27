# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV ENV_WHATIA=PROD

# Run app.py when the container launches
#CMD ["python", "chatbot.py"]
#CMD ["uvicorn", "chatbot:app", "--host", "0.0.0.0", "--workers", "4"]
CMD ["uvicorn", "chatbot:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--ssl-keyfile", "/etc/letsencrypt/live/secure.whatia.fr/privkey.pem", "--ssl-certfile", "/etc/letsencrypt/live/secure.whatia.fr/fullchain.pem"]