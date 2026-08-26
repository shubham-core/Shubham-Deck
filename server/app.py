from flask import Flask, jsonify, render_template_string
from pathlib import Path
import subprocess

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path("/home/shubham/phone-deck")

COMMANDS = {
    "vscode": BASE_DIR / "vscode.sh",
    "brave": BASE_DIR / "brave.sh",
    "whatsapp": BASE_DIR / "whatsapp.sh",
    "github": BASE_DIR / "github.sh",
    "files": BASE_DIR / "files.sh",
    "terminal": BASE_DIR / "terminal.sh",
}

# ============================================================
# DASHBOARD HTML
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

    <meta name="theme-color" content="#080808">

    <link
        rel="manifest"
        href="/static/manifest.json"
    >

    <title>Shubham Deck</title>

    <style>

        /* =====================================================
           GLOBAL
           ===================================================== */

        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        html,
        body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;

            background: #080808;
            color: #ffffff;

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


        /* =====================================================
           FULLSCREEN BUTTON
           ===================================================== */

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

            width: 46px;
            height: 42px;

            border: 1px solid #333;
            border-radius: 12px;

            background: rgba(30, 30, 30, 0.92);
            color: #ffffff;

            font-size: 21px;
            font-weight: 700;

            display: flex;
            align-items: center;
            justify-content: center;

            cursor: pointer;

            box-shadow:
                0 5px 15px rgba(0, 0, 0, 0.45);

            backdrop-filter: blur(8px);

            transition:
                transform 0.10s ease,
                background 0.10s ease;
        }

        #fullscreenBtn:active {
            transform: scale(0.88);
            background: #303030;
        }


        /* =====================================================
           MAIN DECK
           ===================================================== */

        .deck {
            width: 100%;
            height: 100%;

            max-width: 1000px;
            max-height: 1000px;

            padding:
                max(14px, env(safe-area-inset-top))
                max(14px, env(safe-area-inset-right))
                max(14px, env(safe-area-inset-bottom))
                max(14px, env(safe-area-inset-left));

            display: flex;
            flex-direction: column;
        }


        /* =====================================================
           HEADER
           ===================================================== */

        .topbar {
            min-height: 48px;

            display: flex;
            align-items: center;
            justify-content: space-between;

            margin-bottom: 12px;
        }

        .title {
            font-size: clamp(20px, 4vw, 30px);

            font-weight: 850;

            letter-spacing: 1px;

            user-select: none;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 7px;

            padding:
                7px
                10px;

            border-radius: 999px;

            background: #151515;
            border: 1px solid #252525;

            color: #9a9a9a;

            font-size: 11px;
            font-weight: 700;

            white-space: nowrap;

            user-select: none;
        }

        .status-dot {
            width: 8px;
            height: 8px;

            border-radius: 50%;

            background: #35df86;

            box-shadow:
                0 0 9px rgba(53, 223, 134, 0.8);
        }


        /* =====================================================
           BUTTON GRID
           ===================================================== */

        .grid {
            flex: 1;

            min-height: 0;

            display: grid;

            grid-template-columns:
                repeat(3, minmax(0, 1fr));

            gap: 12px;
        }


        /* =====================================================
           STREAM DECK BUTTON
           ===================================================== */

        .key {
            position: relative;

            min-width: 0;
            min-height: 0;

            border:
                1px solid #292929;

            border-radius: 21px;

            background:
                radial-gradient(
                    circle at 50% 5%,
                    rgba(255, 255, 255, 0.075),
                    transparent 43%
                ),
                linear-gradient(
                    145deg,
                    #181818,
                    #111111
                );

            color: #ffffff;

            display: flex;
            flex-direction: column;

            align-items: center;
            justify-content: center;

            gap: 10px;

            padding: 10px;

            cursor: pointer;

            user-select: none;

            box-shadow:
                inset 0 1px 0
                    rgba(255, 255, 255, 0.035),

                0 8px 20px
                    rgba(0, 0, 0, 0.28);

            transition:
                transform 0.09s ease,
                background 0.09s ease,
                border-color 0.09s ease,
                box-shadow 0.09s ease;
        }

        .key:hover {
            border-color: #414141;
        }

        .key:active,
        .key.pressed {
            transform: scale(0.94);

            border-color: #606060;

            background:
                radial-gradient(
                    circle at 50% 30%,
                    rgba(255, 255, 255, 0.13),
                    transparent 52%
                ),
                #202020;

            box-shadow:
                inset 0 0 20px
                    rgba(255, 255, 255, 0.045),

                0 3px 8px
                    rgba(0, 0, 0, 0.35);
        }


        /* =====================================================
           ICONS
           ===================================================== */

        .icon {
            width: clamp(50px, 10vw, 88px);
            height: clamp(50px, 10vw, 88px);

            object-fit: contain;

            user-select: none;
            pointer-events: none;

            filter:
                drop-shadow(
                    0 4px 8px
                    rgba(0, 0, 0, 0.4)
                );
        }


        /* =====================================================
           BUTTON LABEL
           ===================================================== */

        .label {
            font-size:
                clamp(12px, 2.25vw, 17px);

            line-height: 1.1;

            font-weight: 750;

            letter-spacing: 0.2px;

            text-align: center;

            user-select: none;
            pointer-events: none;
        }


        /* =====================================================
           FOOTER
           ===================================================== */

        .footer {
            min-height: 25px;

            display: flex;
            align-items: flex-end;
            justify-content: center;

            color: #4e4e4e;

            font-size: 10px;
            font-weight: 600;

            letter-spacing: 0.5px;

            user-select: none;
        }


        /* =====================================================
           SMALL PHONES
           ===================================================== */

        @media (max-width: 600px) {

            .deck {
                padding:
                    max(10px, env(safe-area-inset-top))
                    max(10px, env(safe-area-inset-right))
                    max(10px, env(safe-area-inset-bottom))
                    max(10px, env(safe-area-inset-left));
            }

            .grid {
                gap: 9px;
            }

            .key {
                border-radius: 17px;
            }

            .label {
                font-size: 13px;
            }
        }


        /* =====================================================
           VERY SMALL PHONES
           ===================================================== */

        @media (max-width: 380px) {

            .grid {
                gap: 7px;
            }

            .key {
                border-radius: 14px;
            }

            .icon {
                width: 45px;
                height: 45px;
            }

            .label {
                font-size: 11px;
            }
        }


        /* =====================================================
           LANDSCAPE
           ===================================================== */

        @media (orientation: landscape) {

            .deck {
                max-width: 1150px;
            }

            .grid {
                grid-template-columns:
                    repeat(3, minmax(0, 1fr));
            }

            .icon {
                width: clamp(48px, 9vh, 78px);
                height: clamp(48px, 9vh, 78px);
            }
        }

    </style>
</head>


<body>


    <!-- =======================================================
         FULLSCREEN BUTTON
         ======================================================= -->

    <button
        id="fullscreenBtn"
        onclick="goFullscreen()"
        aria-label="Enter fullscreen"
        title="Fullscreen"
    >
        ⛶
    </button>


    <!-- =======================================================
         MAIN DECK
         ======================================================= -->

    <main class="deck">


        <!-- ===================================================
             HEADER
             =================================================== -->

        <header class="topbar">

            <div class="title">
                MY DECK
            </div>

            <div class="status">

                <span class="status-dot"></span>

                LAPTOP ONLINE

            </div>

        </header>


        <!-- ===================================================
             BUTTON GRID
             =================================================== -->

        <section class="grid">


            <!-- VS CODE -->

            <button
                class="key"
                type="button"
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


            <!-- BRAVE -->

            <button
                class="key"
                type="button"
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


            <!-- WHATSAPP -->

            <button
                class="key"
                type="button"
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


            <!-- GITHUB -->

            <button
                class="key"
                type="button"
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


            <!-- FILES -->

            <button
                class="key"
                type="button"
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


            <!-- TERMINAL -->

            <button
                class="key"
                type="button"
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


        </section>


        <!-- ===================================================
             FOOTER
             =================================================== -->

        <footer class="footer">
            SHUBHAM DECK • V2
        </footer>


    </main>


    <!-- =======================================================
         JAVASCRIPT
         ======================================================= -->

    <script>


        // ======================================================
        // RUN LAPTOP COMMAND
        // ======================================================

        async function runCommand(name, button) {

            // Visual press effect
            button.classList.add("pressed");

            window.setTimeout(() => {
                button.classList.remove("pressed");
            }, 140);


            try {

                const response =
                    await fetch(
                        "/run/" + encodeURIComponent(name),
                        {
                            method: "GET",
                            cache: "no-store"
                        }
                    );


                const data =
                    await response.json();


                if (!data.ok) {

                    console.error(
                        "Command failed:",
                        data.error
                    );

                    showToast(
                        data.error ||
                        "Command failed"
                    );
                }


            } catch (error) {

                console.error(
                    "Connection error:",
                    error
                );

                showToast(
                    "Laptop connection lost"
                );
            }
        }


        // ======================================================
        // FULLSCREEN
        // ======================================================

        async function goFullscreen() {

            try {

                if (!document.fullscreenElement) {

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


        // ======================================================
        // FULLSCREEN STATE
        // ======================================================

        function hideFullscreenButton() {

            const button =
                document.getElementById(
                    "fullscreenBtn"
                );

            if (button) {
                button.style.display = "none";
            }
        }


        function showFullscreenButton() {

            const button =
                document.getElementById(
                    "fullscreenBtn"
                );

            if (button) {
                button.style.display = "flex";
            }
        }


        document.addEventListener(
            "fullscreenchange",
            () => {

                if (document.fullscreenElement) {

                    hideFullscreenButton();

                } else {

                    showFullscreenButton();

                }

            }
        );


        // ======================================================
        // SMALL TOAST MESSAGE
        // ======================================================

        function showToast(message) {

            let toast =
                document.getElementById(
                    "deckToast"
                );


            if (!toast) {

                toast =
                    document.createElement(
                        "div"
                    );

                toast.id = "deckToast";

                toast.style.position =
                    "fixed";

                toast.style.left = "50%";

                toast.style.bottom = "28px";

                toast.style.transform =
                    "translateX(-50%)";

                toast.style.zIndex = "10000";

                toast.style.padding =
                    "10px 15px";

                toast.style.borderRadius =
                    "12px";

                toast.style.background =
                    "rgba(30,30,30,.94)";

                toast.style.border =
                    "1px solid #3a3a3a";

                toast.style.color =
                    "#ffffff";

                toast.style.fontSize =
                    "13px";

                toast.style.fontWeight =
                    "700";

                toast.style.boxShadow =
                    "0 8px 25px rgba(0,0,0,.4)";

                toast.style.pointerEvents =
                    "none";

                document.body.appendChild(
                    toast
                );
            }


            toast.textContent = message;

            toast.style.opacity = "1";


            window.clearTimeout(
                toast._timer
            );


            toast._timer =
                window.setTimeout(
                    () => {

                        toast.style.opacity =
                            "0";

                    },
                    2200
                );
        }


        // ======================================================
        // PREVENT DOUBLE-TAP ZOOM
        // ======================================================

        let lastTouchEnd = 0;

        document.addEventListener(
            "touchend",
            (event) => {

                const now =
                    Date.now();

                if (
                    now - lastTouchEnd <= 300
                ) {

                    event.preventDefault();

                }

                lastTouchEnd = now;

            },
            {
                passive: false
            }
        );


        // ======================================================
        // PAGE READY
        // ======================================================

        window.addEventListener(
            "load",
            () => {

                console.log(
                    "Shubham Deck ready"
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
    """Return the Stream Deck dashboard."""
    return render_template_string(HTML)


@app.get("/health")
def health():
    """Simple connection test."""
    return jsonify({
        "ok": True,
        "service": "Shubham Deck"
    })


@app.get("/run/<name>")
def run_command(name):
    """Safely execute one of the predefined launcher scripts."""

    script = COMMANDS.get(name)

    # Unknown command
    if script is None:
        return jsonify({
            "ok": False,
            "error": "Unknown command"
        }), 404

    # Missing script
    if not script.exists():
        return jsonify({
            "ok": False,
            "error": f"Launcher not found: {script}"
        }), 500

    # Not executable
    if not script.is_file():
        return jsonify({
            "ok": False,
            "error": f"Launcher is not a file: {script}"
        }), 500

    try:

        subprocess.Popen(
            [str(script)],
            cwd=str(BASE_DIR),
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
            "Failed to launch %s",
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
