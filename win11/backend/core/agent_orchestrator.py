from typing import Any, Dict
from pydantic import BaseModel
from backend.core.planner import ExecutionPlan
from backend.tools.tool_registry import tool_registry

class ExecutionData(BaseModel):
    status: str
    result: str
    action: str = "NONE"
    sysCommand: str = ""
    logs: list[str] = []
    stderr: str = ""

class AgentOrchestrator:
    """
    Executes the plan by routing to specific agents.
    """
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionData:
        logs = []
        action = "NONE"
        sysCommand = ""
        result = "Successfully executed plan."
        status = "success"
        stderr = ""

        logs.append(f"Starting execution of intent: {plan.intent}")
        
        for agent_name in plan.required_agents:
            agent = tool_registry.get_agent(agent_name)
            if not agent:
                logs.append(f"[{agent_name.upper()} AGENT] ERROR: Agent not found.")
                stderr += f"Agent {agent_name} not found. "
                status = "error"
                continue
                
            logs.append(f"[{agent_name.upper()} AGENT] Invoked.")
            # We simply invoke it with a basic command for now
            try:
                cmd_to_run = plan.user_input if plan.user_input else plan.intent
                exec_res = await agent.execute(cmd_to_run, plan.intent)
                verified = await agent.verify(exec_res)
                logs.append(f"[{agent_name.upper()} AGENT] Execution {'verified' if verified else 'failed verification'}.")
                
                if exec_res.get("action") and exec_res.get("action") != "NONE":
                    action = exec_res["action"]
                if exec_res.get("sysCommand"):
                    sysCommand = exec_res["sysCommand"]
                if not verified:
                    status = "error"
                    stderr += exec_res.get("stderr", "")
            except Exception as e:
                logs.append(f"[{agent_name.upper()} AGENT] Exception: {str(e)}")
                stderr += f"Agent {agent_name} failed: {str(e)}. "
                status = "error"

        return ExecutionData(
            status=status,
            result=result,
            action=action,
            sysCommand=sysCommand,
            logs=logs,
            stderr=stderr
        )

agent_orchestrator = AgentOrchestrator()
