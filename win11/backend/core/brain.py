import os
import json
import asyncio
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

        # 1. Gather Context
        os_context = await context_engine.get_current_state()
        
        # 2. Memory Retrieval
        past_memories = await long_term_memory.semantic_search(user_input, limit=3)
        memory_str = "\\n".join([f"- {m['content']}" for m in past_memories]) if past_memories else "No relevant past context."

        # 3. Adaptive Planning
        plan = await planner.create_plan(user_input, os_context, working_memory.get_all())

        # 4. Execution & Orchestration
        if plan.depth == ReasoningDepth.FAST:
            execution_data = None
            action = "NONE"
            sys_command = ""
            logs = ["[BRAIN] Fast mode bypassed planning."]
        else:
            execution_data = await agent_orchestrator.execute_plan(plan)
            verified = await decision_engine.verify_execution(execution_data.model_dump())
            action = execution_data.action
            sys_command = execution_data.sysCommand
            logs = execution_data.logs
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
                "action": "NONE",
                "logs": logs + ["[FALLBACK] Using default response"],
                "notifications": []
            }
        else:
            result_json["logs"] = result_json.get("logs", []) + logs
            if action != "NONE" and result_json.get("action") == "NONE":
                result_json["action"] = action
                result_json["sysCommand"] = sys_command

        # 7. Memory Update
        chat_history_db.add_message(session_id, "assistant", result_json.get("speech", ""))
        await long_term_memory.save_interaction(session_id, "user", user_input)
        await long_term_memory.save_interaction(session_id, "assistant", result_json.get("speech", ""))
        
        result_json["geminiActive"] = bool(os.getenv("GEMINI_API_KEY"))
        return result_json
