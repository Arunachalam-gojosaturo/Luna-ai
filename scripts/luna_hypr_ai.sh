#!/usr/bin/env bash
# ==============================================================================
# Luna AI - Arch Linux Hyprland Quick-Action AI Controller
# ==============================================================================

MODE="selection"
QUERY=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --prompt)
            MODE="prompt"
            ;;
        --selection)
            MODE="selection"
            ;;
        --explain)
            MODE="explain"
            ;;
        --voice)
            MODE="voice"
            ;;
        *)
            QUERY="$*"
            break
            ;;
    esac
    shift
done

# Handle Voice Mode
if [[ "$MODE" == "voice" ]]; then
    notify-send -a "Luna AI" -i "audio-input-microphone" "Luna Voice" "Listening for voice command..."
    curl -s -X POST "http://localhost:3000/api/stt/record_local" >/dev/null 2>&1 &
    exit 0
fi

# Determine query input based on mode
if [[ "$MODE" == "prompt" ]]; then
    # Prompt user with fuzzel
    if command -v fuzzel >/dev/null 2>&1; then
        QUERY=$(fuzzel --dmenu --prompt "Ask Luna AI: " --lines 0 --width 50)
    elif command -v rofi >/dev/null 2>&1; then
        QUERY=$(rofi -dmenu -p "Ask Luna AI:")
    fi
    [[ -z "$QUERY" ]] && exit 0
elif [[ "$MODE" == "explain" ]]; then
    RAW_CLIP=$(wl-paste -p 2>/dev/null || wl-paste 2>/dev/null)
    [[ -z "$RAW_CLIP" ]] && {
        notify-send -a "Luna AI" -u low "Luna AI" "No text selected in clipboard to explain."
        exit 0
    }
    QUERY="Explain this concise and suggest fixes if it contains an error or code:\n${RAW_CLIP:0:3000}"
elif [[ -z "$QUERY" ]]; then
    # Default selection mode: take highlighted primary selection or clipboard
    QUERY=$(wl-paste -p 2>/dev/null || wl-paste 2>/dev/null)
    [[ -z "$QUERY" ]] && {
        notify-send -a "Luna AI" -u low "Luna AI" "No text selected. Highlight text and try again."
        exit 0
    }
    QUERY="Briefly explain or answer this concisely in 1-3 sentences:\n${QUERY:0:2000}"
fi

# Send initial feedback notification
NOTIF_ID=$(notify-send -p -a "Luna AI" -i "dialog-information" "Luna AI" "Thinking...")

# Get Gemini API Key from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$BASE_DIR/.env"
GEMINI_KEY=""
if [[ -f "$ENV_FILE" ]]; then
    GEMINI_KEY=$(grep -E '^GEMINI_API_KEY=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

RESPONSE=""

# 1. Try Luna OS Backend first (port 3000)
if curl -s --max-time 1 http://localhost:3000/api/health >/dev/null 2>&1; then
    PAYLOAD=$(jq -n --arg cmd "$QUERY" '{command: $cmd}')
    API_RES=$(curl -s --max-time 6 -X POST "http://localhost:3000/api/luna/command" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" 2>/dev/null)
    RESPONSE=$(echo "$API_RES" | jq -r '.speech // empty' 2>/dev/null)
fi

# 2. If Luna backend did not respond, call Gemini API directly (Ultra-fast gemini-3.5-flash)
if [[ -z "$RESPONSE" && -n "$GEMINI_KEY" ]]; then
    GEMINI_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=${GEMINI_KEY}"
    REQ_JSON=$(jq -n --arg text "$QUERY" '{contents: [{parts: [{text: $text}]}]}')
    GEM_RES=$(curl -s --max-time 6 -X POST "$GEMINI_URL" \
        -H "Content-Type: application/json" \
        -d "$REQ_JSON" 2>/dev/null)
    RESPONSE=$(echo "$GEM_RES" | jq -r '.candidates[0].content.parts[0].text // empty' 2>/dev/null)
fi

# 3. If still no response, fallback to local Ollama (luna-2.5b or qwen)
if [[ -z "$RESPONSE" ]]; then
    OLLAMA_PAYLOAD=$(jq -n --arg model "luna-2.5b:latest" --arg prompt "$QUERY" --argjson stream false \
        '{model: $model, prompt: $prompt, stream: $stream}')
    OLLAMA_RES=$(curl -s --max-time 10 http://localhost:11434/api/generate -d "$OLLAMA_PAYLOAD" 2>/dev/null)
    RESPONSE=$(echo "$OLLAMA_RES" | jq -r '.response // empty' 2>/dev/null)
fi

# Fallback error message if everything failed
if [[ -z "$RESPONSE" ]]; then
    RESPONSE="Could not connect to Luna AI or local LLM. Please check your network or API key."
fi

# Clean up response
CLEAN_RESPONSE=$(echo "$RESPONSE" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

# Copy response to Wayland clipboard
echo -n "$CLEAN_RESPONSE" | wl-copy 2>/dev/null

# Update notification with response
SUMMARY_QUERY=$(echo "$QUERY" | head -n 1 | cut -c 1-40)
if [[ -n "$NOTIF_ID" ]]; then
    notify-send -r "$NOTIF_ID" -a "Luna AI" -i "accessories-dictionary" "Luna AI: $SUMMARY_QUERY" "$CLEAN_RESPONSE (Copied to clipboard)"
else
    notify-send -a "Luna AI" -i "accessories-dictionary" "Luna AI: $SUMMARY_QUERY" "$CLEAN_RESPONSE (Copied to clipboard)"
fi
