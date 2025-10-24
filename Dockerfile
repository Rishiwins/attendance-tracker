# Use a pre-built image with OpenCV support
FROM python:3.11

WORKDIR /app

# Install system dependencies for face recognition
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    cmake \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-dev \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    ffmpeg \
    libopenblas-dev \
    liblapack-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages that are known to work
RUN pip install --no-cache-dir --upgrade pip

# Install core dependencies first
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    opencv-python-headless==4.8.1.78 \
    cmake

# Try to install dlib with timeout and fallback
RUN timeout 300 pip install --no-cache-dir dlib==19.24.2 || echo "dlib installation timed out, will use lite mode"

# Try to install face recognition with timeout and fallback
RUN timeout 300 pip install --no-cache-dir face-recognition==1.3.0 || echo "face-recognition installation timed out, will use lite mode"

# Copy and install remaining requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data logs

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]