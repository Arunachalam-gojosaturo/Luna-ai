import speech_recognition as sr
import threading
import asyncio
from backend.core.task_manager import ws_manager

class VoiceAgent:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"[Voice] Warning: Could not initialize microphone globally: {e}")
            self.microphone = None
            
        self.is_listening = False
        self.stop_listening_func = None
        self.main_loop = None
        self.is_speaking = False
        self.is_awake = False
        self.last_speaking_time = 0

    def set_speaking(self, speaking: bool):
        import time
        self.is_speaking = speaking
        if speaking:
            print("[Voice] Suspended mic - Luna is speaking")
        else:
            self.last_speaking_time = time.time()
            print("[Voice] Resumed mic")

    def start_background_listening(self):
        if self.is_listening or not self.microphone: 
            return
        self.is_listening = True
        
        self.main_loop = asyncio.get_running_loop()
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
        def callback(recognizer, audio):
            import time
            if self.is_speaking:
                if time.time() - self.last_speaking_time > 15.0:
                    print("[Voice] Failsafe: Resetting speaking lock (15s timeout)")
                    self.is_speaking = False
                else:
                    return
            
            if time.time() - self.last_speaking_time < 2.0:
                return
                
            try:
                text = recognizer.recognize_google(audio).lower()
                print(f"[Voice] Heard: {text}")
                
                # Check for wake word
                wake_words = ["luna wake up", "luna"]
                found_wake = False
                for w in wake_words:
                    if w in text:
                        found_wake = True
                        text = text.replace(w, "").strip()
                        break
                
                if found_wake:
                    self.is_awake = True
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.broadcast("WAKE_WORD_DETECTED", {"text": "luna"}), 
                        self.main_loop
                    )
                    
                    if text:
                        # They said a command right after the wake word
                        asyncio.run_coroutine_threadsafe(
                            ws_manager.broadcast("VOICE_COMMAND", {"text": text}),
                            self.main_loop
                        )
                        self.is_awake = False
                elif self.is_awake:
                    # Send as command and go back to sleep
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.broadcast("VOICE_COMMAND", {"text": text}),
                        self.main_loop
                    )
                    self.is_awake = False
                    
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[Voice] Request Error: {e}")
            except Exception as e:
                print(f"[Voice] Unexpected Error in callback: {e}")

        # listen_in_background spawns a thread
        self.stop_listening_func = self.recognizer.listen_in_background(self.microphone, callback)
        print("[Voice] Background listening started.")

    def stop_background_listening(self):
        if self.stop_listening_func:
            self.stop_listening_func(wait_for_stop=False)
        self.is_listening = False
        print("[Voice] Background listening stopped.")

voice_agent = VoiceAgent()
