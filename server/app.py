import os
import time
import subprocess
import cv2
import psutil
from flask import Flask, Response, jsonify, render_template_string, request

app = Flask(__name__, static_folder='static')

# Update with your phone's IP Camera URL
CAMERA_URL = "http://10.124.165.12:8080/video"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Deck OS Command Center</title>
    <!-- Your existing Lumi styles (will load if directory exists) -->
    <link rel="stylesheet" href="/static/css/lumi.css">
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --bg: #020617;
            --surface: rgba(15, 23, 42, 0.65);
            --border: rgba(56, 189, 248, 0.2);
            --accent: #38bdf8;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --glow: 0 0 25px rgba(56, 189, 248, 0.15);
            --font-ui: 'Segoe UI', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(2, 132, 199, 0.15), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(56, 189, 248, 0.1), transparent 25%);
            color: var(--text);
            font-family: var(--font-ui);
            min-height: 100vh;
            padding: 20px;
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 20px;
            overflow-x: hidden;
        }

        @media (max-width: 1024px) {
            body { grid-template-columns: 1fr; padding: 12px; gap: 16px; }
        }

        /* Glass & Containers */
        .glass-panel {
            background: var(--surface);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--glow);
            padding: 24px;
        }

        /* Sidebar Elements */
        .sidebar { display: flex; flex-direction: column; gap: 32px; }

        .brand {
            display: flex; align-items: center; gap: 16px;
            font-size: 1.4rem; font-weight: 800; letter-spacing: 2px;
        }

        .badge {
            background: rgba(56, 189, 248, 0.2); color: var(--accent);
            padding: 2px 8px; border-radius: 8px; font-size: 0.7rem; font-weight: bold;
        }

        .lumi-avatar-wrapper {
            width: 48px; height: 48px; background: rgba(0,0,0,0.3);
            border-radius: 50%; border: 1px solid var(--border);
            display: flex; align-items: center; justify-content: center; overflow: hidden;
        }
        .lumi-avatar-wrapper img { width: 100%; height: 100%; object-fit: contain; }

        /* Stats */
        .stats-container { display: flex; flex-direction: column; gap: 20px; }
        .stat-group { display: flex; flex-direction: column; gap: 8px; }
        .stat-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; font-weight: 600; letter-spacing: 1px;}
        .stat-value { color: var(--accent); font-family: var(--font-mono); }
        .text-muted { color: var(--text-muted); display: flex; align-items: center; gap: 6px; }

        .stat-bar-bg {
            width: 100%; height: 6px; background: rgba(255,255,255,0.05);
            border-radius: 4px; overflow: hidden;
        }
        .stat-bar-fill {
            height: 100%; background: var(--accent); border-radius: 4px;
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 10px var(--accent);
        }
        .text-muted-bg { background: var(--text-muted); box-shadow: none; }

        /* Status Indicator */
        .system-status { display: flex; flex-direction: column; gap: 12px; margin-top: auto; }
        .status-indicator {
            display: flex; align-items: center; gap: 10px;
            font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;
            padding: 12px 16px; border-radius: 12px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05);
        }
        .status-indicator.online { color: #10b981; }
        .status-indicator.offline { color: var(--danger); }
        .status-indicator .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }

        /* Main Content & Camera */
        .main-content { display: flex; flex-direction: column; gap: 20px; }

        .cam-wrapper {
            position: relative; width: 100%; aspect-ratio: 16/9;
            border-radius: 24px; overflow: hidden; padding: 0; background: #000; border: 1px solid var(--border);
        }
        #camera-feed { width: 100%; height: 100%; object-fit: cover; transition: opacity 0.3s; }

        .camera-offline-state {
            position: absolute; inset: 0; display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            background: #000; color: var(--danger); font-family: var(--font-mono);
            letter-spacing: 2px; text-align: center; z-index: 5;
        }
        .hidden { display: none !important; }

        /* HUD */
        .hud {
            position: absolute; inset: 0; pointer-events: none;
            box-shadow: inset 0 0 80px rgba(0,0,0,0.8);
            padding: 24px; display: flex; flex-direction: column; justify-content: space-between; z-index: 10;
        }
        .hud-top, .hud-bottom { display: flex; justify-content: space-between; align-items: flex-end; }
        .hud-mono { font-family: var(--font-mono); color: rgba(255,255,255,0.7); font-size: 0.85rem; text-shadow: 0 2px 4px #000; }

        .rec-indicator { display: flex; align-items: center; gap: 8px; color: #ef4444; font-family: var(--font-mono); font-weight: bold; font-size: 0.9rem; letter-spacing: 1px; text-shadow: 0 2px 4px #000;}
        .rec-dot { width: 12px; height: 12px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 10px #ef4444; animation: pulse 2s infinite; }
        @keyframes pulse { 0% {opacity:1;} 50% {opacity:0.3;} 100% {opacity:1;} }

        .crosshair {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 60px; height: 60px; border: 1px solid rgba(255,255,255,0.2); border-radius: 50%;
        }
        .crosshair::before, .crosshair::after { content: ''; position: absolute; background: rgba(255,255,255,0.4); }
        .crosshair::before { top: -20px; bottom: -20px; left: 29px; width: 1px; }
        .crosshair::after { left: -20px; right: -20px; top: 29px; height: 1px; }

        /* Buttons & Grid */
        .section-title { font-size: 0.85rem; color: var(--text-muted); letter-spacing: 2px; margin-bottom: 16px; }
        .btn-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px; }
        
        .btn {
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 16px; border-radius: 16px; color: var(--text); font-size: 0.9rem; font-weight: 600;
            cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
        }

        .btn:hover {
            background: rgba(56, 189, 248, 0.1); border-color: var(--accent);
            transform: translateY(-2px); box-shadow: 0 8px 20px rgba(56, 189, 248, 0.15);
        }
        .btn:active { transform: translateY(1px); }
        .btn i { color: var(--accent); transition: transform 0.2s; }
        .btn:hover i { transform: scale(1.1); }

        .btn-danger { border-color: rgba(239, 68, 68, 0.3); }
        .btn-danger:hover { background: rgba(239, 68, 68, 0.15); border-color: var(--danger); box-shadow: 0 8px 20px rgba(239, 68, 68, 0.15); }
        .btn-danger i { color: var(--danger); }
        
        .btn-secondary { background: transparent; border-color: var(--text-muted); color: var(--text-muted); padding: 12px; }
        .btn-secondary:hover { background: rgba(255,255,255,0.05); border-color: var(--text); color: var(--text); box-shadow: none;}

        /* Toasts & Modals */
        #toast-container { position: fixed; bottom: 24px; right: 24px; display: flex; flex-direction: column; gap: 12px; z-index: 1000; }
        .toast {
            background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px); border-left: 4px solid var(--accent);
            padding: 16px 24px; border-radius: 8px; color: #fff; font-weight: 500; font-size: 0.9rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); transform: translateX(120%); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex; align-items: center; gap: 12px;
        }
        .toast.show { transform: translateX(0); }
        .toast.error { border-color: var(--danger); }

        .modal-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(5px);
            display: flex; align-items: center; justify-content: center; z-index: 2000;
            opacity: 0; pointer-events: none; transition: opacity 0.2s;
        }
        .modal-overlay.active { opacity: 1; pointer-events: auto; }
        .modal-box { width: 90%; max-width: 400px; text-align: center; display: flex; flex-direction: column; gap: 16px; align-items: center; transform: translateY(20px); transition: transform 0.3s; }
        .modal-overlay.active .modal-box { transform: translateY(0); }
        .modal-actions { display: flex; gap: 16px; width: 100%; margin-top: 8px; }
        .modal-actions .btn { flex: 1; padding: 12px; flex-direction: row; }

        /* Utilities */
        .icon-sm { width: 16px; height: 16px; }
        .mt-4 { margin-top: 24px; }
        .mt-3 { margin-top: 16px; }
        .mt-auto { margin-top: auto; }
    </style>
</head>
<body>
    <div id="toast-container"></div>

    <!-- Confirmation Modal -->
    <div id="modal-overlay" class="modal-overlay">
        <div class="modal-box glass-panel">
            <i data-lucide="alert-triangle" style="color: var(--danger); width: 48px; height: 48px;"></i>
            <h2 id="modal-title">Confirm Action</h2>
            <p id="modal-message">Are you sure you want to proceed?</p>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-danger" id="modal-confirm-btn">Execute</button>
            </div>
        </div>
    </div>

    <aside class="sidebar glass-panel">
        <div class="brand">
            <div id="lumi-container" class="lumi-avatar-wrapper">
                <img id="lumi-avatar" src="/static/lumi/lumi-idle.svg" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%2338bdf8\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'><rect x=\'2\' y=\'2\' width=\'20\' height=\'8\' rx=\'2\' ry=\'2\'/><rect x=\'2\' y=\'14\' width=\'20\' height=\'8\' rx=\'2\' ry=\'2\'/><line x1=\'6\' y1=\'6\' x2=\'6.01\' y2=\'6\'/><line x1=\'6\' y1=\'18\' x2=\'6.01\' y2=\'18\'/></svg>'">
            </div>
            <span>DECK OS <span class="badge">PRO</span></span>
        </div>
        
        <div class="stats-container">
            <div class="stat-group">
                <div class="stat-row">
                    <span class="text-muted"><i data-lucide="cpu" class="icon-sm"></i> CPU LOAD</span>
                    <span id="cpu-val" class="stat-value">0%</span>
                </div>
                <div class="stat-bar-bg"><div id="cpu-bar" class="stat-bar-fill"></div></div>
            </div>

            <div class="stat-group">
                <div class="stat-row">
                    <span class="text-muted"><i data-lucide="memory-stick" class="icon-sm"></i> MEMORY</span>
                    <span id="ram-val" class="stat-value">0%</span>
                </div>
                <div class="stat-bar-bg"><div id="ram-bar" class="stat-bar-fill"></div></div>
            </div>

            <div class="stat-group">
                <div class="stat-row">
                    <span class="text-muted"><i data-lucide="hard-drive" class="icon-sm"></i> STORAGE</span>
                    <span id="disk-val" class="stat-value">0%</span>
                </div>
                <div class="stat-bar-bg"><div id="disk-bar" class="stat-bar-fill text-muted-bg"></div></div>
            </div>
        </div>
        
        <div class="system-status">
            <div class="status-indicator online" id="conn-status">
                <div class="dot"></div>
                <span id="conn-text">SYSTEM ONLINE</span>
            </div>
            <div class="stat-row mt-auto">
                <span class="text-muted">UPTIME</span>
                <span id="uptime-val" class="stat-value">0h 0m</span>
            </div>
        </div>
    </aside>

    <main class="main-content">
        <section class="cam-section">
            <div class="cam-wrapper glass-panel" style="padding: 0; box-shadow: none;">
                <div class="hud">
                    <div class="hud-top">
                        <div class="rec-indicator"><div class="rec-dot"></div> <span id="cam-status">LINK ACTIVE</span></div>
                        <div class="hud-mono">OPTICAL.FEED // 10.124.165.12</div>
                    </div>
                    <div class="crosshair"></div>
                    <div class="hud-bottom">
                        <div id="hud-time" class="hud-mono">00:00:00.000</div>
                        <div class="hud-mono">SYS.V5 <i data-lucide="wifi" class="icon-sm" style="margin-left: 8px;"></i></div>
                    </div>
                </div>
                <img id="camera-feed" src="/video_feed" alt="Camera Feed">
                
                <!-- Fallback when camera is offline -->
                <div id="camera-offline" class="camera-offline-state hidden">
                    <i data-lucide="camera-off" style="width: 48px; height: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
                    <div>OPTICAL LINK SEVERED</div>
                    <button class="btn btn-secondary mt-3" onclick="reconnectCamera()" style="font-size: 0.8rem; padding: 8px 16px; flex-direction: row; width: auto;">
                        <i data-lucide="refresh-cw"></i> REINITIALIZE
                    </button>
                </div>
            </div>
        </section>

        <section class="controls-section glass-panel">
            <h3 class="section-title">QUICK ACTIONS</h3>
            <div class="btn-grid">
                <button class="btn action-btn" data-action="terminal"><i data-lucide="terminal"></i> Terminal</button>
                <button class="btn action-btn" data-action="vscode"><i data-lucide="code"></i> VS Code</button>
                <button class="btn action-btn" data-action="screenshot"><i data-lucide="camera"></i> Capture</button>
                <button class="btn action-btn" data-action="vol_up"><i data-lucide="volume-2"></i> Vol +</button>
                <button class="btn action-btn" data-action="vol_down"><i data-lucide="volume-1"></i> Vol -</button>
                <button class="btn action-btn" data-action="lock"><i data-lucide="lock"></i> Lock PC</button>
            </div>
            
            <h3 class="section-title mt-4" style="color: var(--danger);">SYSTEM POWER</h3>
            <div class="btn-grid" style="grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));">
                <button class="btn btn-danger action-btn" data-action="reboot" data-confirm="true"><i data-lucide="refresh-cw"></i> Reboot</button>
                <button class="btn btn-danger action-btn" data-action="shutdown" data-confirm="true"><i data-lucide="power"></i> Shutdown</button>
            </div>
        </section>
    </main>

    <!-- Your existing Lumi JS (will load if exists) -->
    <script src="/static/js/lumi.js"></script>
    <script>
        // Initialize Icons
        lucide.createIcons();

        // --- STATE ---
        let isOffline = false;
        let actionToConfirm = null;

        // --- DOM ELEMENTS ---
        const toastContainer = document.getElementById('toast-container');
        const modalOverlay = document.getElementById('modal-overlay');
        const camFeed = document.getElementById('camera-feed');
        const camOffline = document.getElementById('camera-offline');

        // --- NOTIFICATIONS ---
        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const icon = type === 'success' ? '<i data-lucide="check-circle"></i>' : '<i data-lucide="alert-triangle"></i>';
            toast.innerHTML = `${icon} <span>${message}</span>`;
            
            toastContainer.appendChild(toast);
            lucide.createIcons({ root: toast });
            
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        // --- ACTION HANDLING ---
        async function triggerAction(action) {
            try {
                const res = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action})
                });
                
                const data = await res.json();
                if (data.status === 'success') {
                    showToast(`Executed: ${action.replace('_', ' ').toUpperCase()}`);
                } else {
                    showToast(`Failed: ${data.message}`, 'error');
                }
            } catch(e) { 
                showToast('Connection to host lost', 'error');
                console.error(e); 
            }
        }

        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.getAttribute('data-action');
                const requiresConfirm = btn.getAttribute('data-confirm');
                
                if (requiresConfirm === 'true') {
                    openModal(action);
                } else {
                    triggerAction(action);
                }
            });
        });

        // --- MODAL LOGIC ---
        function openModal(action) {
            actionToConfirm = action;
            document.getElementById('modal-message').innerText = `Are you sure you want to ${action.toUpperCase()} the system?`;
            modalOverlay.classList.add('active');
        }

        function closeModal() {
            actionToConfirm = null;
            modalOverlay.classList.remove('active');
        }

        document.getElementById('modal-confirm-btn').addEventListener('click', () => {
            if (actionToConfirm) triggerAction(actionToConfirm);
            closeModal();
        });

        // --- SYSTEM POLLING ---
        function updateConnectionStatus(online) {
            const statusEl = document.getElementById('conn-status');
            const textEl = document.getElementById('conn-text');
            
            if (online && isOffline) {
                statusEl.className = 'status-indicator online';
                textEl.innerText = 'SYSTEM ONLINE';
                isOffline = false;
            } else if (!online && !isOffline) {
                statusEl.className = 'status-indicator offline';
                textEl.innerText = 'CONNECTION LOST';
                isOffline = true;
            }
        }

        async function updateStats() {
            try {
                const res = await fetch('/api/system-stats', { signal: AbortSignal.timeout(2000) });
                if (!res.ok) throw new Error('Network error');
                
                const data = await res.json();
                
                document.getElementById('cpu-val').innerText = `${data.cpu}%`;
                document.getElementById('cpu-bar').style.width = `${data.cpu}%`;
                
                document.getElementById('ram-val').innerText = `${data.ram}%`;
                document.getElementById('ram-bar').style.width = `${data.ram}%`;
                
                document.getElementById('disk-val').innerText = `${data.disk}%`;
                document.getElementById('disk-bar').style.width = `${data.disk}%`;
                
                document.getElementById('uptime-val').innerText = data.uptime;
                
                updateConnectionStatus(true);
            } catch(e) {
                updateConnectionStatus(false);
            }
        }

        // --- CAMERA FALLBACK ---
        camFeed.addEventListener('error', () => {
            camFeed.classList.add('hidden');
            camOffline.classList.remove('hidden');
            document.getElementById('cam-status').innerText = 'LINK SEVERED';
            document.getElementById('cam-status').style.color = 'var(--text-muted)';
            document.querySelector('.rec-dot').style.display = 'none';
        });

        function reconnectCamera() {
            camFeed.src = ''; 
            setTimeout(() => {
                camFeed.src = '/video_feed?' + new Date().getTime(); // Bust cache
                camOffline.classList.add('hidden');
                camFeed.classList.remove('hidden');
                
                document.getElementById('cam-status').innerText = 'LINK ACTIVE';
                document.getElementById('cam-status').style.color = '#ef4444';
                document.querySelector('.rec-dot').style.display = 'block';
            }, 500);
        }

        // --- TIMERS ---
        setInterval(updateStats, 2000);
        updateStats();

        setInterval(() => {
            const now = new Date();
            document.getElementById('hud-time').innerText = 
                now.toLocaleTimeString('en-US', { hour12: false }) + '.' + 
                now.getMilliseconds().toString().padStart(3, '0');
        }, 47);
    </script>
</body>
</html>
"""

def generate_frames():
    """Generates camera frames with proper resource cleanup."""
    cap = cv2.VideoCapture(CAMERA_URL)
    # Reduce buffer size to minimize latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                time.sleep(0.5) # Wait before retrying if stream drops
                continue
                
            # Compress for faster network transmission
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if not ret: 
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        # CRITICAL: Release the camera if the client disconnects to prevent memory leaks
        cap.release()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system-stats')
def system_stats():
    uptime_sec = time.time() - psutil.boot_time()
    h = int(uptime_sec // 3600)
    m = int((uptime_sec % 3600) // 60)
    
    try:
        disk = psutil.disk_usage('/').percent
    except:
        disk = 0

    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.1), 
        "ram": psutil.virtual_memory().percent,
        "disk": disk,
        "uptime": f"{h}h {m}m"
    })

@app.route('/api/action', methods=['POST'])
def handle_action():
    data = request.get_json() or {}
    action = data.get('action')
    
    # Whitelisted actions
    actions = {
        'terminal': ['gnome-terminal'],
        'vscode': ['code'],
        'screenshot': ['gnome-screenshot'],
        'vol_up': ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+5%'],
        'vol_down': ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%'],
        'lock': ['loginctl', 'lock-session'],
        'reboot': ['systemctl', 'reboot'],
        'shutdown': ['systemctl', 'poweroff']
    }
    
    if action in actions:
        try:
            subprocess.Popen(actions[action], env=os.environ.copy())
            return jsonify({"status": "success", "action": action})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "unknown_action"}), 400

if __name__ == '__main__':
    # Threaded=True prevents the camera stream from blocking API requests
    app.run(host='0.0.0.0', port=5000, threaded=True)
