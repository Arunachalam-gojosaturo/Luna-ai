"""Audio system health check and permission verification for Luna OS."""

import os
import sys
import subprocess
from pathlib import Path

def check_audio_devices():
    """Check if audio devices are accessible."""
    try:
        alsa_devices = Path("/dev/snd")
        if not alsa_devices.exists():
            return {"status": "error", "message": "ALSA devices not found (/dev/snd)"}
        
        devices = list(alsa_devices.glob("pcm*"))
        if not devices:
            return {"status": "error", "message": "No ALSA PCM devices found"}
        
        readable = any(os.access(str(d), os.R_OK) for d in devices)
        writable = any(os.access(str(d), os.W_OK) for d in devices)
        
        if not readable or not writable:
            return {
                "status": "warning",
                "message": "ALSA devices found but insufficient permissions. Run: sudo usermod -aG audio $(whoami)"
            }
        
        return {"status": "ok", "message": f"Found {len(devices)} audio devices with proper permissions"}
    except Exception as e:
        return {"status": "error", "message": f"Error checking audio devices: {str(e)}"}

def check_pulseaudio():
    """Check if PulseAudio is running and accessible."""
    try:
        result = subprocess.run(["pgrep", "-f", "pulseaudio"], capture_output=True)
        if result.returncode != 0:
            return {"status": "info", "message": "PulseAudio not running (using ALSA)"}
        
        pulse_socket = Path.home() / ".pulse"
        if not pulse_socket.exists():
            return {"status": "warning", "message": "PulseAudio socket not found"}
        
        return {"status": "ok", "message": "PulseAudio is running and accessible"}
    except Exception as e:
        return {"status": "info", "message": f"Could not check PulseAudio: {str(e)}"}

def check_user_groups():
    """Check if user is in required audio groups."""
    try:
        result = subprocess.run(["groups"], capture_output=True, text=True)
        groups = result.stdout.strip().split()
        
        audio_group = "audio" in groups
        
        if not audio_group:
            return {
                "status": "warning",
                "message": "User not in 'audio' group. Run: sudo usermod -aG audio $(whoami)",
                "audio_group": False
            }
        
        return {
            "status": "ok",
            "message": "User is in required audio groups",
            "audio_group": audio_group
        }
    except Exception as e:
        return {"status": "error", "message": f"Error checking user groups: {str(e)}"}

def check_microphone_access():
    """Test if microphone can be accessed via speech_recognition."""
    try:
        import speech_recognition as sr
        
        with sr.Microphone() as source:
            pass
        
        return {"status": "ok", "message": "Microphone is accessible via speech_recognition"}
    except Exception as e:
        error_msg = str(e).lower()
        
        if "permission" in error_msg or "device" in error_msg:
            return {
                "status": "error",
                "message": f"Microphone access denied: {str(e)}",
                "fix": "Run: sudo usermod -aG audio $(whoami) && newgrp audio"
            }
        
        return {"status": "error", "message": f"Microphone error: {str(e)}"}

def full_audio_check():
    """Run complete audio system check."""
    print("\n🔊 Luna OS Audio System Health Check")
    print("=" * 50)
    
    checks = {
        "Audio Devices": check_audio_devices(),
        "PulseAudio": check_pulseaudio(),
        "User Groups": check_user_groups(),
        "Microphone Access": check_microphone_access(),
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = result.get("status", "unknown")
        message = result.get("message", "Unknown status")
        
        icon = "✅" if status == "ok" else "⚠️" if status == "warning" else "❌" if status == "error" else "ℹ️"
        print(f"\n{icon} {check_name}: {status.upper()}")
        print(f"   {message}")
        
        if status == "error":
            all_ok = False
            if "fix" in result:
                print(f"   🔧 Fix: {result['fix']}")
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ Audio system is ready for voice commands!")
    else:
        print("❌ Audio system has issues. See fixes above.")
    print()
    
    return checks

if __name__ == "__main__":
    full_audio_check()
