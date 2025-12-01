# 📡 Raspberry Pi 5 FM Message Broadcaster

Polls the Picnic API for chat messages, logs **new** messages, and broadcasts them over FM radio using a Raspberry Pi.

The project:

- Fetches messages from the Picnic `/api/v1/fm/get-chat` endpoint  
- Detects and handles only **new** messages  
- Logs all received messages to a text file  
- Sends each new message to an FM transmitter (GPIO FM or external TX)

> ⚠️ **Note:** GPIO-based FM transmitting is experimental on Raspberry Pi 5. It may require extra tweaking or a different transmitter solution (USB FM, external RF module, etc.).

---

## ✨ Features

- Fetches chat/messages from the Picnic API (`/api/v1/fm/get-chat`)
- Uses Bearer token authentication
- Detects **new** messages only (no re-broadcast)
- Logs all messages to `messages_log.txt`
- Converts text messages to audio via TTS (e.g. `espeak`, in your script)
- Sends audio to an FM transmitter (e.g. [`fm_transmitter`](https://github.com/markondej/fm_transmitter) or `rpitx`)
- Runs in a loop and checks for new messages every few seconds

---

## ⚙️ Hardware Requirements

### Required

- **Raspberry Pi 5**
- Internet connection (Wi-Fi or Ethernet)
- FM antenna:
  - A piece of wire (~20–40 cm) connected to **GPIO4 (pin 7)**

> 🔎 GPIO FM on Pi 5 is not officially supported by many older tools. If it doesn’t work, consider a USB FM transmitter or an older Pi (3/4).

### Optional (if not using GPIO FM)

- USB FM transmitter  
- External FM modulator  
- Any FM-capable SDR hardware  

---

## 🧰 Software Requirements

### System packages (Raspberry Pi OS)

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip espeak git make gcc
