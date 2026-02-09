import os
import time
import json
import requests
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.config import settings

# --- Data Models from brain.ipynb ---

class VideoExecutorStrategy(BaseModel):
    video_prompt: str = Field(
        ..., 
        description="Detailed cinematic description for Veo 3.1 including camera movement and lighting."
    )
    motion_bucket_id: int = Field(
        default=85, 
        ge=1, le=255, 
        description="Motion intensity: 1 for static, 255 for extreme movement."
    )
    audio_prompt: str = Field(
        ..., 
        description="Description of the native audio soundscape (ambient sounds, music, foley)."
    )
    overlay_text: str = Field(
        ..., 
        description="The hook/headline text to be displayed on the video."
    )
    aspect_ratio: str = Field(
        default="9:16", 
        description="The frame dimensions (e.g., 9:16 for vertical, 16:9 for wide)."
    )
    video_title: str = Field(..., description="Optimized title for the video post.")
    tags: List[str] = Field(default_factory=list, description="List of 5 relevant SEO hashtags.")

# --- System Prompt from brain.ipynb ---

SYSTEM_PROMPT = """
You are an expert AI Cinematographer and Sound Designer. Your role is to take a creative strategy and translate it into precise technical instructions for Google Veo 3.1.

Instructions for Scene Generation:
Camera Movement: Always specify a camera motion (e.g., 'dolly-in', 'slow orbit', 'low-angle tilt').
Cinematic Lighting: Use professional lighting terms (e.g., 'volumetric fog', 'rim lighting', 'soft-box diffusion').
Soundscape Logic: Describe sounds that match the visual actions for Veo's native audio engine.

Output (Strict JSON):
{{
  "veo_prompt": "A detailed, 1-paragraph cinematic description of the scene including camera movement and lighting.",
  "motion_bucket_id": 85,
  "audio_description": "A specific description of the ambient and foley sounds.",
  "video_metadata": {{
    "resolution": "1080p",
    "aspect_ratio": "9:16",
    "fps": 24
  }}
}}
"""

class VideoGenAgent(BaseAgent):
    name = "video_gen"
    description = "Generate cinematic AI videos using Replicate (Minimax/Veo) with detailed prompts"
    icon = "🎥"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        # 1. Generate Strategy
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{topic}")
        ])
        
        structured_model = self.model.with_structured_output(VideoExecutorStrategy)
        chain = prompt | structured_model
        
        print(f"🎥 Generating video strategy for: {topic}")
        strategy = await self._safe_invoke(chain, {"topic": topic})
        
        print(f"🎬 Title: {strategy.video_title}")
        print(f"📝 Overlay: {strategy.overlay_text}")
        print(f"🎥 Prompt: {strategy.video_prompt[:100]}...")
        
        # 2. Generate Video using Replicate
        try:
            # Run blocking Replicate call in thread
            video_url = await asyncio.to_thread(self._generate_video_replicate, strategy.video_prompt)
            # 3. Download Video (blocking I/O)
            video_path = await asyncio.to_thread(self._download_video, video_url)
            
            return {
                "strategy": strategy.model_dump(),
                "video_url": video_url,
                "output_file": video_path
            }
        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            return {
                "strategy": strategy.model_dump(),
                "error": str(e)
            }
    
    def _generate_video_replicate(self, prompt: str) -> str:
        # Require Replicate API Token
        api_token = os.environ.get("REPLICATE_API_TOKEN") or getattr(settings, "REPLICATE_API_TOKEN", None)
        if not api_token:
            raise ValueError("Missing REPLICATE_API_TOKEN")
        
        import replicate
        
        print(f"🎬 Starting video generation on Replicate (minimax/video-01)...")
        # Ensure client is configured if needed, or environment variable handles it
        
        prediction = replicate.predictions.create(
            model="minimax/video-01",
            input={
                "prompt": prompt,
                "prompt_optimizer": True
            }
        )
        
        print(f"⏳ Waiting for video... (ID: {prediction.id})")
        prediction.wait()
        
        if prediction.status == "succeeded":
            print(f"✅ Video generated!")
            return str(prediction.output)
        else:
            raise Exception(f"Generation failed: {prediction.error}")
            
    def _download_video(self, video_url: str) -> str:
        output_dir = settings.DATA_DIR / "videos"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_filename = f"{timestamp}_video.mp4"
        video_path = output_dir / video_filename
        
        print(f"📥 Downloading video...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"💾 Video saved to: {video_path}")
        return str(video_path)
