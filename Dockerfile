# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Rust via rustup
#RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
#ENV PATH="/root/.cargo/bin:${PATH}"

# Install system dependencies if needed (e.g., for aiohttp, cryptography, or other packages)
# Uncomment if necessary:
RUN #apt-get update && apt-get install -y python3-dev libffi-dev libssl-dev && apt-get clean

# Install any needed packages specified in requirements.txt
RUN #pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV ENV_WHATIA=PROD

# Run app.py when the container launches
CMD ["uvicorn", "chatbot:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/etc/letsencrypt/live/secure.whatia.fr/privkey.pem", "--ssl-certfile", "/etc/letsencrypt/live/secure.whatia.fr/fullchain.pem"]
