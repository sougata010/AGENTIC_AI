import os
import time
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.config import settings

# --- Data Models from brain.ipynb ---

class Email(BaseModel):
    topic: str = Field(description="Topic in 3-5 words")
    greeting: str = Field(description="Greeting like 'Dear Mr. Smith,' or 'Hi Team,'")
    subject: str = Field(description="Subject line under 10 words")
    body: str = Field(description="Email body under 120 words. Natural human tone. No placeholders.")
    closing: str = Field(description="Sign-off with name, e.g. 'Best regards,\nSougata'")

# --- System Prompt from brain.ipynb ---

SYSTEM_PROMPT = """
You are a professional email writer. Write emails that sound natural and human.

RULES:
1. Keep body under 120 words - be concise
2. Write in natural, conversational tone
3. Each sentence should be meaningful
4. No placeholder brackets like [Your Name] - use actual names from context
5. Be direct and professional
"""

class EmailGenAgent(BaseAgent):
    name = "email_gen"
    description = "Generate professional, concise emails with natural human tone"
    icon = "✉️"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "Write an email about: {topic}")
        ])
        
        # Use a lower temperature as in the notebook (0.5)
        model = self.model # BaseAgent uses default, potentially I should allow override or set in kwargs
        # The notebook used temperature=0.5, I'll rely on the default or user config for now, 
        # or I can pass configuration if I had a way. 
        # For now, I'll just use the standard model.
        
        structured_model = model.with_structured_output(Email)
        chain = prompt | structured_model
        
        print(f"📧 Generating email for: {topic}")
        email = await self._safe_invoke(chain, {"topic": topic})
        
        filepath = await asyncio.to_thread(self._save_email, email)
        
        return {
            "email": email.model_dump(),
            "formatted_text": self._format_email(email),
            "output_file": filepath
        }
    
    def _format_email(self, email: Email) -> str:
        body = email.body.strip()
        formatted_lines = []
        current_line = ""
        
        for word in body.split():
            if len(current_line) + len(word) + 1 <= 75:
                current_line += (" " if current_line else "") + word
            else:
                formatted_lines.append(current_line)
                current_line = word
            
            if current_line.endswith(('.', '?', '!')):
                formatted_lines.append(current_line)
                current_line = ""
        
        if current_line:
            formatted_lines.append(current_line)
        
        formatted_body = "\n".join(formatted_lines)
        
        return f"""Subject: {email.subject}

{email.greeting}

{formatted_body}

{email.closing}
"""

    def _save_email(self, email: Email) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() or c in " _-" else "_" for c in email.topic[:30])
        filename = f"{timestamp}_{safe_topic}.txt"
        
        # Ensure directory exists (using settings.DATA_DIR subfolder or similar)
        # The original code used "emails/" relative to execution. 
        # I'll use settings.DATA_DIR / "emails"
        output_dir = settings.DATA_DIR / "emails"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = output_dir / filename
        
        formatted = self._format_email(email)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted)
        
        print(f"📁 Saved to: {filepath}")
        return str(filepath)
