import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/souga/Project-Own/LANGCHAIN')
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from xhtml2pdf import pisa
from datetime import datetime

load_dotenv('c:/Users/souga/Project-Own/LANGCHAIN/.env')

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.7)
DATA_DIR = 'nexus_data'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(f'{DATA_DIR}/reports', exist_ok=True)

CSS = '''<style>
@page{margin:1.5cm}body{font-family:Arial;font-size:11pt;line-height:1.5;color:#333}
h1{color:#1565c0;font-size:18pt;border-bottom:3px solid #1565c0;padding-bottom:8px}
h2{color:#2e7d32;font-size:13pt;margin-top:18px}
.box{padding:12px;margin:10px 0;border-radius:4px}
.info{background:#e3f2fd;border-left:4px solid #2196f3}
.warn{background:#ffebee;border-left:4px solid #f44336}
.success{background:#e8f5e9;border-left:4px solid #4caf50}
.code{background:#263238;color:#aed581;padding:15px;font-family:Consolas;font-size:9pt;white-space:pre-wrap}
.score{background:#e8f5e9;border:2px solid #4caf50;padding:15px;text-align:center;font-size:24pt;font-weight:bold;color:#2e7d32}
table{width:100%;border-collapse:collapse;margin:10px 0}th{background:#1565c0;color:white;padding:8px;text-align:left}
td{border:1px solid #ddd;padding:8px}tr:nth-child(even){background:#f5f5f5}
</style>'''

def pdf(html, name): 
    path = f'{DATA_DIR}/reports/{name}_{datetime.now().strftime("%H%M%S")}.pdf'
    with open(path, 'wb') as f: pisa.CreatePDF(CSS + html, dest=f)
    return path

print('='*60)
print('NEXUS TEST - Testing All Modules')
print('='*60)

# Test 1: CODEX
print('\n[1/4] CODEX (Code Review)...')

class SecurityIssue(BaseModel):
    severity: str = Field(description='High, Medium, or Low')
    issue: str = Field(description='Description of the security issue')
    fix: str = Field(description='How to fix it')

class CodeReview(BaseModel):
    summary: str = Field(description='Brief summary of code quality')
    quality_score: int = Field(description='Score from 1 to 10 only', ge=1, le=10)
    security_issues: List[SecurityIssue] = Field(description='List of security vulnerabilities found')
    suggestions: List[str] = Field(description='Improvement suggestions')
    refactored_code: str = Field(description='The improved version of the code')

code = '''def login(user, pwd):
    query = f"SELECT * FROM users WHERE username='{user}' AND password='{pwd}'"
    result = db.execute(query)
    return True if result else False'''

prompt = ChatPromptTemplate.from_messages([
    ('system', '''You are CODEX, an expert code analyst.
Review code for security vulnerabilities, performance, and best practices.
IMPORTANT: quality_score must be between 1-10 (integer only).
Identify specific security issues with severity levels.'''),
    ('human', 'Review this Python code:\n```python\n{code}\n```')
])
chain = prompt | model.with_structured_output(CodeReview)
r = chain.invoke({'code': code})

print(f'  Quality: {r.quality_score}/10')
print(f'  Security Issues: {len(r.security_issues)}')
for s in r.security_issues:
    print(f'    [{s.severity}] {s.issue[:60]}')

sec_html = ''.join([f'<tr><td>{s.severity}</td><td>{s.issue}</td><td>{s.fix}</td></tr>' for s in r.security_issues])
html = f'''<h1>CODEX Code Review</h1>
<div class="score">{r.quality_score}/10</div>
<h2>Summary</h2><p>{r.summary}</p>
<h2>Security Issues</h2><table><tr><th>Severity</th><th>Issue</th><th>Fix</th></tr>{sec_html}</table>
<h2>Suggestions</h2><ul>{''.join([f'<li>{s}</li>' for s in r.suggestions])}</ul>
<h2>Refactored Code</h2><div class="code">{r.refactored_code.replace('<', '&lt;').replace('>', '&gt;')}</div>'''
print(f'  PDF: {pdf(html, "codex_review")}')

# Test 2: SHERLOCK
print('\n[2/4] SHERLOCK (Debug)...')

class DebugAnalysis(BaseModel):
    error_type: str = Field(description='Type of error (e.g., RecursionError, TypeError)')
    root_cause: str = Field(description='Detailed explanation of why the error occurred')
    fix_explanation: str = Field(description='How to fix the issue')
    fixed_code: str = Field(description='The corrected code')
    confidence: int = Field(description='Confidence level 1-100', ge=1, le=100)

prompt = ChatPromptTemplate.from_messages([
    ('system', '''You are SHERLOCK, a debugging detective.
Analyze code errors, identify root causes, and provide fixes.
Be thorough in your analysis.'''),
    ('human', 'Debug this code:\n```python\n{code}\n```\nError: {error}')
])
chain = prompt | model.with_structured_output(DebugAnalysis)
r = chain.invoke({'code': 'def factorial(n):\n    return n * factorial(n-1)', 'error': 'RecursionError: maximum recursion depth exceeded'})

print(f'  Error: {r.error_type}')
print(f'  Cause: {r.root_cause[:70]}...')
print(f'  Confidence: {r.confidence}%')

html = f'''<h1>SHERLOCK Debug Report</h1>
<div class="box warn"><h2>Error: {r.error_type}</h2></div>
<h2>Root Cause</h2><div class="box info">{r.root_cause}</div>
<h2>Fix</h2><p>{r.fix_explanation}</p>
<h2>Corrected Code</h2><div class="code">{r.fixed_code.replace('<', '&lt;').replace('>', '&gt;')}</div>
<div class="score">Confidence: {r.confidence}%</div>'''
print(f'  PDF: {pdf(html, "sherlock_debug")}')

# Test 3: ATLAS
print('\n[3/4] ATLAS (System Design)...')

class Component(BaseModel):
    name: str = Field(description='Component name (e.g., API Gateway, Message Queue)')
    purpose: str = Field(description='What this component does')
    technology: str = Field(description='Suggested technology (e.g., Redis, PostgreSQL)')

class SystemDesign(BaseModel):
    overview: str = Field(description='High-level system overview')
    components: List[Component] = Field(description='List of system components')
    scalability: List[str] = Field(description='Scalability considerations')

prompt = ChatPromptTemplate.from_messages([
    ('system', '''You are ATLAS, a system design expert.
Design scalable, production-ready architectures.
Include specific technologies for each component.'''),
    ('human', 'Design a system for: {requirements}')
])
chain = prompt | model.with_structured_output(SystemDesign)
r = chain.invoke({'requirements': 'Real-time chat application with 100K concurrent users'})

print(f'  Components: {len(r.components)}')
for c in r.components[:4]:
    print(f'    - {c.name}: {c.technology}')

comps = ''.join([f'<tr><td>{c.name}</td><td>{c.purpose}</td><td>{c.technology}</td></tr>' for c in r.components])
html = f'''<h1>ATLAS System Design</h1>
<h2>Overview</h2><p>{r.overview}</p>
<h2>Components</h2><table><tr><th>Component</th><th>Purpose</th><th>Technology</th></tr>{comps}</table>
<h2>Scalability</h2><ul>{''.join([f'<li>{s}</li>' for s in r.scalability])}</ul>'''
print(f'  PDF: {pdf(html, "atlas_design")}')

# Test 4: SOCRATES
print('\n[4/4] SOCRATES (Interview)...')

class InterviewQuestion(BaseModel):
    question: str = Field(description='The interview question')
    category: str = Field(description='Category: behavioral, technical, or situational')
    difficulty: str = Field(description='Easy, Medium, or Hard')

class MockInterview(BaseModel):
    role: str = Field(description='Job role')
    questions: List[InterviewQuestion] = Field(description='Interview questions')
    tips: List[str] = Field(description='Tips for the interviewee')

prompt = ChatPromptTemplate.from_messages([
    ('system', '''You are SOCRATES, an expert interview coach.
Generate realistic interview questions for the specified role.
Include a mix of behavioral and technical questions.'''),
    ('human', 'Create a mock interview for: {role}')
])
chain = prompt | model.with_structured_output(MockInterview)
r = chain.invoke({'role': 'Senior Software Engineer'})

print(f'  Role: {r.role}')
print(f'  Questions: {len(r.questions)}')
for q in r.questions[:3]:
    print(f'    [{q.category}] {q.question[:50]}...')

qs = ''.join([f'<div class="box info"><h3>{q.question}</h3><p>Category: {q.category} | Difficulty: {q.difficulty}</p></div>' for q in r.questions])
html = f'''<h1>SOCRATES Mock Interview</h1>
<h2>Role: {r.role}</h2>
{qs}
<h2>Tips</h2><div class="box success"><ul>{''.join([f'<li>{t}</li>' for t in r.tips])}</ul></div>'''
print(f'  PDF: {pdf(html, "socrates_interview")}')

print('\n' + '='*60)
print('ALL TESTS COMPLETE!')
print('='*60)
print(f'\nPDFs in: {os.path.abspath(DATA_DIR)}/reports/')
