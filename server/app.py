from flask import Flask, jsonify, render_template_string
from pathlib import Path
import subprocess
import shutil
import time

app = Flask(__name__)

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path("/home/shubham/Desktop/Shubham-Deck")
SCRIPTS_DIR = PROJECT_DIR / "scripts"

# ============================================================
# COMMAND REGISTRY
# ============================================================

COMMANDS = {
    # Apps
    "vscode": SCRIPTS_DIR / "vscode.sh",
    "brave": SCRIPTS_DIR / "brave.sh",
    "whatsapp": SCRIPTS_DIR / "whatsapp.sh",
    "github": SCRIPTS_DIR / "github.sh",
    "files": SCRIPTS_DIR / "files.sh",
    "terminal": SCRIPTS_DIR / "terminal.sh",

    # System
    "mute": SCRIPTS_DIR / "mute.sh",
    "volume-up": SCRIPTS_DIR / "volume-up.sh",
    "volume-down": SCRIPTS_DIR / "volume-down.sh",
    "lock": SCRIPTS_DIR / "lock.sh",
    "screenshot": SCRIPTS_DIR / "screenshot.sh",
}


# ============================================================
# HELPERS
# ============================================================

def read_cpu_usage():
    """
    Calculate CPU usage from /proc/stat without requiring
    extra packages.
    """
    def sample():
        with open("/proc/stat", "r", encoding="utf-8") as f:
            line = f.readline()

        values = list(map(int, line.split()[1:]))

        user, nice, system, idle, iowait, irq, softirq, steal = values[:8]

        idle_total = idle + iowait
        total = sum(values)

        return total, idle_total

    total1, idle1 = sample()
    time.sleep(0.12)
    total2, idle2 = sample()

    total_delta = total2 - total1
    idle_delta = idle2 - idle1

    if total_delta <= 0:
        return 0.0

    usage = (1 - (idle_delta / total_delta)) * 100

    return round(max(0.0, min(100.0, usage)), 1)


def read_memory():
    """
    Return RAM usage information from /proc/meminfo.
    """
    values = {}

    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0])

    total_kb = values.get("MemTotal", 0)
    available_kb = values.get("MemAvailable", 0)

    used_kb = total_kb - available_kb

    if total_kb <= 0:
        return {
            "used_gb": 0,
            "total_gb": 0,
            "percent": 0,
        }

    used_gb = used_kb / 1024 / 1024
    total_gb = total_kb / 1024 / 1024
    percent = (used_kb / total_kb) * 100

    return {
        "used_gb": round(used_gb, 1),
        "total_gb": round(total_gb, 1),
        "percent": round(percent, 1),
    }


def read_disk():
    """
    Return root filesystem usage.
    """
    total, used, free = shutil.disk_usage("/")

    total_gb = total / 1024 / 1024 / 1024
    used_gb = used / 1024 / 1024 / 1024
    free_gb = free / 1024 / 1024 / 1024

    percent = (used / total) * 100 if total else 0

    return {
        "used_gb": round(used_gb, 1),
        "total_gb": round(total_gb, 1),
        "free_gb": round(free_gb, 1),
        "percent": round(percent, 1),
    }


def read_temperature():
    """
    Try to obtain CPU temperature from lm-sensors/sysfs.
    Returns None when unavailable.
    """

    # First try lm-sensors.
    sensors = shutil.which("sensors")

    if sensors:
        try:
            result = subprocess.run(
                [sensors],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            text = result.stdout

            for line in text.splitlines():
                if "Package id 0:" in line:
                    parts = line.split()

                    for part in parts:
                        if part.endswith("°C"):
                            cleaned = part.replace("+", "").replace("°C", "")
                            try:
                                return round(float(cleaned), 1)
                            except ValueError:
                                pass

                if "Tctl:" in line or "Tdie:" in line:
                    parts = line.split()

                    for part in parts:
                        if part.endswith("°C"):
                            cleaned = part.replace("+", "").replace("°C", "")
                            try:
                                return round(float(cleaned), 1)
                            except ValueError:
                                pass

        except Exception:
            pass

    # Fallback: thermal-zone files.
    thermal_root = Path("/sys/class/thermal")

    if thermal_root.exists():
        for zone in thermal_root.glob("thermal_zone*/temp"):
            try:
                raw = int(zone.read_text().strip())
                temp = raw / 1000

                if -20 <= temp <= 120:
                    return round(temp, 1)
            except Exception:
                continue

    return None


def read_uptime():
    """
    Read Linux uptime.
    """
    try:
        seconds = float(
            Path("/proc/uptime").read_text().split()[0]
        )

        seconds = int(seconds)

        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        if days:
            return f"{days}d {hours}h {minutes}m"

        if hours:
            return f"{hours}h {minutes}m"

        return f"{minutes}m"

    except Exception:
        return "Unknown"


# ============================================================
# DASHBOARD
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="
            width=device-width,
            initial-scale=1,
            maximum-scale=1,
            user-scalable=no,
            viewport-fit=cover
        "
    >

    <meta name="theme-color" content="#070707">

    <link
        rel="manifest"
        href="/static/manifest.json"
    >

    <title>Shubham Deck</title>

    <style>

        /* ====================================================
           RESET
           ==================================================== */

        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        html,
        body {
            margin: 0;
            width: 100%;
            height: 100%;

            background:
                radial-gradient(
                    circle at 50% -10%,
                    #202020 0,
                    #0c0c0c 35%,
                    #050505 100%
                );

            color: #fff;

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            overflow: hidden;

            touch-action: manipulation;
        }

        body {
            display: flex;
            align-items: center;
            justify-content: center;
        }


        /* ====================================================
           DECK
           ==================================================== */

        .deck {
            width: 100%;
            height: 100%;

            max-width: 1200px;

            padding:
                max(12px, env(safe-area-inset-top))
                max(12px, env(safe-area-inset-right))
                max(12px, env(safe-area-inset-bottom))
                max(12px, env(safe-area-inset-left));

            display: flex;
            flex-direction: column;
        }


        /* ====================================================
           TOP BAR
           ==================================================== */

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;

            min-height: 52px;

            margin-bottom: 10px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-mark {
            width: 36px;
            height: 36px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 11px;

            background:
                linear-gradient(
                    145deg,
                    #353535,
                    #181818
                );

            border: 1px solid #3c3c3c;

            box-shadow:
                inset 0 1px 0
                    rgba(255,255,255,.08);
        }

        .brand-text {
            font-size: clamp(18px, 4vw, 28px);
            font-weight: 850;
            letter-spacing: .8px;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 7px;

            padding: 7px 10px;

            border: 1px solid #252525;
            border-radius: 999px;

            background: rgba(20,20,20,.8);

            color: #929292;

            font-size: 10px;
            font-weight: 800;

            letter-spacing: .3px;
        }

        .status-dot {
            width: 8px;
            height: 8px;

            border-radius: 50%;

            background: #38e58b;

            box-shadow:
                0 0 10px
                rgba(56,229,139,.75);
        }


        /* ====================================================
           FULLSCREEN
           ==================================================== */

        #fullscreenBtn {
            position: fixed;

            top: max(
                10px,
                env(safe-area-inset-top)
            );

            right: max(
                10px,
                env(safe-area-inset-right)
            );

            z-index: 9999;

            width: 44px;
            height: 40px;

            border: 1px solid #333;
            border-radius: 12px;

            background: rgba(30,30,30,.95);
            color: white;

            font-size: 20px;
            font-weight: 800;

            cursor: pointer;

            box-shadow:
                0 8px 24px rgba(0,0,0,.4);

            backdrop-filter: blur(10px);
        }

        #fullscreenBtn:active {
            transform: scale(.88);
        }


        /* ====================================================
           NAVIGATION
           ==================================================== */

        .nav {
            display: grid;

            grid-template-columns:
                repeat(3, 1fr);

            gap: 7px;

            margin-bottom: 10px;
        }

        .nav-btn {
            height: 39px;

            border: 1px solid #252525;
            border-radius: 11px;

            background: #111;

            color: #777;

            font-size: 11px;
            font-weight: 850;

            cursor: pointer;

            transition:
                background .12s ease,
                color .12s ease,
                transform .08s ease;
        }

        .nav-btn.active {
            color: #fff;

            background:
                linear-gradient(
                    145deg,
                    #292929,
                    #181818
                );

            border-color: #454545;
        }

        .nav-btn:active {
            transform: scale(.96);
        }


        /* ====================================================
           PAGE
           ==================================================== */

        .page {
            display: none;

            flex: 1;

            min-height: 0;
        }

        .page.active {
            display: flex;
            flex-direction: column;
        }


        /* ====================================================
           APP / SYSTEM GRID
           ==================================================== */

        .deck-grid {
            flex: 1;
            min-height: 0;

            display: grid;

            grid-template-columns:
                repeat(3, minmax(0, 1fr));

            grid-template-rows:
                repeat(2, minmax(0, 1fr));

            gap: 10px;
        }


        /* ====================================================
           KEY
           ==================================================== */

        .key {
            min-width: 0;
            min-height: 0;

            border: 1px solid #292929;
            border-radius: 20px;

            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(255,255,255,.07),
                    transparent 42%
                ),
                linear-gradient(
                    145deg,
                    #191919,
                    #101010
                );

            color: white;

            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;

            gap: 9px;

            padding: 9px;

            cursor: pointer;

            box-shadow:
                inset 0 1px 0
                    rgba(255,255,255,.035),

                0 7px 18px
                    rgba(0,0,0,.27);

            transition:
                transform .09s ease,
                background .09s ease,
                border-color .09s ease;
        }

        .key:active,
        .key.pressed {
            transform: scale(.94);

            border-color: #656565;

            background:
                radial-gradient(
                    circle at 50% 30%,
                    rgba(255,255,255,.13),
                    transparent 50%
                ),
                #222;
        }


        /* ====================================================
           APP ICON
           ==================================================== */

        .icon {
            width:
                clamp(48px, 9vw, 82px);

            height:
                clamp(48px, 9vw, 82px);

            object-fit: contain;

            pointer-events: none;
            user-select: none;

            filter:
                drop-shadow(
                    0 5px 10px
                    rgba(0,0,0,.4)
                );
        }


        /* ====================================================
           EMOJI ICON
           ==================================================== */

        .emoji-icon {
            font-size:
                clamp(40px, 8vw, 68px);

            line-height: 1;

            pointer-events: none;
            user-select: none;
        }


        /* ====================================================
           LABEL
           ==================================================== */

        .label {
            font-size:
                clamp(11px, 2.15vw, 16px);

            font-weight: 800;

            line-height: 1.1;

            text-align: center;

            pointer-events: none;
            user-select: none;
        }


        /* ====================================================
           SYSTEM STATS
           ==================================================== */

        .stats-wrap {
            flex: 1;

            min-height: 0;

            display: flex;
            flex-direction: column;

            gap: 10px;
        }

        .stats-grid {
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: 10px;

            flex: 1;
        }

        .stat-card {
            border: 1px solid #292929;
            border-radius: 18px;

            background:
                linear-gradient(
                    145deg,
                    #191919,
                    #101010
                );

            padding: 15px;

            display: flex;
            flex-direction: column;
            justify-content: space-between;

            min-height: 0;
        }

        .stat-head {
            color: #777;

            font-size: 10px;

            font-weight: 850;

            letter-spacing: 1px;
        }

        .stat-value {
            font-size:
                clamp(21px, 5vw, 36px);

            font-weight: 850;
        }

        .stat-sub {
            color: #777;

            font-size: 10px;

            font-weight: 700;
        }

        .meter {
            width: 100%;
            height: 7px;

            border-radius: 99px;

            overflow: hidden;

            background: #252525;
        }

        .meter > span {
            display: block;

            height: 100%;

            width: 0%;

            background:
                linear-gradient(
                    90deg,
                    #777,
                    #ddd
                );

            border-radius: inherit;

            transition:
                width .35s ease;
        }

        .refresh-btn {
            min-height: 43px;

            border: 1px solid #303030;
            border-radius: 13px;

            background: #171717;

            color: #fff;

            font-weight: 850;

            cursor: pointer;
        }


        /* ====================================================
           AI VISION PAGE
           ==================================================== */

        .vision-shell {
            flex: 1;

            min-height: 0;

            display: flex;
            flex-direction: column;

            gap: 10px;
        }

        .camera-panel {
            position: relative;

            flex: 1;

            min-height: 0;

            border:
                1px solid #292929;

            border-radius: 20px;

            background:
                radial-gradient(
                    circle,
                    #171717,
                    #0b0b0b
                );

            display: flex;
            align-items: center;
            justify-content: center;

            overflow: hidden;
        }

        .camera-placeholder {
            text-align: center;
            color: #777;
        }

        .camera-icon {
            font-size: 56px;
            margin-bottom: 10px;
        }

        .camera-title {
            color: #aaa;
            font-weight: 850;
        }

        .camera-sub {
            margin-top: 5px;
            font-size: 11px;
            color: #555;
        }

        .vision-controls {
            display: grid;

            grid-template-columns:
                repeat(2, 1fr);

            gap: 8px;
        }

        .vision-btn {
            min-height: 43px;

            border:
                1px solid #2a2a2a;

            border-radius: 13px;

            background: #171717;

            color: #fff;

            font-weight: 800;

            cursor: pointer;
        }


        /* ====================================================
           TOAST
           ==================================================== */

        #toast {
            position: fixed;

            left: 50%;
            bottom: 25px;

            transform:
                translateX(-50%);

            z-index: 20000;

            max-width: 88%;

            padding:
                10px
                14px;

            border:
                1px solid #3a3a3a;

            border-radius: 12px;

            background:
                rgba(25,25,25,.96);

            color: #fff;

            font-size: 12px;

            font-weight: 750;

            box-shadow:
                0 10px 30px
                rgba(0,0,0,.45);

            opacity: 0;

            pointer-events: none;

            transition:
                opacity .2s ease;
        }


        /* ====================================================
           RESPONSIVE
           ==================================================== */

        @media (max-width: 600px) {

            .deck-grid {
                gap: 8px;
            }

            .key {
                border-radius: 16px;
            }

            .stats-grid {
                gap: 8px;
            }

            .stat-card {
                border-radius: 15px;
                padding: 12px;
            }
        }

        @media (orientation: landscape) {

            .deck {
                max-width: 1200px;
            }

            .deck-grid {
                gap: 9px;
            }

            .icon {
                width:
                    clamp(45px, 8vh, 75px);

                height:
                    clamp(45px, 8vh, 75px);
            }

            .emoji-icon {
                font-size:
                    clamp(38px, 7vh, 60px);
            }
        }


    </style>

</head>


<body>


<!-- ============================================================
     FULLSCREEN BUTTON
     ============================================================ -->

<button
    id="fullscreenBtn"
    onclick="goFullscreen()"
    aria-label="Enter fullscreen"
>
    ⛶
</button>


<!-- ============================================================
     MAIN
     ============================================================ -->

<main class="deck">


    <!-- HEADER -->

    <header class="topbar">

        <div class="brand">

            <div class="brand-mark">
                ⚡
            </div>

            <div class="brand-text">
                SHUBHAM DECK
            </div>

        </div>


        <div class="status">

            <span class="status-dot"></span>

            ONLINE

        </div>

    </header>


    <!-- ========================================================
         NAV
         ======================================================== -->

    <nav class="nav">

        <button
            class="nav-btn active"
            onclick="switchPage('apps', this)"
        >
            APPS
        </button>

        <button
            class="nav-btn"
            onclick="switchPage('system', this)"
        >
            SYSTEM
        </button>

        <button
            class="nav-btn"
            onclick="switchPage('vision', this)"
        >
            AI VISION
        </button>

    </nav>


    <!-- ========================================================
         APPS
         ======================================================== -->

    <section
        id="apps"
        class="page active"
    >

        <div class="deck-grid">


            <button
                class="key"
                onclick="runCommand('vscode', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/vscode.png"
                    alt=""
                >

                <span class="label">
                    VS Code
                </span>
            </button>


            <button
                class="key"
                onclick="runCommand('brave', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/brave.png"
                    alt=""
                >

                <span class="label">
                    Brave
                </span>
            </button>


            <button
                class="key"
                onclick="runCommand('whatsapp', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/whatsapp.ico"
                    alt=""
                >

                <span class="label">
                    WhatsApp
                </span>
            </button>


            <button
                class="key"
                onclick="runCommand('github', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/github.svg"
                    alt=""
                >

                <span class="label">
                    GitHub
                </span>
            </button>


            <button
                class="key"
                onclick="runCommand('files', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/files.svg"
                    alt=""
                >

                <span class="label">
                    Files
                </span>
            </button>


            <button
                class="key"
                onclick="runCommand('terminal', this)"
            >
                <img
                    class="icon"
                    src="/static/icons/terminal.svg"
                    alt=""
                >

                <span class="label">
                    Terminal
                </span>
            </button>


        </div>

    </section>


    <!-- ========================================================
         SYSTEM
         ======================================================== -->

    <section
        id="system"
        class="page"
    >

        <div class="stats-wrap">


            <!-- SYSTEM CONTROL BUTTONS -->

            <div class="deck-grid">

                <button
                    class="key"
                    onclick="runCommand('mute', this)"
                >
                    <span class="emoji-icon">
                        🔇
                    </span>

                    <span class="label">
                        Mute
                    </span>
                </button>


                <button
                    class="key"
                    onclick="runCommand('volume-up', this)"
                >
                    <span class="emoji-icon">
                        🔊
                    </span>

                    <span class="label">
                        Volume +
                    </span>
                </button>


                <button
                    class="key"
                    onclick="runCommand('volume-down', this)"
                >
                    <span class="emoji-icon">
                        🔉
                    </span>

                    <span class="label">
                        Volume -
                    </span>
                </button>


                <button
                    class="key"
                    onclick="runCommand('lock', this)"
                >
                    <span class="emoji-icon">
                        🔒
                    </span>

                    <span class="label">
                        Lock
                    </span>
                </button>


                <button
                    class="key"
                    onclick="runCommand('screenshot', this)"
                >
                    <span class="emoji-icon">
                        📸
                    </span>

                    <span class="label">
                        Screenshot
                    </span>
                </button>


                <button
                    class="key"
                    onclick="loadStats()"
                >
                    <span class="emoji-icon">
                        📊
                    </span>

                    <span class="label">
                        Refresh Stats
                    </span>
                </button>

            </div>


            <!-- LIVE STATS -->

            <div class="stats-grid">


                <div class="stat-card">

                    <div class="stat-head">
                        CPU
                    </div>

                    <div
                        id="cpuValue"
                        class="stat-value"
                    >
                        --
                    </div>

                    <div class="meter">
                        <span
                            id="cpuMeter"
                        ></span>
                    </div>

                </div>


                <div class="stat-card">

                    <div class="stat-head">
                        RAM
                    </div>

                    <div
                        id="ramValue"
                        class="stat-value"
                    >
                        --
                    </div>

                    <div
                        id="ramSub"
                        class="stat-sub"
                    >
                        --
                    </div>

                    <div class="meter">
                        <span
                            id="ramMeter"
                        ></span>
                    </div>

                </div>


                <div class="stat-card">

                    <div class="stat-head">
                        CPU TEMP
                    </div>

                    <div
                        id="tempValue"
                        class="stat-value"
                    >
                        --
                    </div>

                    <div class="stat-sub">
                        CPU temperature
                    </div>

                </div>


                <div class="stat-card">

                    <div class="stat-head">
                        DISK
                    </div>

                    <div
                        id="diskValue"
                        class="stat-value"
                    >
                        --
                    </div>

                    <div
                        id="diskSub"
                        class="stat-sub"
                    >
                        --
                    </div>

                    <div class="meter">
                        <span
                            id="diskMeter"
                        ></span>
                    </div>

                </div>


            </div>

        </div>

    </section>


    <!-- ========================================================
         AI VISION
         ======================================================== -->

    <section
        id="vision"
        class="page"
    >

        <div class="vision-shell">


            <div class="camera-panel">

                <div class="camera-placeholder">

                    <div class="camera-icon">
                        📷
                    </div>

                    <div class="camera-title">
                        AI VISION
                    </div>

                    <div class="camera-sub">
                        Camera pipeline coming next
                    </div>

                </div>

            </div>


            <div class="vision-controls">

                <button
                    class="vision-btn"
                    onclick="showToast('Camera setup coming next')"
                >
                    START CAMERA
                </button>

                <button
                    class="vision-btn"
                    onclick="showToast('AI detection coming next')"
                >
                    OBJECT DETECTION
                </button>

            </div>

        </div>

    </section>


</main>


<!-- TOAST -->

<div id="toast"></div>


<script>


    // ========================================================
    // RUN LAPTOP COMMAND
    // ========================================================

    async function runCommand(
        name,
        button
    ) {

        if (button) {

            button.classList.add(
                "pressed"
            );

            setTimeout(
                () => {
                    button.classList.remove(
                        "pressed"
                    );
                },
                140
            );
        }


        try {

            const response =
                await fetch(
                    "/run/" +
                    encodeURIComponent(name),
                    {
                        method: "GET",
                        cache: "no-store"
                    }
                );


            const data =
                await response.json();


            if (!data.ok) {

                showToast(
                    data.error ||
                    "Command failed"
                );

            } else {

                showToast(
                    name
                        .replaceAll("-", " ")
                        .toUpperCase()
                    + " EXECUTED"
                );

            }


        } catch (error) {

            console.error(error);

            showToast(
                "Laptop connection lost"
            );
        }
    }


    // ========================================================
    // PAGE SWITCHING
    // ========================================================

    function switchPage(
        pageName,
        button
    ) {

        document
            .querySelectorAll(".page")
            .forEach(
                page => {
                    page.classList.remove(
                        "active"
                    );
                }
            );


        document
            .querySelectorAll(".nav-btn")
            .forEach(
                navButton => {
                    navButton.classList.remove(
                        "active"
                    );
                }
            );


        const page =
            document.getElementById(
                pageName
            );


        if (page) {

            page.classList.add(
                "active"
            );
        }


        if (button) {

            button.classList.add(
                "active"
            );
        }


        if (pageName === "system") {

            loadStats();
        }
    }


    // ========================================================
    // SYSTEM STATS
    // ========================================================

    async function loadStats() {

        try {

            const response =
                await fetch(
                    "/api/system-stats",
                    {
                        cache: "no-store"
                    }
                );


            const stats =
                await response.json();


            if (!stats.ok) {

                showToast(
                    "Unable to load system stats"
                );

                return;
            }


            // CPU

            document
                .getElementById("cpuValue")
                .textContent =
                    stats.cpu.percent + "%";


            document
                .getElementById("cpuMeter")
                .style.width =
                    stats.cpu.percent + "%";


            // RAM

            document
                .getElementById("ramValue")
                .textContent =
                    stats.memory.percent + "%";


            document
                .getElementById("ramSub")
                .textContent =
                    stats.memory.used_gb +
                    " / " +
                    stats.memory.total_gb +
                    " GB";


            document
                .getElementById("ramMeter")
                .style.width =
                    stats.memory.percent + "%";


            // TEMP

            document
                .getElementById("tempValue")
                .textContent =
                    stats.temperature === null
                        ? "N/A"
                        : stats.temperature + "°C";


            // DISK

            document
                .getElementById("diskValue")
                .textContent =
                    stats.disk.percent + "%";


            document
                .getElementById("diskSub")
                .textContent =
                    stats.disk.free_gb +
                    " GB free";


            document
                .getElementById("diskMeter")
                .style.width =
                    stats.disk.percent + "%";


        } catch (error) {

            console.error(error);

            showToast(
                "Stats connection failed"
            );
        }
    }


    // ========================================================
    // FULLSCREEN
    // ========================================================

    async function goFullscreen() {

        try {

            if (
                !document.fullscreenElement
            ) {

                await document
                    .documentElement
                    .requestFullscreen();

                hideFullscreenButton();
            }

        } catch (error) {

            console.warn(
                "Fullscreen unavailable:",
                error
            );
        }
    }


    function hideFullscreenButton() {

        const button =
            document.getElementById(
                "fullscreenBtn"
            );

        if (button) {

            button.style.display =
                "none";
        }
    }


    function showFullscreenButton() {

        const button =
            document.getElementById(
                "fullscreenBtn"
            );

        if (button) {

            button.style.display =
                "block";
        }
    }


    document.addEventListener(
        "fullscreenchange",
        () => {

            if (
                document.fullscreenElement
            ) {

                hideFullscreenButton();

            } else {

                showFullscreenButton();
            }
        }
    );


    // ========================================================
    // TOAST
    // ========================================================

    let toastTimer = null;


    function showToast(
        message
    ) {

        const toast =
            document.getElementById(
                "toast"
            );


        toast.textContent =
            message;


        toast.style.opacity =
            "1";


        clearTimeout(
            toastTimer
        );


        toastTimer =
            setTimeout(
                () => {

                    toast.style.opacity =
                        "0";

                },
                1800
            );
    }


    // ========================================================
    // STARTUP
    // ========================================================

    window.addEventListener(
        "load",
        () => {

            console.log(
                "Shubham Deck V4 ready"
            );

        }
    );


</script>


</body>

</html>
"""


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    return render_template_string(HTML)


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Shubham Deck"
    })


@app.get("/api/system-stats")
def system_stats():

    try:

        cpu = read_cpu_usage()
        memory = read_memory()
        disk = read_disk()
        temperature = read_temperature()
        uptime = read_uptime()

        return jsonify({
            "ok": True,
            "cpu": {
                "percent": cpu
            },
            "memory": memory,
            "disk": disk,
            "temperature": temperature,
            "uptime": uptime
        })

    except Exception as exc:

        app.logger.exception(
            "Failed to read system stats"
        )

        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.get("/run/<name>")
def run_command(name):

    script = COMMANDS.get(name)

    if script is None:

        return jsonify({
            "ok": False,
            "error": "Unknown command"
        }), 404


    if not script.exists():

        return jsonify({
            "ok": False,
            "error":
                f"Script not found: {script}"
        }), 500


    if not script.is_file():

        return jsonify({
            "ok": False,
            "error":
                f"Not a file: {script}"
        }), 500


    try:

        subprocess.Popen(
            [str(script)],
            cwd=str(SCRIPTS_DIR),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return jsonify({
            "ok": True,
            "command": name
        })


    except Exception as exc:

        app.logger.exception(
            "Failed to execute command: %s",
            name
        )

        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
