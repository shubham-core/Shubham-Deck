document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("lumi-container");
    const avatar = document.getElementById("lumi-avatar");
    if (!container || !avatar) return;

    const STATE_IDLE = "/static/lumi/lumi-idle.svg";
    const STATE_STRESS = "/static/lumi/lumi-stress.svg";
    const STATE_ACTION = "/static/lumi/lumi-action.svg";

    async function updateLumiState() {
        if (container.classList.contains("action")) return;
        try {
            const res = await fetch("/api/system-stats");
            const data = await res.json();
            const cpu = Number(data.cpu) || 0;
            const ram = data.ram ? (Number(data.ram.percent) || 0) : 0;

            if (cpu > 80 || ram > 80) {
                avatar.src = STATE_STRESS;
                container.className = "stress";
            } else {
                avatar.src = STATE_IDLE;
                container.className = "";
            }
        } catch (err) {
            console.warn("Lumi poll warning:", err);
        }
    }

    setInterval(updateLumiState, 2500);

    document.querySelectorAll("button, .btn, .card, a").forEach(elem => {
        elem.addEventListener("click", () => {
            avatar.src = STATE_ACTION;
            container.className = "action";
            setTimeout(() => {
                updateLumiState();
            }, 800);
        });
    });
});
