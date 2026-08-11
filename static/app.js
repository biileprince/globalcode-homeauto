async function toggleDevice(deviceKey) {
    const card = document.getElementById(`card-${deviceKey}`);
    const checkbox = document.getElementById(`toggle-${deviceKey}`);
    const statusPill = document.getElementById(`status-${deviceKey}`);

    // Optimistic UI update — feels instant, corrected below if it fails
    const goingOn = !card.classList.contains("on");

    try {
        const response = await fetch(`/api/toggle/${deviceKey}`, { method: "POST" });
        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        applyState(deviceKey, data[deviceKey]);
        if (deviceKey === 'soundsystem') {
            refreshStatus();
        }
    } catch (err) {
        console.error("Failed to toggle device:", err);
        setConnection(false);
    }
}

function applyState(deviceKey, isOn) {
    const card = document.getElementById(`card-${deviceKey}`);
    const checkbox = document.getElementById(`toggle-${deviceKey}`);
    const statusPill = document.getElementById(`status-${deviceKey}`);

    if (!card) return;

    card.classList.toggle("on", isOn);
    card.classList.toggle("off", !isOn);
    if (checkbox) checkbox.checked = isOn;
    if (statusPill) statusPill.textContent = isOn ? "ON" : "OFF";
}

async function refreshStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();
        
        const alarmBanner = document.getElementById("alarm-banner");
        
        if (data.alarm_active) {
            document.body.classList.add("alarm-active");
            if (alarmBanner) {
                alarmBanner.classList.remove("hidden");
                alarmBanner.innerText = `🚨 ${data.alarm_reason}! CLICK TO DISMISS 🚨`;
            }
        } else {
            document.body.classList.remove("alarm-active");
            if (alarmBanner) alarmBanner.classList.add("hidden");
        }

        for (const [key, isOn] of Object.entries(data)) {
            if (key === "alarm_active" || key === "alarm_reason") continue;
            applyState(key, isOn);
        }
        setConnection(true);
    } catch (err) {
        console.error("Failed to refresh status:", err);
        setConnection(false);
    }
}

function setConnection(online) {
    const dot = document.getElementById("connection-dot");
    const text = document.getElementById("connection-text");
    if (!dot || !text) return;
    dot.classList.toggle("offline", !online);
    text.textContent = online ? "Connected to Raspberry Pi" : "Connection lost — retrying...";
}

// Keep the UI in sync in case a device is toggled from elsewhere
setInterval(refreshStatus, 5000);

async function dismissAlarm() {
    try {
        const response = await fetch("/api/dismiss_alarm", { method: "POST" });
        const data = await response.json();
        
        document.body.classList.remove("alarm-active");
        const alarmBanner = document.getElementById("alarm-banner");
        if (alarmBanner) alarmBanner.classList.add("hidden");
        
        for (const [key, isOn] of Object.entries(data)) {
            if (key === "alarm_active" || key === "alarm_reason") continue;
            applyState(key, isOn);
        }
    } catch (err) {
        console.error("Failed to dismiss alarm:", err);
    }
}
