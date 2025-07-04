
FROM python:3.10.4-slim-buster

# Install dependencies
RUN apt-get update && apt-get install -y python3-pip curl ffmpeg

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port Flask will use
EXPOSE 5000

# Command to run the application
CMD ["python3", "app.py"]
