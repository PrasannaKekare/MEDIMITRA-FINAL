#!/bin/bash
# ============================================================
# MediMitra — Bluetooth Speaker Auto-Connect Script
# Reads speaker MACs from speaker_map.json and connects them.
# Runs in foreground with periodic reconnect checks.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEAKER_MAP="$SCRIPT_DIR/model/speaker_map.json"
LOG_PREFIX="[BT-CONNECT]"
MAX_RETRIES=10
RETRY_DELAY=5
CHECK_INTERVAL=60

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${CYAN}$(date '+%H:%M:%S')${NC} ${GREEN}${LOG_PREFIX}${NC} $1"; }
log_warn()  { echo -e "${CYAN}$(date '+%H:%M:%S')${NC} ${YELLOW}${LOG_PREFIX}${NC} $1"; }
log_error() { echo -e "${CYAN}$(date '+%H:%M:%S')${NC} ${RED}${LOG_PREFIX}${NC} $1"; }

# Extract MAC addresses from speaker_map.json
get_speaker_macs() {
    if [ ! -f "$SPEAKER_MAP" ]; then
        log_error "Speaker map not found at $SPEAKER_MAP"
        return 1
    fi

    # Parse MACs from the JSON file using python (available on the Pi)
    python3 -c "
import json, sys
try:
    with open('$SPEAKER_MAP') as f:
        data = json.load(f)
    for sid, info in data.items():
        mac = info.get('mac', '')
        name = info.get('family_member', 'Unknown')
        if mac:
            print(f'{mac}|{name}')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Check if a Bluetooth device is connected
is_connected() {
    local mac="$1"
    bluetoothctl info "$mac" 2>/dev/null | grep -q "Connected: yes"
}

# Check if PipeWire sink exists for a speaker
has_audio_sink() {
    local mac="$1"
    local mac_underscored="${mac//:/_}"
    pactl list short sinks 2>/dev/null | grep -q "bluez_output.${mac_underscored}"
}

# Connect a single Bluetooth speaker
connect_speaker() {
    local mac="$1"
    local name="$2"
    local retries=0

    if is_connected "$mac"; then
        if has_audio_sink "$mac"; then
            log_info "✅ $name ($mac) — already connected with audio sink"
            return 0
        else
            log_warn "⚠️  $name ($mac) — connected but no audio sink, reconnecting..."
            bluetoothctl disconnect "$mac" > /dev/null 2>&1
            sleep 2
        fi
    fi

    log_info "🔗 Connecting to $name ($mac)..."

    while [ $retries -lt $MAX_RETRIES ]; do
        retries=$((retries + 1))

        # Trust and connect
        bluetoothctl trust "$mac" > /dev/null 2>&1
        bluetoothctl connect "$mac" > /dev/null 2>&1

        # Wait for connection to establish
        sleep 3

        if is_connected "$mac"; then
            # Wait a bit more for PipeWire to register the sink
            sleep 2

            if has_audio_sink "$mac"; then
                log_info "✅ $name ($mac) — connected successfully (attempt $retries)"
                return 0
            else
                log_warn "⚠️  $name ($mac) — connected but waiting for audio sink..."
                sleep 3
                if has_audio_sink "$mac"; then
                    log_info "✅ $name ($mac) — audio sink ready"
                    return 0
                fi
            fi
        fi

        log_warn "🔄 $name ($mac) — retry $retries/$MAX_RETRIES in ${RETRY_DELAY}s..."
        sleep "$RETRY_DELAY"
    done

    log_error "❌ $name ($mac) — failed to connect after $MAX_RETRIES attempts"
    return 1
}

# Connect all speakers from the map
connect_all_speakers() {
    local speakers
    speakers=$(get_speaker_macs)

    if [ -z "$speakers" ]; then
        log_error "No speakers found in speaker_map.json"
        return 1
    fi

    local all_ok=true

    while IFS='|' read -r mac name; do
        if [ -n "$mac" ]; then
            connect_speaker "$mac" "$name" || all_ok=false
        fi
    done <<< "$speakers"

    if $all_ok; then
        log_info "🎉 All speakers connected successfully"
        return 0
    else
        log_warn "⚠️  Some speakers failed to connect"
        return 1
    fi
}

# One-shot mode: just connect and exit
if [ "$1" = "--once" ]; then
    connect_all_speakers
    exit $?
fi

# Persistent mode: connect then monitor
log_info "Starting Bluetooth speaker monitor..."
connect_all_speakers

log_info "Monitoring speaker connections every ${CHECK_INTERVAL}s..."
while true; do
    sleep "$CHECK_INTERVAL"

    # Re-read speaker map (it might have been updated via the web UI)
    speakers=$(get_speaker_macs)
    if [ -z "$speakers" ]; then
        continue
    fi

    while IFS='|' read -r mac name; do
        if [ -n "$mac" ]; then
            if ! is_connected "$mac" || ! has_audio_sink "$mac"; then
                log_warn "🔌 $name ($mac) disconnected — reconnecting..."
                connect_speaker "$mac" "$name"
            fi
        fi
    done <<< "$speakers"
done
