import os
import json
import hashlib
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from xhtml2pdf import pisa
from dotenv import load_dotenv

from app.agents.base import BaseAgent
from app.config import settings

# Ensure environment variables are loaded (BaseAgent handled it, but good to be safe)
load_dotenv()

# --- Configuration & Setup ---

DATA_DIR = settings.DATA_DIR / "nexus_data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DATA_DIR / "reports", exist_ok=True)
os.makedirs(DATA_DIR / "knowledge", exist_ok=True)

CSS = '''<style>
@page{margin:1.5cm}body{font-family:Arial;font-size:11pt;line-height:1.5;color:#333}
h1{color:#1565c0;font-size:18pt;border-bottom:3px solid #1565c0;padding-bottom:8px}
h2{color:#2e7d32;font-size:13pt;margin-top:18px}h3{color:#6a1b9a;font-size:11pt}
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
    path = DATA_DIR / f'reports/{name}_{datetime.now().strftime("%H%M%S")}.pdf'
    with open(path, 'wb') as f: pisa.CreatePDF(CSS + html, dest=f)
    print(f'PDF: {path}')
    return str(path)

# --- 1. ARIA (Research) ---

class Contribution(BaseModel):
    title: str = Field(description='Contribution title')
    description: str = Field(description='Detailed description')

class PaperAnalysis(BaseModel):
    title: str = Field(description='Paper title')
    authors: List[str] = Field(description='List of author names')
    summary: str = Field(description='Abstract summary in 2-3 sentences')
    contributions: List[Contribution] = Field(description='Key contributions')
    methodology: str = Field(description='Research methodology used')
    findings: List[str] = Field(description='Main findings')
    limitations: List[str] = Field(description='Study limitations')
    relevance_score: int = Field(description='1-10 relevance score', ge=1, le=10)

class Theme(BaseModel):
    name: str = Field(description='Theme name')
    description: str = Field(description='Theme description')

class LiteratureReview(BaseModel):
    topic: str = Field(description='Review topic')
    overview: str = Field(description='Field overview')
    themes: List[Theme] = Field(description='Major research themes')
    gaps: List[str] = Field(description='Research gaps identified')
    future_directions: List[str] = Field(description='Future research directions')

class ResearchQuestion(BaseModel):
    question: str = Field(description='Research question')
    hypothesis: str = Field(description='Proposed hypothesis')
    methodology: str = Field(description='Suggested methodology')
    contribution: str = Field(description='Expected contribution')
    feasibility: int = Field(description='1-10 feasibility', ge=1, le=10)

ARIA_PROMPT = '''Role: Academic Research Expert.
Analyze content with rigor. ID contributions, methods, findings, limitations.
Output strict JSON.'''

class ARIA:
    def __init__(self, model):
        self.model = model

    async def analyze(self, content: str) -> PaperAnalysis:
        prompt = ChatPromptTemplate.from_messages([('system', ARIA_PROMPT), ('human', 'Analyze this paper:\n{content}')])
        chain = prompt | self.model.with_structured_output(PaperAnalysis)
        r = await self._safe_invoke(chain, {"content": content[:8000]})
        contribs = ''.join([f'<tr><td>{c.title}</td><td>{c.description}</td></tr>' for c in r.contributions])
        html = f'''<h1>Paper Analysis: {r.title}</h1>
        <div class="box info"><strong>Authors:</strong> {', '.join(r.authors)}</div>
        <h2>Summary</h2><p>{r.summary}</p>
        <h2>Contributions</h2><table><tr><th>Contribution</th><th>Description</th></tr>{contribs}</table>
        <h2>Methodology</h2><p>{r.methodology}</p>
        <h2>Findings</h2><ul>{''.join([f'<li>{f}</li>' for f in r.findings])}</ul>
        <h2>Limitations</h2><div class="box warn"><ul>{''.join([f'<li>{l}</li>' for l in r.limitations])}</ul></div>
        <div class="score">{r.relevance_score}/10</div>'''
        print(f'Paper: {r.title} | Relevance: {r.relevance_score}/10')
        pdf_path = await asyncio.to_thread(pdf, html, 'paper_analysis')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def review(self, topic: str, context: str = '') -> LiteratureReview:
        prompt = ChatPromptTemplate.from_messages([('system', ARIA_PROMPT), ('human', 'Create literature review for: {topic}\nContext: {context}')])
        chain = prompt | self.model.with_structured_output(LiteratureReview)
        r = await self._safe_invoke(chain, {"topic": topic, "context": context})
        themes = ''.join([f'<div class="box info"><h3>{t.name}</h3><p>{t.description}</p></div>' for t in r.themes])
        html = f'''<h1>Literature Review: {topic}</h1>
        <h2>Overview</h2><p>{r.overview}</p>
        <h2>Major Themes</h2>{themes}
        <h2>Research Gaps</h2><div class="box warn"><ul>{''.join([f'<li>{g}</li>' for g in r.gaps])}</ul></div>
        <h2>Future Directions</h2><div class="box success"><ul>{''.join([f'<li>{d}</li>' for d in r.future_directions])}</ul></div>'''
        print(f'Review: {topic} | Gaps: {len(r.gaps)}')
        pdf_path = await asyncio.to_thread(pdf, html, 'lit_review')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def questions(self, topic: str, gap: str) -> List[ResearchQuestion]:
        prompt = ChatPromptTemplate.from_messages([('system', ARIA_PROMPT), ('human', 'Generate 3 research questions for gap: {gap} in topic: {topic}')])
        chain = prompt | self.model.with_structured_output(List[ResearchQuestion])
        qs = await self._safe_invoke(chain, {"topic": topic, "gap": gap})
        html = f'<h1>Research Questions: {topic}</h1><p>Gap: {gap}</p>'
        for i, q in enumerate(qs, 1):
            html += f'''<div class="box info"><h2>RQ{i}: {q.question}</h2>
            <p><strong>Hypothesis:</strong> {q.hypothesis}</p>
            <p><strong>Method:</strong> {q.methodology}</p>
            <p><strong>Contribution:</strong> {q.contribution}</p>
            <p>Feasibility: {q.feasibility}/10</p></div>'''
        print(f'Generated {len(qs)} research questions')
        pdf_path = await asyncio.to_thread(pdf, html, 'research_questions')
        return {"data": qs, "pdf": str(pdf_path)}

# --- 2. CODEX (Code) ---

class SecurityIssue(BaseModel):
    severity: str = Field(description='High, Medium, or Low')
    issue: str = Field(description='Description of the vulnerability')
    fix: str = Field(description='How to fix it')

class PerformanceIssue(BaseModel):
    issue: str = Field(description='Performance problem')
    impact: str = Field(description='Impact on performance')
    fix: str = Field(description='Optimization suggestion')

class CodeReview(BaseModel):
    summary: str = Field(description='Brief code quality summary')
    quality_score: int = Field(description='1-10 quality score', ge=1, le=10)
    security_issues: List[SecurityIssue] = Field(description='Security vulnerabilities')
    performance_issues: List[PerformanceIssue] = Field(description='Performance issues')
    suggestions: List[str] = Field(description='Improvement suggestions')
    refactored_code: str = Field(description='Improved code version')

class Vulnerability(BaseModel):
    vuln_type: str = Field(description='Vulnerability type (e.g., SQL Injection)')
    severity: str = Field(description='Critical, High, Medium, or Low')
    description: str = Field(description='Vulnerability description')
    cwe: str = Field(description='CWE reference (e.g., CWE-89)')

class SecurityAudit(BaseModel):
    risk_level: str = Field(description='Overall risk: Critical, High, Medium, Low')
    vulnerabilities: List[Vulnerability] = Field(description='Found vulnerabilities')
    remediation: List[str] = Field(description='Steps to fix')
    secure_code: str = Field(description='Secure implementation')

CODEX_PROMPT = '''Role: Senior Code Reviewer.
Analyze security, performance, maintainability. Reference CWE/OWASP.
Scores 1-10. Output strict JSON.'''

class CODEX:
    def __init__(self, model):
        self.model = model

    async def review(self, code: str, language: str = 'python') -> CodeReview:
        prompt = ChatPromptTemplate.from_messages([('system', CODEX_PROMPT), ('human', 'Review this {lang} code:\n```{lang}\n{code}\n```')])
        chain = prompt | self.model.with_structured_output(CodeReview)
        r = await self._safe_invoke(chain, {"code": code, "lang": language})
        sec_html = ''.join([f'<tr><td>{s.severity}</td><td>{s.issue}</td><td>{s.fix}</td></tr>' for s in r.security_issues])
        perf_html = ''.join([f'<tr><td>{p.issue}</td><td>{p.impact}</td><td>{p.fix}</td></tr>' for p in r.performance_issues])
        html = f'''<h1>CODEX Code Review</h1>
        <div class="score">{r.quality_score}/10</div>
        <h2>Summary</h2><p>{r.summary}</p>
        <h2>Security Issues</h2><table><tr><th>Severity</th><th>Issue</th><th>Fix</th></tr>{sec_html or '<tr><td colspan="3">None</td></tr>'}</table>
        <h2>Performance Issues</h2><table><tr><th>Issue</th><th>Impact</th><th>Fix</th></tr>{perf_html or '<tr><td colspan="3">None</td></tr>'}</table>
        <h2>Suggestions</h2><ul>{''.join([f'<li>{s}</li>' for s in r.suggestions])}</ul>
        <h2>Refactored Code</h2><div class="code">{r.refactored_code.replace('<', '&lt;').replace('>', '&gt;')}</div>'''
        print(f'Quality: {r.quality_score}/10 | Security: {len(r.security_issues)} issues')
        pdf_path = await asyncio.to_thread(pdf, html, 'code_review')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def audit(self, code: str) -> SecurityAudit:
        prompt = ChatPromptTemplate.from_messages([('system', CODEX_PROMPT), ('human', 'Security audit:\n```\n{code}\n```')])
        chain = prompt | self.model.with_structured_output(SecurityAudit)
        r = await self._safe_invoke(chain, {"code": code})
        vulns = ''.join([f'<tr><td>{v.vuln_type}</td><td>{v.severity}</td><td>{v.description}</td><td>{v.cwe}</td></tr>' for v in r.vulnerabilities])
        html = f'''<h1>Security Audit</h1>
        <div class="box {'warn' if r.risk_level in ['High', 'Critical'] else 'info'}"><h2>Risk: {r.risk_level}</h2></div>
        <h2>Vulnerabilities</h2><table><tr><th>Type</th><th>Severity</th><th>Description</th><th>CWE</th></tr>{vulns or '<tr><td colspan="4">None</td></tr>'}</table>
        <h2>Remediation</h2><ol>{''.join([f'<li>{s}</li>' for s in r.remediation])}</ol>
        <h2>Secure Code</h2><div class="code">{r.secure_code.replace('<', '&lt;').replace('>', '&gt;')}</div>'''
        print(f'Risk: {r.risk_level} | Vulns: {len(r.vulnerabilities)}')
        pdf_path = await asyncio.to_thread(pdf, html, 'security_audit')
        return {"data": r, "pdf": str(pdf_path)}

# --- 3. SOCRATES (Interview) ---

class STARResponse(BaseModel):
    question_type: str = Field(description='behavioral, technical, or situational')
    situation: str = Field(description='STAR Situation extracted')
    task: str = Field(description='STAR Task extracted')
    action: str = Field(description='STAR Action extracted')
    result: str = Field(description='STAR Result extracted')
    improved_answer: str = Field(description='Better version of the answer')
    score: int = Field(description='1-10 answer quality', ge=1, le=10)
    feedback: str = Field(description='Improvement feedback')
    followups: List[str] = Field(description='Likely follow-up questions')

class InterviewQuestion(BaseModel):
    question: str = Field(description='Interview question')
    category: str = Field(description='behavioral, technical, or situational')
    difficulty: str = Field(description='Easy, Medium, or Hard')
    what_to_assess: str = Field(description='What this question evaluates')

class MockInterview(BaseModel):
    role: str = Field(description='Job role')
    questions: List[InterviewQuestion] = Field(description='Interview questions')
    tips: List[str] = Field(description='Interview tips')

SOCRATES_PROMPT = '''Role: Interview Coach.
Use STAR method. specific feedback. Scores 1-10.
Output strict JSON.'''

class SOCRATES:
    def __init__(self, model):
        self.model = model

    async def evaluate(self, question: str, answer: str) -> STARResponse:
        prompt = ChatPromptTemplate.from_messages([('system', SOCRATES_PROMPT), ('human', 'Question: {question}\nAnswer: {answer}\nEvaluate using STAR.')])
        chain = prompt | self.model.with_structured_output(STARResponse)
        r = await self._safe_invoke(chain, {"question": question, "answer": answer})
        html = f'''<h1>Interview Evaluation</h1>
        <h2>Question</h2><div class="box info">{question}</div>
        <div class="score">{r.score}/10</div>
        <h2>Your Answer</h2><p>{answer}</p>
        <h2>STAR Analysis</h2><table>
        <tr><th>Component</th><th>Your Response</th></tr>
        <tr><td>Situation</td><td>{r.situation}</td></tr>
        <tr><td>Task</td><td>{r.task}</td></tr>
        <tr><td>Action</td><td>{r.action}</td></tr>
        <tr><td>Result</td><td>{r.result}</td></tr></table>
        <h2>Improved Answer</h2><div class="box success">{r.improved_answer}</div>
        <h2>Feedback</h2><p>{r.feedback}</p>
        <h2>Follow-ups</h2><ul>{''.join([f'<li>{q}</li>' for q in r.followups])}</ul>'''
        print(f'Score: {r.score}/10')
        pdf_path = await asyncio.to_thread(pdf, html, 'interview_eval')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def mock(self, role: str, interview_type: str = 'mixed') -> MockInterview:
        prompt = ChatPromptTemplate.from_messages([('system', SOCRATES_PROMPT), ('human', 'Create {type} interview for: {role}')])
        chain = prompt | self.model.with_structured_output(MockInterview)
        r = await self._safe_invoke(chain, {"role": role, "type": interview_type})
        qs = ''.join([f'<div class="box info"><h3>{q.question}</h3><p>Category: {q.category} | Difficulty: {q.difficulty}<br>Assesses: {q.what_to_assess}</p></div>' for q in r.questions])
        html = f'''<h1>Mock Interview: {r.role}</h1>
        {qs}
        <h2>Tips</h2><div class="box success"><ul>{''.join([f'<li>{t}</li>' for t in r.tips])}</ul></div>'''
        print(f'Interview: {r.role} | {len(r.questions)} questions')
        pdf_path = await asyncio.to_thread(pdf, html, 'mock_interview')
        return {"data": r, "pdf": str(pdf_path)}

# --- 4. SHERLOCK (Debug) ---

class DebugAnalysis(BaseModel):
    error_type: str = Field(description='Error type (e.g., RecursionError)')
    root_cause: str = Field(description='Why the error occurred')
    affected: List[str] = Field(description='Affected components')
    investigation: List[str] = Field(description='Investigation steps')
    fix: str = Field(description='How to fix')
    fixed_code: str = Field(description='Corrected code')
    prevention: List[str] = Field(description='Prevention measures')
    confidence: int = Field(description='1-100 confidence', ge=1, le=100)

class LogPattern(BaseModel):
    pattern: str = Field(description='Error pattern')
    count: int = Field(description='Occurrence count')
    severity: str = Field(description='Error, Warning, or Info')

class LogAnalysis(BaseModel):
    summary: str = Field(description='Log summary')
    patterns: List[LogPattern] = Field(description='Error patterns')
    timeline: List[str] = Field(description='Event timeline')
    root_cause: str = Field(description='Root cause hypothesis')
    actions: List[str] = Field(description='Recommended actions')

SHERLOCK_PROMPT = '''Role: Debugging Expert.
Trace root causes, provide step-by-step fix. Confidence 1-100.
Output strict JSON.'''

class SHERLOCK:
    def __init__(self, model):
        self.model = model

    async def debug(self, code: str, error: str) -> DebugAnalysis:
        prompt = ChatPromptTemplate.from_messages([('system', SHERLOCK_PROMPT), ('human', 'Code:\n```\n{code}\n```\nError: {error}')])
        chain = prompt | self.model.with_structured_output(DebugAnalysis)
        r = await self._safe_invoke(chain, {"code": code, "error": error})
        html = f'''<h1>Debug Analysis</h1>
        <div class="box warn"><h2>Error: {r.error_type}</h2></div>
        <h2>Root Cause</h2><div class="box info">{r.root_cause}</div>
        <h2>Affected</h2><ul>{''.join([f'<li>{c}</li>' for c in r.affected])}</ul>
        <h2>Investigation</h2><ol>{''.join([f'<li>{s}</li>' for s in r.investigation])}</ol>
        <h2>Fix</h2><p>{r.fix}</p>
        <h2>Fixed Code</h2><div class="code">{r.fixed_code.replace('<', '&lt;').replace('>', '&gt;')}</div>
        <h2>Prevention</h2><ul>{''.join([f'<li>{p}</li>' for p in r.prevention])}</ul>
        <div class="score">Confidence: {r.confidence}%</div>'''
        print(f'Error: {r.error_type} | Confidence: {r.confidence}%')
        pdf_path = await asyncio.to_thread(pdf, html, 'debug')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def logs(self, log_content: str) -> LogAnalysis:
        prompt = ChatPromptTemplate.from_messages([('system', SHERLOCK_PROMPT), ('human', 'Analyze logs:\n{logs}')])
        chain = prompt | self.model.with_structured_output(LogAnalysis)
        r = await self._safe_invoke(chain, {"logs": log_content[:5000]})
        patterns = ''.join([f'<tr><td>{p.pattern}</td><td>{p.count}</td><td>{p.severity}</td></tr>' for p in r.patterns])
        html = f'''<h1>Log Analysis</h1>
        <h2>Summary</h2><p>{r.summary}</p>
        <h2>Patterns</h2><table><tr><th>Pattern</th><th>Count</th><th>Severity</th></tr>{patterns}</table>
        <h2>Timeline</h2><ol>{''.join([f'<li>{t}</li>' for t in r.timeline])}</ol>
        <h2>Root Cause</h2><div class="box warn">{r.root_cause}</div>
        <h2>Actions</h2><ol>{''.join([f'<li>{a}</li>' for a in r.actions])}</ol>'''
        print(f'Patterns: {len(r.patterns)}')
        pdf_path = await asyncio.to_thread(pdf, html, 'log_analysis')
        return {"data": r, "pdf": str(pdf_path)}

# --- 5. ATLAS (Design) ---

class Component(BaseModel):
    name: str = Field(description='Component name')
    purpose: str = Field(description='What it does')
    technology: str = Field(description='Technology/stack')

class TradeOff(BaseModel):
    decision: str = Field(description='Design decision')
    pros: str = Field(description='Advantages')
    cons: str = Field(description='Disadvantages')

class APIEndpoint(BaseModel):
    method: str = Field(description='HTTP method')
    endpoint: str = Field(description='API path')
    description: str = Field(description='What it does')

class SystemDesign(BaseModel):
    overview: str = Field(description='System overview')
    components: List[Component] = Field(description='System components')
    data_flow: str = Field(description='Data flow description')
    database: str = Field(description='Database design')
    apis: List[APIEndpoint] = Field(description='API endpoints')
    scalability: List[str] = Field(description='Scalability notes')
    trade_offs: List[TradeOff] = Field(description='Design trade-offs')

class DesignReview(BaseModel):
    strengths: List[str] = Field(description='Design strengths')
    weaknesses: List[str] = Field(description='Design weaknesses')
    scalability_score: int = Field(description='1-10', ge=1, le=10)
    maintainability_score: int = Field(description='1-10', ge=1, le=10)
    security_score: int = Field(description='1-10', ge=1, le=10)
    recommendations: List[str] = Field(description='Improvements')

ATLAS_PROMPT = '''Role: System Architect.
Design scalable, maintainable systems. Consider CAP, SOLID.
Scores 1-10. Output strict JSON.'''

class ATLAS:
    def __init__(self, model):
        self.model = model

    async def design(self, requirements: str) -> SystemDesign:
        prompt = ChatPromptTemplate.from_messages([('system', ATLAS_PROMPT), ('human', 'Design: {requirements}')])
        chain = prompt | self.model.with_structured_output(SystemDesign)
        r = await self._safe_invoke(chain, {"requirements": requirements})
        comps = ''.join([f'<tr><td>{c.name}</td><td>{c.purpose}</td><td>{c.technology}</td></tr>' for c in r.components])
        apis = ''.join([f'<tr><td>{a.method}</td><td>{a.endpoint}</td><td>{a.description}</td></tr>' for a in r.apis])
        trades = ''.join([f'<tr><td>{t.decision}</td><td>{t.pros}</td><td>{t.cons}</td></tr>' for t in r.trade_offs])
        html = f'''<h1>System Design</h1>
        <h2>Overview</h2><p>{r.overview}</p>
        <h2>Components</h2><table><tr><th>Component</th><th>Purpose</th><th>Technology</th></tr>{comps}</table>
        <h2>Data Flow</h2><div class="box info">{r.data_flow}</div>
        <h2>Database</h2><div class="box info">{r.database}</div>
        <h2>APIs</h2><table><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>{apis}</table>
        <h2>Scalability</h2><ul>{''.join([f'<li>{s}</li>' for s in r.scalability])}</ul>
        <h2>Trade-offs</h2><table><tr><th>Decision</th><th>Pros</th><th>Cons</th></tr>{trades}</table>'''
        print(f'Components: {len(r.components)} | APIs: {len(r.apis)}')
        pdf_path = await asyncio.to_thread(pdf, html, 'system_design')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def review(self, design: str) -> DesignReview:
        prompt = ChatPromptTemplate.from_messages([('system', ATLAS_PROMPT), ('human', 'Review: {design}')])
        chain = prompt | self.model.with_structured_output(DesignReview)
        r = await self._safe_invoke(chain, {"design": design})
        html = f'''<h1>Design Review</h1>
        <h2>Scores</h2><table><tr><th>Aspect</th><th>Score</th></tr>
        <tr><td>Scalability</td><td>{r.scalability_score}/10</td></tr>
        <tr><td>Maintainability</td><td>{r.maintainability_score}/10</td></tr>
        <tr><td>Security</td><td>{r.security_score}/10</td></tr></table>
        <h2>Strengths</h2><div class="box success"><ul>{''.join([f'<li>{s}</li>' for s in r.strengths])}</ul></div>
        <h2>Weaknesses</h2><div class="box warn"><ul>{''.join([f'<li>{w}</li>' for w in r.weaknesses])}</ul></div>
        <h2>Recommendations</h2><ol>{''.join([f'<li>{rec}</li>' for rec in r.recommendations])}</ol>'''
        print(f'Scalability: {r.scalability_score}/10 | Security: {r.security_score}/10')
        pdf_path = await asyncio.to_thread(pdf, html, 'design_review')
        return {"data": r, "pdf": str(pdf_path)}

# --- 6. ZETTA (Knowledge) ---

class Note(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    links: List[str]
    created: str

class Connection(BaseModel):
    from_note: str = Field(description='Source note title')
    to_note: str = Field(description='Target note title')
    relationship: str = Field(description='How they connect')

class KnowledgeAnalysis(BaseModel):
    connections: List[Connection] = Field(description='Note connections')
    themes: List[str] = Field(description='Emergent themes')
    gaps: List[str] = Field(description='Knowledge gaps')
    synthesis: str = Field(description='Synthesized insight')

ZETTA_PROMPT = '''Role: Knowledge Graph Architect.
Find non-obvious connections, themes, and synthesis.'''

class ZETTA:
    def __init__(self, model):
        self.model = model
        self.notes = {}
        self.load()
    
    def load(self):
        path = DATA_DIR / 'knowledge/notes.json'
        if os.path.exists(path):
            with open(path) as f: self.notes = {k: Note(**v) for k, v in json.load(f).items()}
    
    def save(self):
        with open(DATA_DIR / 'knowledge/notes.json', 'w') as f:
            json.dump({k: v.model_dump() for k, v in self.notes.items()}, f, indent=2)
    
    async def add(self, title: str, content: str, tags: List[str] = []) -> Note:
        nid = hashlib.md5(title.encode()).hexdigest()[:8]
        note = Note(id=nid, title=title, content=content, tags=tags, links=[], created=datetime.now().isoformat())
        self.notes[nid] = note
        self.save()
        print(f'Added: {title} [{nid}]')
        return note
    
    async def link(self, id1: str, id2: str):
        if id1 in self.notes and id2 in self.notes:
            if id2 not in self.notes[id1].links: self.notes[id1].links.append(id2)
            if id1 not in self.notes[id2].links: self.notes[id2].links.append(id1)
            self.save()
            print(f'Linked: {self.notes[id1].title} <-> {self.notes[id2].title}')
    
    async def analyze(self) -> Optional[KnowledgeAnalysis]:
        if len(self.notes) < 2:
            print('Need at least 2 notes')
            return None
        notes_text = '\n'.join([f'{n.title}: {n.content[:200]}' for n in self.notes.values()])
        prompt = ChatPromptTemplate.from_messages([('system', ZETTA_PROMPT), ('human', 'Find connections in:\n{notes}')])
        chain = prompt | self.model.with_structured_output(KnowledgeAnalysis)
        r = await self._safe_invoke(chain, {"notes": notes_text})
        conns = ''.join([f'<tr><td>{c.from_note}</td><td>{c.to_note}</td><td>{c.relationship}</td></tr>' for c in r.connections])
        html = f'''<h1>Knowledge Graph</h1>
        <p>{len(self.notes)} notes</p>
        <h2>Connections</h2><table><tr><th>From</th><th>To</th><th>Relationship</th></tr>{conns}</table>
        <h2>Themes</h2><ul>{''.join([f'<li>{t}</li>' for t in r.themes])}</ul>
        <h2>Gaps</h2><div class="box warn"><ul>{''.join([f'<li>{g}</li>' for g in r.gaps])}</ul></div>
        <h2>Synthesis</h2><div class="box success">{r.synthesis}</div>'''
        print(f'Connections: {len(r.connections)}')
        pdf_path = await asyncio.to_thread(pdf, html, 'knowledge_graph')
        return {"data": r, "pdf": str(pdf_path)}
    
    async def list(self):
        print(f'\n{len(self.notes)} Notes:')
        for nid, n in self.notes.items(): print(f'  [{nid}] {n.title}')

# --- 7. PULSE (Productivity) ---

class ProductivityReport(BaseModel):
    total_hours: float = Field(description='Total hours logged')
    productive_hours: float = Field(description='Productive hours')
    focus_score: int = Field(description='1-10 focus score', ge=1, le=10)
    top_activities: List[str] = Field(description='Most common activities')
    time_wasters: List[str] = Field(description='Time wasters')
    patterns: List[str] = Field(description='Work patterns')
    recommendations: List[str] = Field(description='Improvement tips')

PULSE_PROMPT = '''Role: Productivity Analyst.
Analyze patterns, provide evidence-based tips. Focus 1-10.'''

class PULSE:
    def __init__(self, model):
        self.model = model
        self.logs = []
        self.habits = {}
        self.load()
    
    def load(self):
        path = DATA_DIR / 'productivity.json'
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                self.logs = data.get('logs', [])
                self.habits = data.get('habits', {})
    
    def save(self):
        with open(DATA_DIR / 'productivity.json', 'w') as f:
            json.dump({'logs': self.logs, 'habits': self.habits}, f, indent=2)
    
    async def log(self, activity: str, minutes: int, productive: bool = True):
        self.logs.append({'ts': datetime.now().isoformat(), 'activity': activity, 'mins': minutes, 'productive': productive, 'hour': datetime.now().hour})
        self.save()
        print(f'Logged: {activity} ({minutes}min)')
    
    async def habit(self, name: str):
        if name not in self.habits: self.habits[name] = []
        self.habits[name].append(datetime.now().isoformat())
        self.save()
        print(f'Completed: {name} (streak: {len(self.habits[name])})')
    
    async def report(self) -> Optional[ProductivityReport]:
        if len(self.logs) < 5:
            print(f'Need {5 - len(self.logs)} more logs')
            return None
        prompt = ChatPromptTemplate.from_messages([('system', PULSE_PROMPT), ('human', 'Analyze: {logs}')])
        chain = prompt | self.model.with_structured_output(ProductivityReport)
        r = await self._safe_invoke(chain, {"logs": json.dumps(self.logs[-50:])})
        html = f'''<h1>Productivity Report</h1>
        <div class="score">{r.focus_score}/10</div>
        <h2>Summary</h2><table>
        <tr><td>Total Hours</td><td>{r.total_hours:.1f}h</td></tr>
        <tr><td>Productive</td><td>{r.productive_hours:.1f}h</td></tr>
        <tr><td>Efficiency</td><td>{(r.productive_hours/r.total_hours*100) if r.total_hours > 0 else 0:.0f}%</td></tr></table>
        <h2>Top Activities</h2><ul>{''.join([f'<li>{a}</li>' for a in r.top_activities])}</ul>
        <h2>Time Wasters</h2><div class="box warn"><ul>{''.join([f'<li>{w}</li>' for w in r.time_wasters])}</ul></div>
        <h2>Patterns</h2><ul>{''.join([f'<li>{p}</li>' for p in r.patterns])}</ul>
        <h2>Recommendations</h2><div class="box success"><ol>{''.join([f'<li>{rec}</li>' for rec in r.recommendations])}</ol></div>'''
        print(f'Focus: {r.focus_score}/10')
        pdf_path = await asyncio.to_thread(pdf, html, 'productivity')
        return {"data": r, "pdf": str(pdf_path)}

# --- NEXUS Core ---

class NEXUS:
    def __init__(self, model):
        self.aria = ARIA(model)
        self.codex = CODEX(model)
        self.socrates = SOCRATES(model)
        self.sherlock = SHERLOCK(model)
        self.atlas = ATLAS(model)
        self.zetta = ZETTA(model)
        self.pulse = PULSE(model)
    
    def help(self):
        print('''
NEXUS - Neural EXpert Unified System
=====================================

ARIA (Research):
  nexus.aria.analyze(content)     Analyze research paper
  nexus.aria.review(topic)        Literature review
  nexus.aria.questions(topic,gap) Research questions

CODEX (Code):
  nexus.codex.review(code)        Full code review
  nexus.codex.audit(code)         Security audit

SOCRATES (Interview):
  nexus.socrates.evaluate(q, a)   Evaluate answer
  nexus.socrates.mock(role)       Mock interview

SHERLOCK (Debug):
  nexus.sherlock.debug(code,err)  Debug analysis
  nexus.sherlock.logs(content)    Log analysis

ATLAS (Design):
  nexus.atlas.design(reqs)        System design
  nexus.atlas.review(design)      Design review

ZETTA (Knowledge):
  nexus.zetta.add(title,content)  Add note
  nexus.zetta.link(id1,id2)       Link notes
  nexus.zetta.analyze()           Find connections
  nexus.zetta.list()              List notes

PULSE (Productivity):
  nexus.pulse.log(activity,mins)  Log activity
  nexus.pulse.habit(name)         Complete habit
  nexus.pulse.report()            Productivity report
''')

class NexusAgent(BaseAgent):
    name = "nexus"
    description = "Research-Level Multi-Domain AI Command Center (ARIA, CODEX, SOCRATES, SHERLOCK, ATLAS, ZETTA, PULSE)"
    icon = "🧠"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Executes NEXUS operations.
        
        Args:
            topic: The input to process.
            kwargs:
                module (str): Sub-agent to use (aria, codex, socrates, sherlock, atlas, zetta, pulse)
                command (str): Specific command to run (e.g., 'analyze', 'review')
                context (str): Additional context
                ...other arguments specific to commands
        """
        nexus = NEXUS(self.model)
        
        module = kwargs.get("module")
        command = kwargs.get("command")
        
        if not module or not command:
            # Default behavior or routing could go here
            # For now, return help info or try to infer
            nexus.help()
            return {"message": "Please specify 'module' and 'command' in arguments."}

        # Dispatcher logic
        try:
            mod_instance = getattr(nexus, module, None)
            if not mod_instance:
                return {"error": f"Module '{module}' not found."}
            
            cmd_func = getattr(mod_instance, command, None)
            if not cmd_func:
                return {"error": f"Command '{command}' not found in module '{module}'."}
            
            # Prepare arguments. Note: 'topic' is mapped to the first argument usually
            # But specific functions have specific signatures.
            # We map 'topic' to the primary argument of each function.
            
            args = {}
            if module == "aria":
                if command == "analyze": args = {"content": topic}
                elif command == "review": args = {"topic": topic, "context": kwargs.get("context", "")}
                elif command == "questions": args = {"topic": topic, "gap": kwargs.get("gap", "")}
            elif module == "codex":
                if command == "review": args = {"code": topic, "language": kwargs.get("language", "python")}
                elif command == "audit": args = {"code": topic}
            elif module == "socrates":
                if command == "evaluate": args = {"question": kwargs.get("question", ""), "answer": topic}
                elif command == "mock": args = {"role": topic, "interview_type": kwargs.get("interview_type", "mixed")}
            elif module == "sherlock":
                if command == "debug": args = {"code": topic, "error": kwargs.get("error", "")}
                elif command == "logs": args = {"log_content": topic}
            elif module == "atlas":
                if command == "design": args = {"requirements": topic}
                elif command == "review": args = {"design": topic}
            elif module == "zetta":
                if command == "add": args = {"title": topic, "content": kwargs.get("content", ""), "tags": kwargs.get("tags", [])}
                elif command == "link": args = {"id1": kwargs.get("id1"), "id2": kwargs.get("id2")}
                elif command == "analyze": args = {}
                elif command == "list": args = {}
            elif module == "pulse":
                if command == "log": args = {"activity": topic, "minutes": kwargs.get("minutes", 30)}
                elif command == "habit": args = {"name": topic}
                elif command == "report": args = {}

            print(f"🧠 NEXUS executing: {module}.{command}")
            result = await cmd_func(**args)
            
            # Helper to wrap result based on module/command
            model_data = None
            pdf_path = None

            if isinstance(result, dict) and "data" in result:
                # New format: {"data": model, "pdf": path}
                raw_data = result["data"]
                pdf_path = result.get("pdf")
                if hasattr(raw_data, "model_dump"):
                    model_data = raw_data.model_dump()
                else:
                    model_data = raw_data
            else:
                # Old format or Direct return
                if hasattr(result, "model_dump"):
                    model_data = result.model_dump()
                else:
                    model_data = result

            response = {}
            
            # Wrap based on what frontend expects
            if module == "codex":
                if command == "review": response["review"] = model_data
                elif command == "audit": response["audit"] = model_data
            elif module == "sherlock":
                if command == "debug": response["analysis"] = model_data
                elif command == "logs": response["logs"] = model_data
            elif module == "atlas":
                if command == "design": response["design"] = model_data
                elif command == "review": response["design_review"] = model_data
            elif module == "socrates":
                if command == "mock": response["interview"] = model_data
                elif command == "evaluate": response["evaluation"] = model_data
            elif module == "aria":
                if command == "analyze": response["paper_analysis"] = model_data
                elif command == "review": response["review"] = model_data
                elif command == "questions": response["questions"] = model_data
            elif module == "zetta":
                if command == "analyze": response["knowledge_graph"] = model_data
            elif module == "pulse":
                if command == "report": response["report"] = model_data
            
            # Fallback if no specific key matched
            if not response:
                response["result"] = model_data

            # Add PDF if available
            if pdf_path:
                response["pdf"] = pdf_path
            
            return response

        except Exception as e:
            return {"error": str(e)}

