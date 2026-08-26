#!/bin/bash
desktop=$(grep -l '^Name=WhatsApp Web$' ~/.local/share/applications/*.desktop 2>/dev/null | head -n1)
exec_cmd=$(sed -n 's/^Exec=//p' "$desktop" | head -n1)
eval "$exec_cmd" >/dev/null 2>&1 &
