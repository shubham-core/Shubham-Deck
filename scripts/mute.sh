#!/bin/bash
set -e
pactl set-sink-mute @DEFAULT_SINK@ toggle
