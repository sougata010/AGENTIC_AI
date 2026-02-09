from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from app.config import settings

from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent LLM calls
llm_semaphore = asyncio.Semaphore(2)

# Global response cache (1 hour TTL, 100 entries)
response_cache = TTLCache(maxsize=100, ttl=3600)

class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"
    icon: str = "🤖"
    
    def __init__(self, temperature: float = 0.7):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=temperature,
            google_api_key=settings.GEMINI_API_KEY,
            transport="rest"
        )
    
    def get_structured_model(self, schema):
        return self.model.with_structured_output(schema)
    
    @retry(
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        wait=wait_exponential(multiplier=2, min=10, max=120),
        stop=stop_after_attempt(10),
        before_sleep=lambda retry_state: logger.warning(f"⚠️ Quota hit. Retrying in {retry_state.next_action.sleep}s...")
    )
    async def _safe_invoke(self, chain, inputs: Dict[str, Any]) -> Any:
        # Create a cache key from inputs and agent name
        # We use a stable string representation
        cache_key = f"{self.name}:{hash(str(inputs))}"
        
        if cache_key in response_cache:
            logger.info(f"💾 Cache hit for agent: {self.name}")
            return response_cache[cache_key]
            
        async with llm_semaphore:
            logger.info(f"🤖 Invoking LLM for agent: {self.name}")
            result = await chain.ainvoke(inputs)
            response_cache[cache_key] = result
            return result
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute")
    
    def get_info(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "icon": self.icon
        }
