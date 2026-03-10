# Gunakan Arch Linux sebagai base image
FROM archlinux:latest

# Update sistem dan instal paket dasar
# Kita instal nodejs, npm, python, pip, ffmpeg, dan curl
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    nodejs \
    npm \
    python \
    python-pip \
    ffmpeg \
    curl \
    git \
    base-devel

# Instal yt-dlp secara manual untuk versi terbaru
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Set direktori kerja
WORKDIR /app

# Copy package files dan instal dependensi Node.js
COPY package*.json ./
RUN npm install

# Copy requirements dan instal dependensi Python
# Di Arch Linux, pip mewajibkan penggunaan virtual environment
COPY requirements.txt ./
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy semua file project
COPY . .

# Expose port Flask
EXPOSE 8000

# Jalankan backend Python dan bridge Node.js secara bersamaan
CMD ["bash", "-c", "/app/venv/bin/python app.py & node bridge.js"]
