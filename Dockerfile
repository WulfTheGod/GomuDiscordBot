# Use Python as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the project files into the container
COPY . .

# Command to run your bot
CMD ["python", "gomu.py"]
