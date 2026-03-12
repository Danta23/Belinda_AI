# Use Arch Linux as base image
FROM archlinux:latest

# Update system and install packages
# We use -Syu to ensure the entire system is up-to-date
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    nodejs \
    npm \
    python \
    python-pip \
    lua \
    ffmpeg \
    curl \
    git \
    base-devel \
    fastfetch \
    toilet \
    cowsay \
    lolcat \
    figlet \
    speedtest-cli \
    fortune-mod \
    htop \
    neovim \
    nano \
    tree \
    unzip \
    wget \
    translate-shell \
    gawk \
    jq

# Install the absolute latest yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Force NPM to install the latest versions of dependencies
RUN rm -f package-lock.json && \
    npm install && \
    npm update

# Copy requirements
COPY requirements.txt ./

# Update pip and install latest python requirements
RUN python -m venv /app/venv && \
    /app/venv/bin/python -m pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -U -r requirements.txt

# Copy all project files
COPY . .

# Expose Flask port
EXPOSE 8000

# Run both Python backend and Node bridge
CMD ["bash", "-c", "/app/venv/bin/python app.py & node bridge.js"]
