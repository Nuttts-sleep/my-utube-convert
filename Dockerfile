# Start with a standard Python 3.11 image
FROM python:3.11-slim

# Install FFmpeg using the system's package manager
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside our "computer-in-a-box"
WORKDIR /app

# Copy our requirements file into the box
COPY requirements.txt .

# Install our Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code (app.py) into the box
COPY . .

# Tell Render what command to run when the server starts
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
