import os
import json
import asyncio
import re
from backend.core.provider import ProviderManager
from backend.agents.system import SystemAgent
from backend.memory.embeddings import save_conversation, semantic_search_memory
from backend.core.context import context_engine
from backend.core.decision import decision_engine
from backend.core.planner import planner_engine
from backend.core.executor import executor_engine

class LunaBrainV2:
    """
    Jarvis-Class AI Intelligence Core.
    """
    def __init__(self):
        self.provider = ProviderManager()
        self.system_agent = SystemAgent()
        
    async def process(self, command: str, session_id: str = "default_session"):
        return await self.process_command(command)

    async def process_command(self, req):
        if isinstance(req, str):
            from backend.api.routes import CommandRequest
            command = req
            req = CommandRequest(command=command)
        else:
            command = req.command
        session_id = "default_session"

        # 1. Context Analyzer (Working Memory)
        sys_context = context_engine.get_system_context()

        # 2. Intent Detection & Decision Engine
        intent = decision_engine.detect_intent(command)
        reasoning_depth = decision_engine.determine_reasoning_depth(command)

        # 3. Memory Retrieval (Semantic Memory)
        try:
            past_memories = await semantic_search_memory(command, limit=5 if reasoning_depth == "deep" else 2)
            memory_str = "\n".join([f"- {m.content}" for m in past_memories]) if past_memories else "No relevant past context."
        except Exception:
            memory_str = "No relevant past context."

        # 4. Planning Engine
        plan = planner_engine.generate_plan(command, intent, reasoning_depth)
        plan_str = "\\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])

        # 5. Agent Execution & Tool Selection (Orchestration)
        execution_results = await executor_engine.execute_plan(plan, intent, command)

        # 6. Build the highly contextualized prompt
        system_prompt = f"""You are Luna, an advanced autonomous AI operating system and intelligent workstation companion.
You control an Arch Linux workstation.

CRITICAL RULES:
- When the user starts with a greeting ("Hi", "Hello", "Hey", "Hi Luna", "Introduce yourself", "Who are you?", "Good morning"), Luna MUST introduce herself with an AWESOME, high-tech, confident self-introduction as Luna, the autonomous AI operating system.
- NEVER include the user's name (do NOT say "Arunachalam", "Boss", or any user name) in Luna's self-introduction! Introduce Luna directly and powerfully.

# Active System Context
OS: {sys_context['os']} {sys_context['release']}
CPU: {sys_context['cpu_usage']}% | RAM: {sys_context['ram_usage']}%
CWD: {sys_context['cwd']}

# Semantic Memory
{memory_str}

# Execution Plan & Agent Verification
Reasoning Depth: {reasoning_depth}
Intent: {intent}
Plan Executed:
{plan_str}
Verification Logs: {execution_results['logs']}

When the user enters an input, analyze their request and respond in the following structured JSON format:
{{
  "state": "Idle" | "Listening" | "Thinking" | "Speaking" | "Executing" | "Warning",
  "speech": "Your response text to display and read out loud. Be conversational, natural, and friendly.",
  "action": "APP_CONTROL" | "SYSTEM_MANAGEMENT" | "FILE_OPERATION" | "MONITORING" | "SYNC_DEVICE" | "RUN_TESTS" | "TRIGGER_BUILD" | "ADD_GOAL" | "TOGGLE_DEVICE" | "EXECUTE_SYSTEM_COMMAND" | "NONE",
  "sysCommand": "The exact bash/shell command to execute. For URLs use 'xdg-open <url>'. If no command is needed, leave empty.",
  "requiresPrivilege": false,
  "targetDevice": "Android" | "Arch Linux" | "Windows" | "NONE",
  "logs": ["Array of 4 to 6 lines of simulated highly technical logs"],
  "notifications": ["Array of short notifications"]
}}
Ensure the output is strictly valid JSON.
User command: "{command}"
"""
        messages = [{"role": "system", "content": system_prompt}]
        for msg in req.history:
            r = "assistant" if msg.get("role") in ["model", "assistant"] else "user"
            messages.append({"role": r, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": command})
            
        # 7. Streaming Response (Provider Routing)
        result_json = await self.provider.generate_response(messages, req)
        
        # Override the LLM action if our executor confidently generated one
        if execution_results['action'] != "NONE" and result_json.get("action") == "NONE":
            result_json["action"] = execution_results['action']
            result_json["sysCommand"] = execution_results['sysCommand']
            
        # Merge logs
        result_json["logs"] = result_json.get("logs", []) + execution_results['logs']

        # Ensure Luna's awesome self-introduction on greetings without user name
        cmd_strip = command.strip().lower()
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
            speech = re.sub(r"\b(Arunachalam's|Arunachalam’s)\s+(personal\s+)?(AI\s+)?(assistant|operating\s+system)\b", "an advanced autonomous AI operating system", speech, flags=re.IGNORECASE)
            speech = re.sub(r"\b(Arunachalam|Boss)[,!\s]+", "", speech, flags=re.IGNORECASE)
            speech = re.sub(r"[,!\s]+(Arunachalam|Boss)\b", "", speech, flags=re.IGNORECASE)
            if "luna" not in speech.lower() or len(speech.split()) < 8:
                speech = "Hello! I am Luna — an advanced autonomous AI operating system and intelligent workstation companion. I'm engineered for deep Linux system control, cybersecurity workflows, full-stack software architecture, and high-performance automation. All neural subsystems are online and operating at peak efficiency. What are we conquering today?"
            result_json["speech"] = speech.strip()
            result_json["state"] = "Speaking"

        # 8. Store Long-Term Semantic Memory
        try:
            await save_conversation(session_id, "user", command)
            await save_conversation(session_id, "assistant", result_json.get("speech", ""))
        except Exception:
            pass

        # 9. Audit Logging
        if result_json.get("sysCommand") or result_json.get("action") != "NONE":
            self.system_agent.append_audit_log(
                command, 
                result_json.get("action", "NONE"), 
                result_json.get("sysCommand", ""), 
                result_json.get("requiresPrivilege", False)
            )
            
        result_json["geminiActive"] = bool(os.getenv("GEMINI_API_KEY"))
        return result_json

luna_brain_v2 = LunaBrainV2()

__all__ = ["LunaBrainV2", "luna_brain_v2"]
