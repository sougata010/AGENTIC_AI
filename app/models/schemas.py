from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentRequest(BaseModel):
    topic: str = Field(..., description="Main topic or input for the agent")
    options: dict = Field(default_factory=dict, description="Additional options")

class AgentResponse(BaseModel):
    success: bool
    agent: str
    result: dict
    output_file: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

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

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class Quiz(BaseModel):
    title: str
    topic: str
    questions: List[QuizQuestion]
    difficulty: str

class RoadmapStep(BaseModel):
    title: str
    description: str
    resources: List[str]
    duration: str

class Roadmap(BaseModel):
    title: str
    topic: str
    steps: List[RoadmapStep]
    total_duration: str

class SecurityIssue(BaseModel):
    severity: str = Field(description="High, Medium, or Low")
    issue: str
    fix: str

class CodeReview(BaseModel):
    summary: str
    quality_score: int = Field(ge=1, le=10)
    security_issues: List[SecurityIssue]
    suggestions: List[str]
    refactored_code: str

class DebugAnalysis(BaseModel):
    error_type: str
    root_cause: str
    fix_explanation: str
    fixed_code: str
    confidence: int = Field(ge=1, le=100)
