# Shubham Deck

Shubham Deck turns an old Android phone into a custom Stream Deck / Elgato-style touchscreen control panel for a Linux laptop.

## Architecture
Android Phone (Browser) -> Flask Web Dashboard (Port 5000) -> Linux Shell Scripts -> Laptop Applications / System Actions

## Features
- App Launcher: Open VS Code, Brave, WhatsApp Web, GitHub, Files, and Terminal.
- System Controls: Mute, Volume Up/Down, Lock Screen, and save Screenshots.
- System Monitoring: Live CPU, RAM, Disk, CPU Temperature, and Uptime statistics.
- Mobile-First UI: Dark theme, fullscreen support, large touch targets, and press animations.

## Running the Server
The application runs as a systemd user service. Do not run app.py manually.

To check status:
systemctl --user status shubham-deck.service

To restart:
systemctl --user restart shubham-deck.service

Access the deck on your phone at: http://<LAPTOP-IP>:5000/

## Future Roadmap
- V5 (AI Vision): Transform the phone camera into a smart local IP camera with real-time AI object/person detection.
