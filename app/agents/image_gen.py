import os
import time
import json
import base64
import requests
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.base import BaseAgent
from app.config import settings

# --- Data Models from functions.py ---

class PinIntent(BaseModel):
    primary_goal: str = Field(description="Main objective of the pin")
    target_audience: str = Field(description="Specific audience persona")
    search_intent: str = Field(description="Pinterest search intent")

class VisualConcept(BaseModel):
    scene_description: str = Field(description="Overall scene and composition")
    subject_focus: str = Field(description="Main subject of the image")
    background_style: str = Field(description="Background aesthetic")
    lighting_style: str = Field(description="Lighting mood")
    camera_angle: str = Field(description="Camera framing or angle")

class ImageGenerationPrompt(BaseModel):
    prompt: str = Field(description="Highly detailed image generation prompt")
    negative_prompt: str = Field(description="Visual elements to avoid")
    aspect_ratio: str = Field(description="Pinterest-friendly aspect ratio")
    quality_tags: List[str] = Field(description="Quality and realism tags")

class TextOverlay(BaseModel):
    headline: str = Field(description="Primary hook text on the image")
    supporting_text: str = Field(description="Secondary optional text")
    font_style: str = Field(description="Font pairing or style")
    text_alignment: str = Field(description="Text alignment")
    placement: str = Field(description="Exact placement on image")

class ColorAndStyle(BaseModel):
    color_palette: List[str] = Field(description="3 hex colors")
    design_style: str = Field(description="Overall design style")
    emotional_vibe: str = Field(description="Emotional tone")

class SeoMetadata(BaseModel):
    pin_title: str = Field(description="SEO-optimized Pinterest title")
    pin_description: str = Field(description="Keyword-rich description with hashtags")
    primary_keywords: List[str] = Field(description="Main SEO keywords")

class PinterestPinStrategy(BaseModel):
    pin_intent: PinIntent
    visual_concept: VisualConcept
    image_generation_prompt: ImageGenerationPrompt
    text_overlay: TextOverlay
    color_and_style: ColorAndStyle
    seo_metadata: SeoMetadata

# --- System Prompt from prompts.py ---

SYSTEM_PROMPT = """
You are a Senior Pinterest Creative Strategist and Visual Director.

Your task is to generate a HIGH-END, PROFESSIONAL Pinterest Pin concept
that is visually polished, scroll-stopping, and optimized for saves.

Return ONLY valid JSON that strictly matches the schema below.

{{
  "pin_intent": {{
    "primary_goal": "The core goal of the pin (e.g., Inspire, Educate, Drive Clicks)",
    "target_audience": "Specific audience persona",
    "search_intent": "Pinterest search intent (Informational, Inspirational, Transactional)"
  }},
  "visual_concept": {{
    "scene_description": "Clear description of the overall scene and composition",
    "subject_focus": "Main visual subject",
    "background_style": "Background aesthetic (e.g., Minimal, Lifestyle, Textured)",
    "lighting_style": "Lighting mood (e.g., Soft Natural, High Contrast)",
    "camera_angle": "Camera framing (e.g., Flat lay, Eye-level, Top-down)"
  }},
  "image_generation_prompt": {{
    "prompt": "Ultra-detailed prompt for Midjourney/DALL·E",
    "negative_prompt": "What to avoid visually",
    "aspect_ratio": "Pinterest-optimized ratio (e.g., 2:3)",
    "quality_tags": ["High resolution", "Editorial quality", "Pinterest aesthetic"]
  }},
  "text_overlay": {{
    "headline": "Short, bold hook text for the image",
    "supporting_text": "Optional secondary line (can be empty)",
    "font_style": "Font pairing style (e.g., Bold Serif + Clean Sans)",
    "text_alignment": "Left, Center, or Right",
    "placement": "Exact placement on image (e.g., Upper third)"
  }},
  "color_and_style": {{
    "color_palette": ["#HEX1", "#HEX2", "#HEX3"],
    "design_style": "Overall design style (e.g., Minimalist, Editorial, Cozy)",
    "emotional_vibe": "Emotional tone (e.g., Calm, Aspirational, Energetic)"
  }},
  "seo_metadata": {{
    "pin_title": "SEO-optimized Pinterest title",
    "pin_description": "Keyword-rich description with 3–5 hashtags",
    "primary_keywords": ["keyword1", "keyword2", "keyword3"]
  }}
}}

No explanations.
No markdown.
JSON output only.
"""

class ImageGenAgent(BaseAgent):
    name = "image_gen"
    description = "Generate high-end Pinterest-optimized images with strategy and validation"
    icon = "🎨"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Executes the full 3-phase pipeline:
        1. Planning: Generate strategy
        2. Execution: Generate image
        3. Validation: Critic/Grade image
        """
        print(f"🚀 Starting Pipeline for: {topic}")
        
        # Phase 1: Planning
        print("🧠 Phase 1: Planning...")
        strategy = await self._generate_strategy(topic)
        
        # Phase 2: Execution
        print("🎨 Phase 2: Executing (Media Gen)...")
        image_path = await asyncio.to_thread(self._generate_image, strategy)
        
        result = {
            "strategy": strategy.model_dump(),
            "image_path": image_path
        }
        
        # Phase 3: Validation
        if image_path:
            print("⚖️ Phase 3: Validating...")
            grading = await asyncio.to_thread(self._grade_image, image_path)
            result["grading"] = grading
            print(f"📊 Grading Result: {grading}")
        else:
            result["grading"] = {"error": "Image generation failed"}
            
        return result

    async def _generate_strategy(self, topic: str) -> PinterestPinStrategy:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", f"Generate a high-end pin concept for the trend: {{topic}}")
        ])
        
        # Use structured output for strict JSON compliance
        structured_llm = self.model.with_structured_output(PinterestPinStrategy)
        chain = prompt | structured_llm
        
        strategy = await chain.ainvoke({"topic": topic})
        return strategy

    def _build_super_prompt(self, strategy: PinterestPinStrategy) -> str:
        gen = strategy.image_generation_prompt
        visual = strategy.visual_concept
        style = strategy.color_and_style
        
        mega_prompt = (
            f"{gen.prompt}. "
            f"Aesthetic: {visual.background_style}, {style.design_style}. "
            f"Lighting: {visual.lighting_style}. "
            f"Camera: {visual.camera_angle}. "
            f"Palette: {', '.join(style.color_palette)}."
        )
        
        tags = ", ".join(gen.quality_tags)
        final_output = f"{mega_prompt} {tags}"
        print(f"📝 Super Prompt: {final_output[:100]}...")
        return final_output

    def _generate_image(self, strategy: PinterestPinStrategy) -> str | None:
        super_prompt = self._build_super_prompt(strategy)
        encoded = quote(super_prompt)
        
        # Using gen.pollinations.ai with API key authentication
        url = f"https://gen.pollinations.ai/image/{encoded}?width=1080&height=1920&model=flux&nologo=true"
        
        headers = {}
        if settings.POLLINATION_API_KEY:
            headers["Authorization"] = f"Bearer {settings.POLLINATION_API_KEY}"
        
        try:
            print(f"📡 Requesting Image Generation (Flux)...")
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200 and len(response.content) > 1000:
                filename = f"pin_{int(time.time())}.png" # Changed to PNG for quality
                path = settings.IMAGES_DIR / filename
                with open(path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Image saved: {path} ({len(response.content)} bytes)")
                return str(path)
            else:
                print(f"❌ API Error: {response.status_code} - {response.text[:100]}")
                return self._fallback_generate(super_prompt)
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return self._fallback_generate(super_prompt)

    def _fallback_generate(self, prompt: str) -> str | None:
        encoded = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true"
        try:
            print(f"📡 Using fallback endpoint...")
            response = requests.get(url, timeout=60)
            if response.status_code == 200 and len(response.content) > 1000:
                filename = f"pin_{int(time.time())}.jpg"
                path = settings.IMAGES_DIR / filename
                with open(path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Image saved via fallback: {path}")
                return str(path)
        except Exception as e:
            print(f"❌ Fallback failed: {e}")
        return None

    def _grade_image(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            prompt = """Rank this 1-10 on Pinterest 'Scroll-Stopping' potential.
            Return JSON with keys: overall_score (int), composition (int), lighting (int), tip (max 1 sentence).
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            )
            
            # Use a separate model instance for grading if needed, or re-use self.model
            # Logic here assumes self.model is multimodal (Gemini Flash is)
            response = self.model.invoke([message])
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"overall_score": 0, "error": "Failed to parse grading JSON", "raw": content}
                
        except Exception as e:
            print(f"❌ Grading Error: {e}")
            return {"overall_score": 0, "error": str(e)}
