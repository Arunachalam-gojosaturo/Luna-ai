import subprocess
import os
import signal

class WhatsAppAgentManager:
    def __init__(self):
        self.process = None
        self.agent_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "whatsapp_agent")
        self.script_path = os.path.join(self.agent_dir, "index.js")
        self.qr_txt_path = os.path.join(self.agent_dir, "qr_base64.txt")
        self.auth_dir = os.path.join(self.agent_dir, "auth_info_baileys")

    def start(self):
        if self.process and self.process.poll() is None:
            return {"status": "already_running"}
        
        # Start node index.js in a subprocess
        try:
            self.process = subprocess.Popen(
                ["node", self.script_path],
                cwd=self.agent_dir
            )
            return {"status": "started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop(self):
        if not self.process or self.process.poll() is not None:
            return {"status": "not_running"}
        
        try:
            self.process.terminate()
            self.process.wait(timeout=3)
            self.process = None
            return {"status": "stopped"}
        except Exception as e:
            try:
                self.process.kill()
                self.process = None
                return {"status": "killed"}
            except Exception as ex:
                return {"status": "error", "message": str(ex)}

    def get_status(self):
        is_running = self.process is not None and self.process.poll() is None
        
        # Check if auth files exist
        has_auth = os.path.exists(self.auth_dir) and len(os.listdir(self.auth_dir)) > 0 if os.path.exists(self.auth_dir) else False
        
        # Check if qr code txt file exists
        qr_data = None
        if os.path.exists(self.qr_txt_path):
            try:
                with open(self.qr_txt_path, "r") as f:
                    qr_data = f.read().strip()
            except Exception:
                pass
        
        # If we have auth, it's either connected or connecting
        # If we have qr_data, we are not connected and displaying qr
        connected = has_auth and (qr_data is None)

        return {
            "is_running": is_running,
            "connected": connected,
            "qr": qr_data
        }

whatsapp_manager = WhatsAppAgentManager()
