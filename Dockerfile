# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=chatbot.py

# Set the directive to specify the executable that will run when the container is initiated
ENTRYPOINT [ "python" ]

# Run app.py when the container launches
CMD [ "chatbot.py" ]