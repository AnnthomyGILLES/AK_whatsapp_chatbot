# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV ENV_WHATIA=PROD

# Run the app using uvicorn server with 4 workers
CMD ["uvicorn", "chatbot:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
