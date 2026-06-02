# ⌚ SmartDeck — Smartwatch PowerPoint Remote

> A PyQt6 desktop app that maps smartwatch media buttons to PowerPoint slide controls.  
> Features a dark UI, live key listener, animated status indicators, and manual nav buttons.

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52?style=flat&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Screenshots](#-screenshots)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Key Mappings](#-key-mappings)
- [Project Structure](#-project-structure)
- [Known Issues](#-known-issues)
- [License](#-license)

---

## 🧠 Overview

**SmartDeck** bridges your smartwatch and your presentations. When you press the **Next Track**, **Previous Track**, or **Play/Pause** media buttons on your smartwatch, SmartDeck intercepts those key events and forwards the correct arrow key (`→` / `←`) to PowerPoint — letting you advance or rewind slides hands-free from your wrist.

It runs as a lightweight background-aware desktop app with a polished dark interface, a live event log, and one-click manual controls for testing.

---

## ✨ Features

- 🎯 **Smartwatch media key detection** — maps Next/Prev/Play-Pause to slide navigation
- ⌨️ **Manual nav buttons** — test Prev / Play-Pause / Next directly inside the app
- 🟢 **Animated live indicator** — pulsing dot shows listener state at a glance
- 📋 **Live event log** — timestamped log of every detected key and triggered action
- ⚡ **Action flash card** — bottom strip highlights the last action with color coding
- 🔒 **Safe hook management** — unhooks only its own keyboard hook, leaves other apps untouched
- 🧹 **Clean shutdown** — hooks are always released when the window is closed

---

## 📸 Screenshots
<table align=center>
  <tr>
    <td><img src="img/Screenshot 2026-06-02 225231.png" width="400"></td>
    <td><img src="img/Screenshot 2026-06-02 225724.png" width="400"></td>
  </tr>
</table>

---
## ⚙️ Requirements

| Dependency | Version | Purpose |
|---|---|---|
| **Python** | `3.10` | Runtime |
| **PyQt6** | `6.x` | GUI framework |
| **keyboard** | `0.13.5+` | Global key hook / send |
| **mediapipe** | `0.10.9` | _(gesture recognition — future integration)_ |

> **Note:** `mediapipe 0.10.9` requires Python `3.10` — do not upgrade Python beyond `3.10.x` if you intend to use MediaPipe features.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/CodewithAz01/SmartDeck.git
cd smartdeck
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`**

```
PyQt6>=6.4.0
keyboard>=0.13.5
mediapipe==0.10.9
```

> ⚠️ **Windows only:** The `keyboard` library requires **administrator privileges** to hook global key events.  
> Run your terminal as Administrator, or the listener will silently fail.

---

## 🖥️ Usage

```bash
python powerpoint_remote.py
```

1. Open your PowerPoint presentation in **Slideshow mode**.
2. Launch SmartDeck.
3. Click **▶ START LISTENING**.
4. Press the **Next Track** or **Previous Track** button on your smartwatch.
5. SmartDeck will send the corresponding arrow key to advance or rewind slides.
6. Click **■ STOP LISTENING** when done.

---

## 🗺️ Key Mappings

| Smartwatch Button | Key Name Detected | Action Sent | Result |
|---|---|---|---|
| ⏭ Next Track | `next track`, `media next`, `next` | `→` (Right Arrow) | Next Slide |
| ⏮ Previous Track | `previous track`, `prev track`, `previous` | `←` (Left Arrow) | Previous Slide |
| ⏯ Play / Pause | `play/pause media`, `media play pause`, `play/pause` | _(logged only)_ | Play / Pause event |

> Different smartwatch brands may emit slightly different key names. Check the **Event Log** for the exact string your device sends, and add it to `KEY_MAP` in the source if needed.

---

## 📁 Project Structure

```
smartdeck/
│
├── powerpoint_remote.py   # Main application entry point
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🐛 Known Issues

- **Requires admin rights on Windows** — the `keyboard` library uses a low-level hook that needs elevated permissions.
- **Play/Pause action** is logged but does not yet send a key — this is intentional and reserved for future gesture-based integration with MediaPipe.
- **macOS / Linux** — partially supported by the `keyboard` library, but not tested with this app. Some key names may differ.

---

## 🔮 Roadmap

- [ ] MediaPipe gesture recognition integration (wave hand = next slide)
- [ ] System tray support (minimize to tray)
- [ ] Custom key mapping via settings panel
- [ ] macOS support

---

## 📄 License

This project is licensed under the **Abdullah Zahid** — feel free to use, modify, and distribute and make it perfect.

---

<p align="center">Made with ❤️ using Python 3.10 & PyQt6</p>
