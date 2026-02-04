import os
import json
import time
import glob
import base64
import requests
from urllib.parse import quote
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from prompts import get_system_prompt

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

def log_to_daily_jsonl(data_object, folder="logs"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(folder, f"{date_str}_pinterest.jsonl")
    if hasattr(data_object, 'model_dump'):
        entry = data_object.model_dump()
    else:
        entry = data_object.dict()
    entry["logged_at"] = datetime.now().isoformat()
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return filename

def get_my_boards(access_token):
    url = "https://api.pinterest.com/v5/boards"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        boards = response.json().get('items', [])
        print("📋 Your Pinterest Boards:")
        for b in boards:
            print(f"Name: {b['name']} | ID: {b['id']}")
        return boards
    else:
        print(f"❌ Error: {response.json()}")
        return None

def init_gemini_client(temperature=0.7, response_mime_type=None):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        response_mime_type=response_mime_type
    )

def generate_trending_topic(client: ChatGoogleGenerativeAI):
    response = client.invoke(
           [ {
                "role": "user",
                "content": (
                    "You are a Pinterest trend analyst. "
                    "Return ONE short, high-performing Pinterest topic. "
                    "No explanation. No formatting. Just the topic."
                )
            }
           ]
    )
    return response.content.strip()

def generate_full_pin_concept(client: ChatGoogleGenerativeAI, topic: str):
    response = client.invoke([
        {"role": "user", "content": get_system_prompt()},
        {"role": "user", "content": f"Generate a high-end pin concept for the trend: {topic}"}
    ])
    return response.content.strip()

def build_super_prompt(strategy):
    gen = strategy.get('image_generation_prompt', {})
    visual = strategy.get('visual_concept', {})
    style = strategy.get('color_and_style', {})
    prompt_text = gen.get('prompt', '')
    bg_style = visual.get('background_style', '')
    design_style = style.get('design_style', '')
    lighting = visual.get('lighting_style', '')
    camera = visual.get('camera_angle', '')
    palette = ', '.join(style.get('color_palette', []))
    mega_prompt = (
        f"{prompt_text}. "
        f"Aesthetic: {bg_style}, {design_style}. "
        f"Lighting: {lighting}. "
        f"Camera: {camera}. "
        f"Palette: {palette}."
    )
    tags = ", ".join(gen.get('quality_tags', []))
    final_output = f"{mega_prompt} {tags}"
    return final_output

def get_latest_image(folder="pinterest_images"):
    if not os.path.exists(folder):
        return None
    files = glob.glob(os.path.join(folder, "*.jpg"))
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)
    return latest_file

def generate_image_with_pollinations(super_prompt, api_key=None, folder="pinterest_images"):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    encoded_prompt = quote(super_prompt)
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width=1080&height=1920&model=flux&nologo=true"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        print(f"📡 Requesting Image Generation (Flux)...")
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200 and len(response.content) > 1000:
            filename = f"pin_{int(time.time())}.jpg"
            path = os.path.join(folder, filename)
            
            with open(path, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ Image saved: {path} ({len(response.content)} bytes)")
            return path
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def grade_image_quality(image_path: str, client: ChatGoogleGenerativeAI) -> dict:
    if not image_path or not os.path.exists(image_path):
        return {"overall_score": 0, "error": "Image not found"}
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
        response = client.invoke([message])
        content = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(content)    
    except Exception as e:
        print(f"❌ Grading Error: {e}")
        return {"overall_score": 0, "error": str(e)}
