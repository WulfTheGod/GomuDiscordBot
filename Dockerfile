# Use Python as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . .

# Set environment variable for cookie path
ENV COOKIE_PATH=/app/cookies.txt

# Command to run your bot
CMD ["python", "gomu.py"]
