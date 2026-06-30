import os
import json
import asyncio
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
        
    async def process_command(self, req):
        command = req.command
        session_id = "default_session"

        # 1. Context Analyzer (Working Memory)
        sys_context = context_engine.get_system_context()

        # 2. Intent Detection & Decision Engine
        intent = decision_engine.detect_intent(command)
        reasoning_depth = decision_engine.determine_reasoning_depth(command)

        # 3. Memory Retrieval (Semantic Memory)
        past_memories = await semantic_search_memory(command, limit=5 if reasoning_depth == "deep" else 2)
        memory_str = "\\n".join([f"- {m.content}" for m in past_memories]) if past_memories else "No relevant past context."

        # 4. Planning Engine
        plan = planner_engine.generate_plan(command, intent, reasoning_depth)
        plan_str = "\\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])

        # 5. Agent Execution & Tool Selection (Orchestration)
        execution_results = await executor_engine.execute_plan(plan, intent, command)

        # 6. Build the highly contextualized prompt
        system_prompt = f"""You are Luna, a highly intelligent, sophisticated personal AI Operating System (Version 3.0).
You control an Arch Linux workstation.

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
            
        # 7. Streaming Response (Provider Routing)
        result_json = await self.provider.generate_response(messages, req)
        
        # Override the LLM action if our executor confidently generated one
        if execution_results['action'] != "NONE" and result_json.get("action") == "NONE":
            result_json["action"] = execution_results['action']
            result_json["sysCommand"] = execution_results['sysCommand']
            
        # Merge logs
        result_json["logs"] = result_json.get("logs", []) + execution_results['logs']

        # 8. Store Long-Term Semantic Memory
        await save_conversation(session_id, "user", command)
        await save_conversation(session_id, "assistant", result_json.get("speech", ""))

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
