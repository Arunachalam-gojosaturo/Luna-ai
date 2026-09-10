import os
import json
import asyncio
import re
from typing import AsyncGenerator, Dict, Any

from backend.core.context_engine import context_engine
from backend.memory.working_memory import working_memory
from backend.core.planner import planner, ReasoningDepth
from backend.core.decision_engine import decision_engine
from backend.core.agent_orchestrator import agent_orchestrator
from backend.providers.provider_manager import ProviderManager
from backend.memory.long_term_memory import long_term_memory
from backend.memory.chat_history import chat_history_db
from backend.core.prompt import build_system_prompt

class LunaBrain:
    def __init__(self):
        self.provider_manager = ProviderManager()

    async def process_request_stream(self, request_data: dict) -> AsyncGenerator[str, None]:
        """
        New stream-based pipeline (for WebSockets/SSE) as defined in Blueprint.
        """
        user_input = request_data.get("command", "")
        
        # 1. Gather Context
        os_context = await context_engine.get_current_state()
        
        # 2. Adaptive Planning
        plan = await planner.create_plan(user_input, os_context, working_memory.get_all())
        
        # 3. Execution & Orchestration
        if plan.depth == ReasoningDepth.FAST:
            # Direct LLM streaming, no tool calls
            async for chunk in self.provider_manager.stream_chat(user_input, os_context, request_data):
                yield chunk
        else:
            # Multi-step or Agent execution
            execution_data = await agent_orchestrator.execute_plan(plan)
            
            # 4. Verification (Self-Correction)
            verified = await decision_engine.verify_execution(execution_data.model_dump())
            if not verified.success:
                yield f"I encountered an issue: {verified.error}. Attempting to recover..."
                return

            # 5. Memory Update
            working_memory.update("last_action", execution_data.action)
            await long_term_memory.save_interaction("default_session", "user", user_input)
            
            # 6. Final LLM generation based on execution
            prompt = f"Based on the successful execution of {plan.steps}, summarize the result for the user: {execution_data.result}"
            async for chunk in self.provider_manager.stream_chat(prompt, os_context, request_data):
                yield chunk

    async def process_request_json(self, req) -> dict:
        """
        Compatibility wrapper for existing UI REST calls that expect JSON.
        """
        user_input = req.command
        session_id = "default"
        
        chat_history_db.add_message(session_id, "user", user_input)

        # 1. Gather Context & 2. Memory Retrieval concurrently
        try:
            os_context, past_memories = await asyncio.gather(
                context_engine.get_current_state(),
                asyncio.wait_for(long_term_memory.semantic_search(user_input, limit=3), timeout=0.8),
                return_exceptions=True
            )
            if isinstance(os_context, Exception):
                os_context = {}
            if isinstance(past_memories, Exception) or not past_memories:
                past_memories = []
        except Exception:
            os_context = {}
            past_memories = []
        
        memory_str = "\n".join([f"- {m['content']}" for m in past_memories]) if past_memories else "No relevant past context."

        # 3. Adaptive Planning
        plan = await planner.create_plan(user_input, os_context, working_memory.get_all())

        # 4. Execution & Orchestration
        if plan.depth == ReasoningDepth.FAST or not plan.required_agents:
            execution_data = None
            action = "NONE"
            sys_command = ""
            logs = ["[BRAIN] Direct intelligence mode."]
            already_executed = False
        else:
            execution_data = await agent_orchestrator.execute_plan(plan)
            verified = await decision_engine.verify_execution(execution_data.model_dump())
            action = execution_data.action
            sys_command = execution_data.sysCommand
            logs = execution_data.logs
            already_executed = getattr(execution_data, "alreadyExecuted", True)
            if not verified.success:
                logs.append(f"[ERROR] Execution failed: {verified.error}")

        # 5. Build prompt
        system_prompt = build_system_prompt(
            os_context, 
            memory_str, 
            plan.depth.value, 
            plan.intent, 
            logs
        )
        messages = [{"role": "system", "content": system_prompt}]
        db_history = chat_history_db.get_history(session_id, limit=20)
        for msg in db_history:
            # Skip the very last one we just added if it's the user input, or we can just let it be.
            # Wait, since we appended the user_input above, it will be the last item in db_history!
            pass
            
        # We need to construct messages carefully.
        # Re-fetch from DB, the last one is the current prompt. We can just use the DB history directly!
        for msg in db_history[:-1]:
            r = "assistant" if msg.get("role") in ["model", "assistant"] else "user"
            messages.append({"role": r, "content": msg.get("content", "")})
            
        # Finally append the current user input
        messages.append({"role": "user", "content": user_input})

        # 6. Get Response
        result_json = await self.provider_manager.get_json(messages, req)
        
        # Validate response structure
        if not isinstance(result_json, dict) or not result_json or "speech" not in result_json:
            result_json = {
                "state": "Speaking",
                "speech": "I processed your request but couldn't generate a detailed response.",
                "action": action,
                "sysCommand": sys_command,
                "alreadyExecuted": already_executed,
                "logs": logs + ["[FALLBACK] Using default response"],
                "notifications": []
            }
        else:
            result_json["logs"] = result_json.get("logs", []) + logs
            if action != "NONE":
                result_json["action"] = action
                result_json["sysCommand"] = sys_command
            result_json["alreadyExecuted"] = already_executed

        # 6.5 Intelligent Device Routing & Protection Layer (Arch Linux vs Mobile)
        mobile_connected = os_context.get("mobile_connected", False)
        cmd_lower = user_input.lower().strip()
        sys_cmd = result_json.get("sysCommand", "").strip()
        target_dev = result_json.get("targetDevice", "")

        # A. WhatsApp Handling: Default to Arch Linux desktop unless user explicitly asked on mobile
        if "whatsapp" in cmd_lower:
            is_mobile_req = any(k in cmd_lower for k in ["on mobile", "on phone", "on android", "on device"])
            if not is_mobile_req:
                result_json["targetDevice"] = "Arch Linux"
                result_json["action"] = "APP_CONTROL"
                result_json["sysCommand"] = "xdg-open 'https://web.whatsapp.com'"
                speech = result_json.get("speech", "")
                if "on your mobile" in speech.lower() or "on mobile" in speech.lower():
                    result_json["speech"] = "Opening WhatsApp Web on your Arch Linux desktop."
            elif not mobile_connected:
                result_json["targetDevice"] = "Android"
                result_json["action"] = "NONE"
                result_json["sysCommand"] = ""
                result_json["speech"] = "Your mobile device is not connected via ADB. Please connect your phone first."

        # B. General Mobile Guard: If mobile is disconnected and response tries ADB or targets Android
        elif not mobile_connected and (target_dev == "Android" or sys_cmd.startswith("adb")):
            result_json["action"] = "NONE"
            result_json["sysCommand"] = ""
            result_json["targetDevice"] = "NONE"
            speech = result_json.get("speech", "")
            if any(w in speech.lower() for w in ["mobile", "phone", "unlock"]):
                result_json["speech"] = "Your mobile device is currently not connected via ADB. Please connect your phone via USB or Wi-Fi first."

        # 6.6 Greeting & Self-Introduction Handling (Remove name, ensure awesome Luna intro)
        cmd_strip = user_input.strip().lower()
        greeting_words = {
            "hi", "hello", "hey", "hi luna", "hello luna", "hey luna",
            "greetings", "good morning", "good afternoon", "good evening",
            "who are you", "who are you?", "who are you luna", "who are you luna?",
            "introduce yourself", "introduce yourself luna", "what can you do", "what can you do?"
        }
        is_greeting = (
            cmd_strip in greeting_words or
            (any(cmd_strip.startswith(g + " ") for g in ["hi", "hello", "hey"]) and len(cmd_strip.split()) <= 3)
        )

        if is_greeting:
            speech = result_json.get("speech", "")
            # Remove any user name references from self-introduction
            speech = re.sub(r"\b(Arunachalam's|Arunachalam’s)\s+(personal\s+)?(AI\s+)?(assistant|operating\s+system)\b", "an advanced autonomous AI operating system", speech, flags=re.IGNORECASE)
            speech = re.sub(r"\b(Arunachalam|Boss)[,!\s]+", "", speech, flags=re.IGNORECASE)
            speech = re.sub(r"[,!\s]+(Arunachalam|Boss)\b", "", speech, flags=re.IGNORECASE)
            # Ensure Luna establishes her awesome identity
            if "luna" not in speech.lower() or len(speech.split()) < 8:
                speech = "Hello! I am Luna — an advanced autonomous AI operating system and intelligent workstation companion. I'm engineered for deep Linux system control, cybersecurity workflows, full-stack software architecture, and high-performance automation. All neural subsystems are online and operating at peak efficiency. What are we conquering today?"
            result_json["speech"] = speech.strip()
            result_json["state"] = "Speaking"

        # 7. Memory Update
        chat_history_db.add_message(session_id, "assistant", result_json.get("speech", ""))
        await long_term_memory.save_interaction(session_id, "user", user_input)
        await long_term_memory.save_interaction(session_id, "assistant", result_json.get("speech", ""))
        
        result_json["geminiActive"] = bool(os.getenv("GEMINI_API_KEY"))
        return result_json

luna_brain = LunaBrain()

__all__ = ["LunaBrain", "luna_brain"]
