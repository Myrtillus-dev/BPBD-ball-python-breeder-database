# 🐍 Ball Python Breeder Database (BPBD)

**From Breeder to Breeders** — Free, open source management software for ball python breeders.

Developed by Myrtillus Reptiles with assistance from AI tools.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Windows](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)

## Features
- 🐍 Animal profiles — genetics, morph and Het tracking
- 📋 Husbandry logs — feeding, weight, shed, cleaning
- ❤️ Health records — vet visits, medications, mite treatments
- 🥚 Clutch management — pairing to hatch, estimated hatch dates
- 🐣 Hatchling records — smart ID generation, sales tracking
- 🌳 Pedigree viewer — 3 generations + CoI calculator
- 📊 Dashboard — feeding alerts, active clutches, quick-log buttons
- 📥 CSV export and import — single table or all at once

## Download
👉 **[Download latest installer](../../releases/latest)**

No Python needed — the installer includes everything.

## Requirements
- Windows 10 or newer

## Installation
1. Download `Setup_BallPythonDB.exe`
2. Run the installer
3. Windows may show a security warning — click **"More info"** → **"Run anyway"**
4. Choose whether to add desktop and Start Menu shortcuts
5. Launch from shortcut or Start Menu

## Your data
All data is stored locally on your computer:
`C:\Users\YourName\AppData\Local\BallPythonDB\ballpython.db`

Your data never leaves your computer.

## For developers — Running from source
```bash
# Requirements: Python 3.8+, no external packages needed
git clone https://github.com/Myrtillus-dev/ball-python-breeder-database
cd ball-python-breeder-database
python main.py
```

## Building the installer
1. Install [NSIS](https://nsis.sourceforge.io/Download)
2. Run `build_installer.bat`
3. `Setup_BallPythonDB.exe` will be created

## License
This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

This means:
- ✅ Free to use and modify
- ✅ Free to distribute
- ✅ Improvements must be shared back under the same license
- ❌ Cannot be used in closed-source commercial products
- ❌ Cannot be sold without releasing the full source code

## Contributing
Issues and pull requests are welcome. If you improve the software, please share it back with the breeding community.

## About
Built for the ball python breeding community as a free alternative to paid breeding management software.
