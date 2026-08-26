#!/bin/bash
set -e

mkdir -p "$HOME/Pictures/Screenshots"

gnome-screenshot -f \
"$HOME/Pictures/Screenshots/Screenshot-$(date +%Y-%m-%d_%H-%M-%S).png"
