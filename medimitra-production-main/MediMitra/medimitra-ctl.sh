#!/bin/bash
# ============================================================
# MediMitra Control Script
# Usage:
#   ./medimitra-ctl.sh start    — Start MediMitra
#   ./medimitra-ctl.sh stop     — Stop MediMitra
#   ./medimitra-ctl.sh restart  — Restart MediMitra
#   ./medimitra-ctl.sh status   — Show status of all services
#   ./medimitra-ctl.sh logs     — Tail the log file
#   ./medimitra-ctl.sh logs-full — View full log file
# ============================================================

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE_NAME="medimitra.service"
LOG_FILE="$HOME/medimitra.log"

case "$1" in
    start)
        echo -e "${GREEN}▶ Starting MediMitra...${NC}"
        systemctl --user start "$SERVICE_NAME"
        sleep 2
        systemctl --user status "$SERVICE_NAME" --no-pager
        ;;

    stop)
        echo -e "${RED}⏹ Stopping MediMitra...${NC}"
        systemctl --user stop "$SERVICE_NAME"
        echo -e "${GREEN}✅ Stopped${NC}"
        ;;

    restart)
        echo -e "${YELLOW}🔄 Restarting MediMitra...${NC}"
        systemctl --user restart "$SERVICE_NAME"
        sleep 3
        systemctl --user status "$SERVICE_NAME" --no-pager
        ;;

    status)
        echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"
        echo -e "${BOLD}  🏥 MediMitra System Status${NC}"
        echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"
        echo ""

        # Systemd service status
        if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
            echo -e "  Service:     ${GREEN}● Running${NC}"
        else
            echo -e "  Service:     ${RED}○ Stopped${NC}"
        fi

        # Next.js
        if curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null | grep -q "200\|304"; then
            echo -e "  Next.js:     ${GREEN}● http://localhost:3000${NC}"
        else
            echo -e "  Next.js:     ${RED}○ Not responding${NC}"
        fi

        # FastAPI
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            echo -e "  FastAPI:     ${GREEN}● http://localhost:8000${NC}"
        else
            echo -e "  FastAPI:     ${RED}○ Not responding${NC}"
        fi

        # Bluetooth speakers
        echo ""
        echo -e "  ${BOLD}Bluetooth Speakers:${NC}"
        SPEAKER_MAP="$(dirname "$0")/model/speaker_map.json"
        if [ -f "$SPEAKER_MAP" ]; then
            python3 -c "
import json
with open('$SPEAKER_MAP') as f:
    data = json.load(f)
for sid, info in data.items():
    mac = info.get('mac', '?')
    name = info.get('family_member', '?')
    print(f'    {name} → {mac} ({sid})')
" 2>/dev/null
        fi

        # Check connected BT devices
        echo ""
        echo -e "  ${BOLD}Connected BT Devices:${NC}"
        bluetoothctl devices Connected 2>/dev/null | while read -r line; do
            echo "    $line"
        done

        echo ""
        echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"

        # PipeWire sinks
        echo ""
        echo -e "  ${BOLD}Audio Sinks (Bluetooth):${NC}"
        pactl list short sinks 2>/dev/null | grep -i "bluez" | while read -r line; do
            echo "    $line"
        done
        echo ""
        ;;

    logs)
        echo -e "${CYAN}📋 Tailing MediMitra logs (Ctrl+C to stop)...${NC}"
        tail -f "$LOG_FILE"
        ;;

    logs-full)
        echo -e "${CYAN}📋 Full MediMitra log:${NC}"
        cat "$LOG_FILE"
        ;;

    *)
        echo -e "${BOLD}MediMitra Control Script${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|logs-full}"
        echo ""
        echo "  start      Start MediMitra services"
        echo "  stop       Stop MediMitra services"
        echo "  restart    Restart MediMitra services"
        echo "  status     Show detailed status"
        echo "  logs       Tail live logs"
        echo "  logs-full  View full log file"
        exit 1
        ;;
esac
