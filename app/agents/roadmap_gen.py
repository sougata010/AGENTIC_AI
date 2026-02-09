import os
import time
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.config import settings

# --- Data Models from brain.ipynb ---

class YouTubeResource(BaseModel):
    video_title: str = Field(description="Title of the YouTube video")
    channel_name: str = Field(description="Name of the YouTube channel")
    duration: str = Field(description="Video duration (e.g., '45 mins', '2 hours')")
    url: str = Field(description="Full YouTube URL")

class Book(BaseModel):
    title: str = Field(description="Book title")
    author: str = Field(description="Author name")
    focus_area: str = Field(description="What the book covers or focuses on")

class Project(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="Brief project description")
    deliverables: List[str] = Field(description="Expected deliverables from the project")

class Week(BaseModel):
    week_number: int = Field(description="Week number (1, 2, 3, etc.)")
    theme: str = Field(description="Main theme or focus area for this week")
    hours_per_day: int = Field(description="Recommended hours of study per day")
    topics: List[str] = Field(description="List of topics to cover this week")
    youtube_resources: List[YouTubeResource] = Field(description="YouTube videos for learning")
    books: List[Book] = Field(description="Recommended books for this week")
    goals: List[str] = Field(description="Weekly learning goals/checkpoints")
    projects: List[Project] = Field(description="Hands-on projects for practice")

class LearningRoadmap(BaseModel):
    title: str = Field(description="Roadmap title (e.g., 'Web Development Roadmap')")
    topic: str = Field(description="Main topic/skill being learned")
    total_weeks: int = Field(description="Total duration in weeks")
    difficulty_level: str = Field(description="Beginner, Intermediate, or Advanced")
    weekly_commitment_hours: int = Field(description="Total hours per week recommended")
    prerequisites: List[str] = Field(description="Required prior knowledge or skills")
    weeks: List[Week] = Field(description="Week-by-week breakdown of the learning path")
    skills_acquired: List[str] = Field(description="Skills you'll gain after completion")
    next_steps: List[str] = Field(description="Recommended next steps after finishing")

# --- System Prompt from brain.ipynb ---

SYSTEM_PROMPT = """ You are an expert curriculum designer and learning path architect. Your task is to create comprehensive, week-by-week learning roadmaps that are perfectly formatted for PDF/document generation.

### Output Format Requirements:
1. **Document Structure:**
   - Title: "Learning Roadmap: [Topic]"
   - Duration: Total weeks
   - Difficulty Level: Beginner/Intermediate/Advanced
   - Prerequisites (if any)

2. **Weekly Breakdown Format:**
   For each week, use this EXACT structure:
   ---
   ## Week [Number]: [Week Theme/Focus Area]
   **Duration:** 7 days | **Effort:** [X] hours/day
   ### 📚 Topics Covered:
   - Topic 1
   - Topic 2
   - Topic 3
   ### 🎥 YouTube Resources:
   | Video Title | Channel | Duration | Link |
   |-------------|---------|----------|------|
   | [Title] | [Channel Name] | [Duration] | [Full URL] |
   ### 📖 Recommended Books:
   | Book Title | Author | Focus Area |
   |------------|--------|------------|
   | [Title] | [Author] | [What it covers] |
   ### ✅ Weekly Goals:
   - [ ] Goal 1
   - [ ] Goal 2
   - [ ] Goal 3
   ### 🛠️ Practice Projects:
   - Project description with clear deliverables
   ---

3. **Formatting Rules:**
   - Use consistent spacing (one blank line between sections)
   - Use horizontal rules (---) to separate weeks
   - Use tables for resources (ensures alignment)
   - Use emojis sparingly for visual markers
   - Keep bullet points concise (max 1-2 lines each)
   - Include FULL YouTube URLs (not shortened)
   - Add estimated time for each resource

4. **Content Guidelines:**
   - Start with fundamentals, progress to advanced
   - Include both free and paid resources
   - Recommend 2-3 YouTube videos per week (quality over quantity)
   - Suggest 1-2 books per week (not overwhelming)
   - Include practical projects for hands-on learning
   - Add milestone checkpoints every 2-3 weeks

5. **End Summary:**
   - Total resources covered
   - Skills acquired
   - Next steps after completion
   - Portfolio projects completed

### Example Response Structure:
# Learning Roadmap: [User Topic]
**Total Duration:** X Weeks | **Level:** [Level] | **Weekly Commitment:** X hours
## Prerequisites:
- Prerequisite 1
- Prerequisite 2
---
## Week 1: [Foundation Theme]
[Continue with the weekly format above...]
---
## Final Summary
[Summarize the complete journey]"""

class RoadmapGenAgent(BaseAgent):
    name = "roadmap_gen"
    description = "Create structured learning roadmaps with resources, videos, and projects"
    icon = "🗺️"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Create a learning roadmap for: {topic}")
        ])
        
        structure_llm = self.model.with_structured_output(LearningRoadmap)
        chain = prompt | structure_llm
        
        print(f"🗺️ Generating roadmap for: {topic}")
        roadmap = await chain.ainvoke({"topic": topic})
        
        paths = await asyncio.to_thread(self._save_roadmap, roadmap)
        
        return {
            "roadmap": roadmap.model_dump(),
            "output_file": paths.get("pdf_path")
        }
    
    def _roadmap_to_markdown(self, roadmap: LearningRoadmap) -> str:
        md = f"# {roadmap.title}\n\n"
        md += f"**Duration:** {roadmap.total_weeks} Weeks | **Level:** {roadmap.difficulty_level} | **Weekly Effort:** {roadmap.weekly_commitment_hours} hours\n\n"
        
        md += "## Prerequisites\n"
        for prereq in roadmap.prerequisites:
            md += f"- {prereq}\n"
        md += "\n---\n\n"
        
        for week in roadmap.weeks:
            md += f"## Week {week.week_number}: {week.theme}\n"
            md += f"**Effort:** {week.hours_per_day} hours/day\n\n"
            
            md += "### 📚 Topics\n"
            for topic in week.topics:
                md += f"- {topic}\n"
            
            md += "\n### 🎥 YouTube Resources\n"
            md += "| Video | Channel | Duration | Link |\n|-------|---------|----------|------|\n"
            for yt in week.youtube_resources:
                md += f"| {yt.video_title} | {yt.channel_name} | {yt.duration} | [Watch]({yt.url}) |\n"
            
            md += "\n### 📖 Books\n"
            md += "| Title | Author | Focus |\n|-------|--------|-------|\n"
            for book in week.books:
                md += f"| {book.title} | {book.author} | {book.focus_area} |\n"
            
            md += "\n### ✅ Goals\n"
            for goal in week.goals:
                md += f"- [ ] {goal}\n"
            
            md += "\n### 🛠️ Projects\n"
            for proj in week.projects:
                md += f"**{proj.name}:** {proj.description}\n"
            
            md += "\n---\n\n"
        
        md += "## Skills Acquired\n"
        for skill in roadmap.skills_acquired:
            md += f"- {skill}\n"
        
        md += "\n## Next Steps\n"
        for step in roadmap.next_steps:
            md += f"- {step}\n"
        
        return md

    def _save_roadmap(self, roadmap: LearningRoadmap) -> Dict[str, str]:
        # Generate filenames
        ts = int(time.time())
        topic_clean = re.sub(r'[^\w\s-]', '', roadmap.topic).replace(' ', '_').lower()
        filename_base = f"{topic_clean}_{ts}"
        
        md_filename = f"{filename_base}_roadmap.md"
        pdf_filename = f"{filename_base}_roadmap.pdf"
        
        md_path = settings.ROADMAPS_DIR / md_filename
        pdf_path = settings.ROADMAPS_DIR / pdf_filename
        
        # 1. Save Markdown
        markdown_content = self._roadmap_to_markdown(roadmap)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Saved Markdown: {md_path}")
        
        # 2. Save PDF using xhtml2pdf
        try:
            import markdown
            from xhtml2pdf import pisa
            
            html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
            styled_html = f'''<!DOCTYPE html>
            <html><head><meta charset="UTF-8"><style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; padding: 20px; line-height: 1.5; font-size: 11px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 20px; }}
            h2 {{ color: #34495e; font-size: 16px; margin-top: 20px; }}
            h3 {{ color: #7f8c8d; font-size: 13px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9px; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            hr {{ border: none; border-top: 1px solid #ecf0f1; margin: 20px 0; }}
            ul {{ margin: 8px 0; padding-left: 20px; }}
            li {{ margin: 3px 0; }}
            </style></head><body>{html_content}</body></html>'''
            
            with open(pdf_path, "w+b") as pdf_file:
                pisa.CreatePDF(styled_html, dest=pdf_file)
            print(f"Saved PDF: {pdf_path}")
            
            return {"md_path": str(md_path), "pdf_path": str(pdf_path)}
            
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            return {"md_path": str(md_path)}
