#!/bin/bash
# ============================================================
# MediMitra — Master Startup Script
# Starts all services for the MediMitra medicine reminder system:
#   1. Waits for network connectivity
#   2. Connects Bluetooth speakers
#   3. Starts Next.js frontend (port 3000)
#   4. Starts FastAPI backend (port 8000)
#   5. Starts Medicine Scheduler
#   6. Monitors all processes and restarts on crash
# ============================================================

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERFACE_DIR="$SCRIPT_DIR/interface"
MODEL_DIR="$SCRIPT_DIR/model"
VENV_DIR="$MODEL_DIR/venv"
LOG_FILE="$HOME/medimitra.log"
PID_DIR="$HOME/.medimitra"

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ── Logging ───────────────────────────────────────────────────
log() {
    local level="$1"
    local color="$2"
    local msg="$3"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    # Write plain text to log file
    echo "${ts} [${level}] ${msg}" >> "$LOG_FILE"
    # Write colored text to stdout (goes to journald or terminal)
    echo -e "${CYAN}${ts}${NC} ${color}[${level}]${NC} ${msg}"
}

log_info()  { log "INFO"  "$GREEN"  "$1"; }
log_warn()  { log "WARN"  "$YELLOW" "$1"; }
log_error() { log "ERROR" "$RED"    "$1"; }
log_start() { log "START" "$MAGENTA" "$1"; }

# ── PID Management ────────────────────────────────────────────
mkdir -p "$PID_DIR"

save_pid() {
    echo "$2" > "$PID_DIR/$1.pid"
}

get_pid() {
    local pidfile="$PID_DIR/$1.pid"
    if [ -f "$pidfile" ]; then
        cat "$pidfile"
    fi
}

is_running() {
    local pid
    pid=$(get_pid "$1")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

# ── Child PIDs for cleanup ────────────────────────────────────
NEXTJS_PID=""
FASTAPI_PID=""
SCHEDULER_PID=""
BT_MONITOR_PID=""

cleanup() {
    log_warn "🛑 Shutting down MediMitra..."

    for name_pid in "Next.js:$NEXTJS_PID" "FastAPI:$FASTAPI_PID" "Scheduler:$SCHEDULER_PID" "BT-Monitor:$BT_MONITOR_PID"; do
        local name="${name_pid%%:*}"
        local pid="${name_pid##*:}"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_info "Stopping $name (PID $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            # Wait up to 5 seconds for graceful shutdown
            for i in $(seq 1 5); do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # Force kill if still alive
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
    done

    # Clean PID files
    rm -f "$PID_DIR"/*.pid

    log_info "👋 MediMitra stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT SIGHUP EXIT

# ── Banner ────────────────────────────────────────────────────
{
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     🏥  MediMitra Startup System  🏥     ║"
echo "  ║   Family Medicine Reminder on Rasp Pi    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
} >> "$LOG_FILE"

echo -e "${BOLD}${MAGENTA}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     🏥  MediMitra Startup System  🏥     ║"
echo "  ║   Family Medicine Reminder on Rasp Pi    ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Wait for Network ─────────────────────────────────
log_start "Step 1/5: Waiting for network connectivity..."

MAX_NET_WAIT=60
waited=0
while ! ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; do
    waited=$((waited + 3))
    if [ $waited -ge $MAX_NET_WAIT ]; then
        log_error "❌ Network not available after ${MAX_NET_WAIT}s — continuing anyway (MongoDB/TTS may fail)"
        break
    fi
    log_warn "⏳ No network yet... (${waited}s / ${MAX_NET_WAIT}s)"
    sleep 3
done

if [ $waited -lt $MAX_NET_WAIT ]; then
    log_info "✅ Network is up"
fi

# ── Step 2: Wait for PipeWire/Audio ──────────────────────────
log_start "Step 2/5: Checking audio subsystem..."

MAX_AUDIO_WAIT=30
waited=0
while ! pactl info > /dev/null 2>&1; do
    waited=$((waited + 2))
    if [ $waited -ge $MAX_AUDIO_WAIT ]; then
        log_error "❌ PipeWire/PulseAudio not ready after ${MAX_AUDIO_WAIT}s"
        break
    fi
    sleep 2
done

if pactl info > /dev/null 2>&1; then
    log_info "✅ Audio subsystem ready (PipeWire)"
fi

# ── Step 3: Connect Bluetooth Speakers ───────────────────────
log_start "Step 3/5: Starting Bluetooth speaker manager..."

# Start the persistent BT monitor in background (handles initial connect + reconnects)
# No blocking one-shot — speakers connect async while web services start
"$SCRIPT_DIR/bt_connect.sh" >> "$LOG_FILE" 2>&1 &
BT_MONITOR_PID=$!
save_pid "bt_monitor" "$BT_MONITOR_PID"
log_info "🔊 Bluetooth monitor started in background (PID $BT_MONITOR_PID)"

# ── Step 4: Start Next.js Frontend ──────────────────────────
log_start "Step 4/5: Starting Next.js frontend..."

if [ ! -d "$INTERFACE_DIR/node_modules" ]; then
    log_warn "📦 node_modules not found, running npm install..."
    (cd "$INTERFACE_DIR" && npm install) >> "$LOG_FILE" 2>&1
fi

(cd "$INTERFACE_DIR" && npm run dev) >> "$LOG_FILE" 2>&1 &
NEXTJS_PID=$!
save_pid "nextjs" "$NEXTJS_PID"
log_info "🌐 Next.js started (PID $NEXTJS_PID) — http://localhost:3000"

# Give Next.js a moment to initialize
sleep 3

# ── Step 5: Start FastAPI Backend + Scheduler ────────────────
log_start "Step 5/5: Starting Python backend services..."

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Start FastAPI server
(cd "$MODEL_DIR" && python -u server.py) >> "$LOG_FILE" 2>&1 &
FASTAPI_PID=$!
save_pid "fastapi" "$FASTAPI_PID"
log_info "🔧 FastAPI started (PID $FASTAPI_PID) — http://localhost:8000"

# Give FastAPI a moment to bind the port
sleep 2

# Start Scheduler
(cd "$MODEL_DIR" && python -u scheduler.py) >> "$LOG_FILE" 2>&1 &
SCHEDULER_PID=$!
save_pid "scheduler" "$SCHEDULER_PID"
log_info "⏰ Scheduler started (PID $SCHEDULER_PID)"

# ── Startup Complete ─────────────────────────────────────────
echo "" >> "$LOG_FILE"
log_info "🎉 MediMitra is fully operational!"
log_info "   Frontend:  http://localhost:3000"
log_info "   Backend:   http://localhost:8000"
log_info "   Scheduler: Running"
log_info "   Speakers:  Auto-managed"
log_info "   Log file:  $LOG_FILE"
echo "" >> "$LOG_FILE"

# ── Process Health Monitor ────────────────────────────────────
HEALTH_CHECK_INTERVAL=15
RESTART_DELAY=5

while true; do
    sleep "$HEALTH_CHECK_INTERVAL"

    # Check Next.js
    if [ -n "$NEXTJS_PID" ] && ! kill -0 "$NEXTJS_PID" 2>/dev/null; then
        log_error "💀 Next.js crashed — restarting..."
        sleep "$RESTART_DELAY"
        (cd "$INTERFACE_DIR" && npm run dev) >> "$LOG_FILE" 2>&1 &
        NEXTJS_PID=$!
        save_pid "nextjs" "$NEXTJS_PID"
        log_info "🔄 Next.js restarted (PID $NEXTJS_PID)"
    fi

    # Check FastAPI
    if [ -n "$FASTAPI_PID" ] && ! kill -0 "$FASTAPI_PID" 2>/dev/null; then
        log_error "💀 FastAPI crashed — restarting..."
        sleep "$RESTART_DELAY"
        source "$VENV_DIR/bin/activate"
        (cd "$MODEL_DIR" && python -u server.py) >> "$LOG_FILE" 2>&1 &
        FASTAPI_PID=$!
        save_pid "fastapi" "$FASTAPI_PID"
        log_info "🔄 FastAPI restarted (PID $FASTAPI_PID)"
    fi

    # Check Scheduler
    if [ -n "$SCHEDULER_PID" ] && ! kill -0 "$SCHEDULER_PID" 2>/dev/null; then
        log_error "💀 Scheduler crashed — restarting..."
        sleep "$RESTART_DELAY"
        source "$VENV_DIR/bin/activate"
        (cd "$MODEL_DIR" && python -u scheduler.py) >> "$LOG_FILE" 2>&1 &
        SCHEDULER_PID=$!
        save_pid "scheduler" "$SCHEDULER_PID"
        log_info "🔄 Scheduler restarted (PID $SCHEDULER_PID)"
    fi

    # Check BT Monitor
    if [ -n "$BT_MONITOR_PID" ] && ! kill -0 "$BT_MONITOR_PID" 2>/dev/null; then
        log_warn "💀 Bluetooth monitor crashed — restarting..."
        "$SCRIPT_DIR/bt_connect.sh" >> "$LOG_FILE" 2>&1 &
        BT_MONITOR_PID=$!
        save_pid "bt_monitor" "$BT_MONITOR_PID"
        log_info "🔄 BT monitor restarted (PID $BT_MONITOR_PID)"
    fi
done
