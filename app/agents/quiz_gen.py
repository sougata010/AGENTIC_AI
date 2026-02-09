import os
import time
import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.config import settings

# --- Data Models from brain.ipynb ---

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_in_the_blank"
    SHORT_ANSWER = "short_answer"

class Option(BaseModel):
    label: str = Field(description="Option label (A, B, C, D)")
    text: str = Field(description="Option text")
    is_correct: bool = Field(description="Whether this is the correct answer")

class Question(BaseModel):
    question_number: int = Field(description="Question number")
    question_type: QuestionType = Field(description="Type of question")
    question_text: str = Field(description="The question")
    options: Optional[List[Option]] = Field(description="Options for MCQ/True-False")
    correct_answer: str = Field(description="Correct answer text")
    explanation: str = Field(description="Why this is the correct answer")
    difficulty: DifficultyLevel = Field(description="Question difficulty")
    topic_tag: str = Field(description="Topic this question covers")

class Quiz(BaseModel):
    title: str = Field(description="Quiz title")
    topic: str = Field(description="Main topic")
    total_questions: int = Field(description="Total number of questions")
    time_limit_minutes: int = Field(description="Suggested time to complete")
    difficulty_distribution: dict = Field(description="Count of easy/medium/hard")
    questions: List[Question] = Field(description="List of questions")
    passing_score: int = Field(description="Minimum score to pass (percentage)")

# --- System Prompt from brain.ipynb ---

SYSTEM_PROMPT = """You are an expert quiz designer and educational assessment specialist. Your task is to create high-quality, well-structured quizzes that effectively test knowledge and understanding.

### Quiz Design Principles:
1. **Question Quality:**
   - Clear, unambiguous wording
   - One correct answer per question (for MCQ)
   - Plausible distractors that test real understanding
   - No trick questions or misleading phrasing

2. **Difficulty Distribution:**
   - Easy (30%): Direct recall, basic concepts
   - Medium (50%): Application, understanding relationships
   - Hard (20%): Analysis, synthesis, edge cases

3. **Question Types to Include:**
   - MCQ: 4 options (A, B, C, D), only one correct
   - True/False: Clear statements, no ambiguity
   - Fill in the Blank: Key terms and concepts

4. **Answer Explanations:**
   - Explain WHY the correct answer is right
   - Briefly explain why wrong options are incorrect
   - Reference key concepts for learning reinforcement

5. **Coverage Rules:**
   - Cover all major subtopics evenly
   - Progress from fundamental to advanced
   - Include real-world application questions
   - Test both theoretical knowledge and practical understanding

6. **Formatting Requirements:**
   - Number questions sequentially
   - Tag each question with its topic area
   - Specify difficulty level per question
   - Keep questions concise (max 2 sentences)
   - Keep options brief (max 1 sentence each)

### Output Structure:
For each question, provide:
- Question number and type
- Question text
- Options (for MCQ/True-False)
- Correct answer
- Detailed explanation
- Difficulty level
- Topic tag"""

class QuizGenAgent(BaseAgent):
    name = "quiz_gen"
    description = "Generate educational quizzes with multiple choice questions, PDFs, and explanations"
    icon = "📝"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Create a quiz on: {topic}")
        ])
        
        structured_model = self.model.with_structured_output(Quiz)
        chain = prompt | structured_model
        
        print(f"📝 Generating quiz for: {topic}")
        quiz = await self._safe_invoke(chain, {"topic": topic})
        
        # Save as Markdown and PDF
        paths = await asyncio.to_thread(self._save_quiz, quiz)
        
        return {
            "quiz": quiz.model_dump(),
            "output_file": paths.get("pdf_path")
        }
    
    def _quiz_to_markdown(self, quiz: Quiz) -> str:
        md = f"# {quiz.title}\n\n"
        md += f"**Topic:** {quiz.topic} | **Questions:** {quiz.total_questions} | **Time:** {quiz.time_limit_minutes} mins | **Passing:** {quiz.passing_score}%\n\n"
        md += "---\n\n"
        
        for q in quiz.questions:
            md += f"### Q{q.question_number}. {q.question_text}\n"
            md += f"*Difficulty: {q.difficulty.value} | Topic: {q.topic_tag}*\n\n"
            
            if q.options:
                for opt in q.options:
                    md += f"- **{opt.label})** {opt.text}\n"
            
            md += f"\n**Answer:** {q.correct_answer}\n\n"
            md += f"**Explanation:** {q.explanation}\n\n"
            md += "---\n\n"
        
        return md

    def _save_quiz(self, quiz: Quiz) -> Dict[str, str]:
        # Generate filenames
        ts = int(time.time())
        topic_clean = re.sub(r'[^\w\s-]', '', quiz.topic).replace(' ', '_').lower()
        filename_base = f"{topic_clean}_{ts}"
        
        md_filename = f"{filename_base}_quiz.md"
        pdf_filename = f"{filename_base}_quiz.pdf"
        
        md_path = settings.QUIZZES_DIR / md_filename
        pdf_path = settings.QUIZZES_DIR / pdf_filename
        
        # 1. Save Markdown
        markdown_content = self._quiz_to_markdown(quiz)
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
            h1 {{ color: #2c3e50; border-bottom: 2px solid #9b59b6; padding-bottom: 8px; font-size: 22px; }}
            h3 {{ color: #8e44ad; font-size: 13px; margin-top: 15px; }}
            strong {{ color: #2c3e50; }}
            hr {{ border: none; border-top: 1px solid #ecf0f1; margin: 15px 0; }}
            ul {{ margin: 8px 0; padding-left: 20px; }}
            li {{ margin: 5px 0; }}
            em {{ color: #7f8c8d; font-size: 10px; }}
            .correct {{ color: #27ae60; font-weight: bold; }}
            </style></head><body>{html_content}</body></html>'''
            
            with open(pdf_path, "w+b") as pdf_file:
                pisa.CreatePDF(styled_html, dest=pdf_file)
            print(f"Saved PDF: {pdf_path}")
            
            return {"md_path": str(md_path), "pdf_path": str(pdf_path)}
            
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            # Return MD path at least
            return {"md_path": str(md_path)}
