
# Download and Setup Instructions for n8n and Local LLM on Mac

This guide provides step-by-step instructions to download and install the required software for running n8n with a local LLM (Ollama) on a Mac Studio M4 Max (128GB RAM, 2TB SSD) for automation, secured behind Cloudflare. The setup is designed for lawyers to process PDFs, images, and data with RAG, ensuring privacy and security.

## Prerequisites
- **Hardware**: Mac Studio M4 Max, 128GB RAM, 2TB SSD, running macOS 15 (Sequoia) or later.
- **Network**: Stable internet connection with a registered domain for Cloudflare.
- **Cloudflare Account**: Free or Pro account for DNS and tunneling.

## Downloads and Installation Steps

### 1. Install Homebrew
Homebrew is a package manager for macOS to simplify software installation.

- **Download**:
  - Open Terminal and run:
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
- **Verify**:
  - Run `brew --version` to confirm installation (e.g., `Homebrew 4.x.x`).

### 2. Install Docker Desktop
Docker Desktop is required to run n8n and Qdrant containers.

- **Download**:
  - Visit [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
  - Download the macOS version for Apple Silicon (M4).
  - Alternatively, install via Homebrew:
    ```bash
    brew install --cask docker
    ```
- **Install**:
  - Open the downloaded `.dmg` file, drag Docker to Applications, and launch it.
  - Enable “Start Docker Desktop when you log in” (Settings > General) for containers to run on power cycle.
- **Configure**:
  - In Docker Desktop Settings > Resources, allocate:
    - CPUs: 16
    - Memory: 32GB
    - Disk: 500GB
- **Verify**:
  - Run `docker --version` in Terminal (e.g., `Docker version 27.x.x`).
  - Run `docker run hello-world` to test.

### 3. Install Ollama
Ollama runs the local LLM and embedding models for RAG.

- **Download**:
  - Visit [ollama.ai/download](https://ollama.ai/download) and download the macOS version.
  - Alternatively, install via Homebrew:
    ```bash
    brew install ollama
    ```
- **Install**:
  - Open the `.dmg` file and follow prompts, or use Homebrew.
- **Pull Models**:
  - Run:
    ```bash
    ollama pull llama3.2:8b
    ollama pull nomic-embed-text
    ```
  - This downloads the Llama 3.2 8B model (~4.5GB) and nomic-embed-text (~250MB) for embeddings.
- **Start Service**:
  - Run `ollama serve` to start the server.
  - For auto-start on boot, create a launch agent:
    ```bash
    mkdir -p ~/Library/LaunchAgents
    cat << EOF > ~/Library/LaunchAgents/com.ollama.serve.plist
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.ollama.serve</string>
        <key>ProgramArguments</key>
        <array>
            <string>/opt/homebrew/bin/ollama</string>
            <string>serve</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
    </dict>
    </plist>
    EOF
    launchctl load ~/Library/LaunchAgents/com.ollama.serve.plist
    ```
- **Verify**:
  - Run `ollama run llama3.2:8b` and test with a prompt (e.g., “Hello, world!”).

### 4. Install Cloudflared
Cloudflared sets up a Cloudflare Tunnel to secure n8n and hide the Mac’s IP.

- **Download**:
  - Install via Homebrew:
    ```bash
    brew install cloudflared
    ```
- **Configure**:
  - Authenticate: `cloudflared tunnel login` (follow browser prompts to link to your Cloudflare account).
  - Create a tunnel: `cloudflared tunnel create n8n-tunnel`.
  - Create `~/.cloudflared/config.yml`:
    ```yaml
    tunnel: n8n-tunnel
    credentials-file: ~/.cloudflared/<tunnel-uuid>.json
    ingress:
      - hostname: n8n.yourdomain.com
        service: http://localhost:5678
      - service: http://status:503
    ```
    - Replace `n8n.yourdomain.com` with your domain.
  - Add DNS in Cloudflare Dashboard:
    - Create a CNAME record: `n8n.yourdomain.com` → `<tunnel-uuid>.cfargotunnel.com`.
- **Run**:
  - Start tunnel: `cloudflared tunnel run n8n-tunnel`.
  - For auto-start, create a launch agent:
    ```bash
    cat << EOF > ~/Library/LaunchAgents/com.cloudflare.tunnel.plist
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.cloudflare.tunnel</string>
        <key>ProgramArguments</key>
        <array>
            <string>/opt/homebrew/bin/cloudflared</string>
            <string>tunnel</string>
            <string>run</string>
            <string>n8n-tunnel</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
    </dict>
    </plist>
    EOF
    launchctl load ~/Library/LaunchAgents/com.cloudflare.tunnel.plist
    ```
- **Verify**:
  - Run `curl https://n8n.yourdomain.com` (should return a 503 until n8n is running).

### 5. Install Additional Tools
- **Git** (for cloning repositories):
  ```bash
  brew install git
  ```
- **Poppler** (for PDF processing):
  ```bash
  brew install poppler
  ```
- **Tesseract** (for image OCR):
  ```bash
  brew install tesseract
  ```

### 6. Set Up n8n Locally
n8n runs in a Docker container for automation workflows.

- **Create Directory**:
  ```bash
  mkdir ~/n8n-local && cd ~/n8n-local
  ```
- **Create `docker-compose.yml`**:
  ```yaml
  version: '3.9'
  services:
    n8n:
      image: n8nio/n8n:latest
      container_name: n8n
      restart: always
      ports:
        - "5678:5678"
      volumes:
        - ./n8n_data:/home/node/.n8n
      environment:
        - N8N_BASIC_AUTH_ACTIVE=true
        - N8N_BASIC_AUTH_USER=admin
        - N8N_BASIC_AUTH_PASSWORD=your_secure_password
        - N8N_HOST=n8n.yourdomain.com
        - N8N_PROTOCOL=https
        - N8N_PORT=5678
    qdrant:
      image: qdrant/qdrant:latest
      container_name: qdrant
      restart: always
      ports:
        - "6333:6333"
      volumes:
        - ./qdrant_data:/qdrant/storage
  ```
  - Replace `your_secure_password` and `n8n.yourdomain.com`.
- **Start n8n**:
  ```bash
  docker compose up -d
  ```
- **Verify**:
  - Access `https://n8n.yourdomain.com` in a browser.
  - Log in with `admin:your_secure_password`.

### 7. Security Setup
- **macOS Firewall**:
  - Enable: System Settings > Network > Firewall > Turn On.
  - Allow Docker Desktop and cloudflared.
- **Cloudflare WAF**:
  - In Cloudflare Dashboard, enable “Bot Fight Mode”.
  - Create a rule to block requests >100/minute from a single IP.
- **n8n Security**:
  - Enable 2FA in n8n settings after login.
  - Back up `~/n8n-local/n8n_data` regularly.

## Notes
- **Storage**: Ensure ~10GB free for Docker images, ~5GB for LLM models, and ~1GB for Qdrant data.
- **Performance**: The M4 Max with 128GB RAM can handle Llama 3.2 8B and n8n efficiently.
- **Next Steps**: After setup, create n8n workflows for RAG (e.g., PDF processing, LLM queries) as outlined in the main plan.
- **Support**: Join [community.n8n.io](https://community.n8n.io) or [ollama.ai/community](https://ollama.ai/community) for help.
```

### How to Download the Markdown File
To save this as a downloadable `.md` file on your Mac:

1. **Copy the Content**:
   - Copy the Markdown content above (everything between the ```markdown and ``` delimiters).

2. **Save to a File**:
   - Open a text editor (e.g., TextEdit, Visual Studio Code, or any code editor).
   - Paste the copied content.
   - Save the file with a `.md` extension, e.g., `Download-Setup-Instructions.md`.
     - In TextEdit: File > Save, name it `Download-Setup-Instructions.md`, and ensure the format is plain text.
     - In VS Code: File > Save As, name it `Download-Setup-Instructions.md`.

3. **Alternative: Create via Terminal**:
   - Open Terminal and run:
     ```bash
     cat << EOF > ~/Desktop/Download-Setup-Instructions.md
     # Paste the entire Markdown content here
     EOF
     ```
   - Replace `# Paste the entire Markdown content here` with the copied Markdown content above.
   - This creates the file on your Desktop.

4. **Verify**:
   - Open the file in a Markdown viewer (e.g., VS Code, Marked 2, or a browser with a Markdown plugin) to confirm it renders correctly.
   - The file should display formatted headings, lists, and code blocks.

### Why It’s Markdown
The content uses **Markdown syntax**, which is a lightweight markup language for formatting text. It includes:
- Headings (`#`, `##`) for structure.
- Bullet points (`-`) for lists.
- Code blocks (```bash, ```yaml) for commands and configurations.
- Links (e.g., `[docker.com](https://www.docker.com)`) for URLs.

The `<xaiArtifact>` tags in my previous response are part of this system’s internal mechanism to track and store the content as a Markdown artifact, but they’re not needed for the actual `.md` file. The cleaned-up version above is ready to be saved and used.

### Additional Notes
- **Docker Desktop Choice**: The setup uses **Docker Desktop** (as recommended in my first response) because it’s simpler for ensuring containers (n8n, Qdrant) restart on power cycle with minimal configuration. It’s ideal for your use case, especially for a turnkey solution on macOS.
- **File Usage**: The `.md` file is a guide for downloading and installing dependencies. Follow its steps in Terminal to set up Homebrew, Docker Desktop, Ollama, Cloudflared, and n8n.
- **Customization**: If you need a specific section expanded (e.g., n8n workflow details) or want the file in a different format (e.g., PDF), let me know.
- **Cloudflare Setup**: Ensure you have a registered domain in Cloudflare before starting, as it’s critical for hiding your Mac’s IP and preventing DoS attacks.

If you encounter issues saving the file or need help executing the steps, please clarify, and I can provide further guidance or alternative formats!