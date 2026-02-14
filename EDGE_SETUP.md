# Edge Hardware Setup Guide

Getting from bare metal to a running VIBE-Eyes instance requires work across three distinct layers, each described below.

---

## System: NVIDIA Jetson Orin Nano

Start here. Everything else builds on a properly configured Jetson. This will no doubt run on other hardware but these instructions target this particular edge device.

**Prerequisite Setup**
- Flash with the `jetson-orin-nano-devkit-super` board configuration
- Required: [Jetson Linux 36.5.x / Jetpack 6.2.2](https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html#updating-a-jetson-device) (removes obnoxiously restrictive 2.25GB Jetson NVMap heap cap)
- Ensure adequate cooling before sustained workloads

**Performance**
- Set MAXN_SUPER power mode
- Enable `jetson_clocks`
- OPTIONAL Consider a permanent switch to headless mode (`sudo systemctl set-default multi-user.target`) 

Confirm your MAXN_SUPER power mode with `sudo nvpmodel -q --verbose` (mine was 2, yours could be 0 or other)
 
```bash
sudo nvpmodel -m 2
```

Verify after reboot:
```bash
sudo tegrastats              # should run without error
nvpmodel -q                  # confirm MAXN
```

Optional: fire up clocks automatically 
```
sudo nano /etc/systemd/system/jetson_clocks.service

	[Unit]
	Description=Set Jetson Clocks to Maximum
	After=multi-user.target

	[Service]
	Type=oneshot
	ExecStart=/usr/bin/jetson_clocks
	RemainAfterExit=true

	[Install]
	WantedBy=multi-user.target
```

**Memory**
- Configure swap (required for SD-based systems, recommended for all)

```bash
sudo fallocate -l 8G /var/swapfile
sudo chmod 600 /var/swapfile
sudo mkswap /var/swapfile
sudo swapon /var/swapfile
echo '/var/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Recommended system packages**
```bash
sudo apt update
sudo apt install -y \
  build-essential \
  curl \
  git \
  git-lfs \
  tmux \
  htop \
  nvtop \
  jq \
  nano \
  libportaudio2 \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  nvidia-jetpack \
  nvidia-container-toolkit
```
---

## Development Environment

A lot of this is covered in the standard Reachy Mini and Reachy Mini Eyes Guides, but some quick things to confirm:

**Git and SSH**
```bash
git lfs install
```

**Python tooling**
Install `uv` (fast Python package/env manager, used throughout this project):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

**USB Device access**
```bash
sudo usermod -aG dialout $USER
```

Log out and back in (or `newgrp dialout`) for group changes to take effect.

---

## AI Runtime

**Install Ollama (so easy!)**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Note: Ollama will start and be automatically enabled at boot

**Pull the model used by the engine**

```bash
ollama pull nemotron-mini:4b-instruct-q5_K_M
```

**Optional: Install Hugging Face CLI** 
`curl -LsSf https://hf.co/cli/install.sh | bash`


---

## VIBE-Eyes engine setup

```bash
# Clone and enter the repo
git clone https://github.com/brainwavecollective/vibe-eyes
cd vibe-eyes

# Create environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .

# Download required NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Download NRC-VAD lexicon
mkdir -p data && cd data
wget http://saifmohammad.com/WebDocs/Lexicons/NRC-VAD-Lexicon-v2.1.zip
unzip NRC-VAD-Lexicon-v2.1.zip
rm NRC-VAD-Lexicon-v2.1.zip
```

Run the vibe-eyes engine:
```bash
uvicorn vibe_eyes.server:app --host 0.0.0.0 --port 8001
```

See the main README for running the full three-process stack with the Reachy Mini.
