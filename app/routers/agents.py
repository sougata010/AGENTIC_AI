from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.utils.cache import cache_response

router = APIRouter(prefix="/api", tags=["agents"])

class AgentRequest(BaseModel):
    agent: str
    topic: str = ""
    options: Dict[str, Any] = {}

@router.get("/agents")
async def list_agents():
    from app.agents import AGENT_INFO
    return {"agents": AGENT_INFO}

@router.post("/execute")
@cache_response(ttl=3600)
async def execute_agent(request: AgentRequest):
    from app.agents import get_agents
    
    agents = get_agents()
    
    if request.agent not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent}' not found")
    
    try:
        agent_cls = agents[request.agent]
        agent = agent_cls()
        
        params = {"topic": request.topic, **request.options}
        if request.agent == "nexus":
            params["code"] = request.options.get("code", "")
            params["error"] = request.options.get("error", "")
            params["requirements"] = request.options.get("requirements", request.topic)
            params["mode"] = request.options.get("mode", "review")
        elif request.agent == "email_gen":
            params["context"] = request.topic
            params["tone"] = request.options.get("tone", "professional")
        elif request.agent == "student_gen":
            params["student_data"] = request.topic
        elif request.agent == "security_recon":
            params["target"] = request.topic
        elif request.agent == "resume_opt":
            params["resume_text"] = request.topic
            params["job_description"] = request.options.get("job_description", "")
        elif request.agent == "debate_coach":
            params["user_argument"] = request.options.get("user_argument", "")
        elif request.agent == "travel_plan":
            params["destination"] = request.topic
            params["duration"] = request.options.get("duration", "3 days")
            params["budget"] = request.options.get("budget", "Medium")
            params["interests"] = request.options.get("interests", "Sightseeing")
        
        result = await agent.execute(**params)
        
        return {
            "success": True,
            "agent": request.agent,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
