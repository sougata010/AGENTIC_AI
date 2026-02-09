import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Dict
from xhtml2pdf import pisa
from datetime import datetime

load_dotenv('c:/Users/souga/Project-Own/LANGCHAIN/.env')
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.4)

DATA = 'scholar_data'
for d in [DATA, f'{DATA}/papers', f'{DATA}/reviews']: os.makedirs(d, exist_ok=True)

CSS = '''<style>
@page{size:A4;margin:2.5cm}body{font-family:Georgia,serif;font-size:11pt;line-height:1.8;text-align:justify}
.header{text-align:center;margin-bottom:30px;border-bottom:2px solid #1a237e;padding-bottom:20px}
.header h1{font-size:16pt;color:#1a237e}h2{color:#1a237e;border-bottom:1px solid #e0e0e0}
.abstract{background:#f5f5f5;padding:15px;border-left:4px solid #1a237e;font-style:italic}
.finding{background:#e8f5e9;padding:12px;margin:10px 0;border-left:4px solid #4caf50}
.gap{background:#fff3e0;padding:12px;margin:10px 0;border-left:4px solid #ff9800}
.critical{background:#ffebee;padding:12px;margin:10px 0;border-left:4px solid #f44336}
.info{background:#e3f2fd;padding:12px;margin:10px 0;border-left:4px solid #2196f3}
table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#1a237e;color:white;padding:10px}
td{padding:10px;border:1px solid #e0e0e0}.score{text-align:center;font-size:28pt;font-weight:700;color:#1a237e}
</style>'''

def pdf(html, folder, name):
    path = f'{DATA}/{folder}/{name}_{datetime.now().strftime("%H%M%S")}.pdf'
    with open(path, 'wb') as f: pisa.CreatePDF(CSS + html, dest=f)
    return path

print('='*60)
print('SCHOLAR - Full Academic Research Platform TEST')
print('='*60)

# Test 1: Literature Review
print('\n[1/3] SURVEY - Systematic Literature Review...')

class Theme(BaseModel):
    name: str
    description: str
    consensus: str

class LiteratureReview(BaseModel):
    topic: str
    papers_analyzed: int
    themes: List[Theme]
    research_gaps: List[str]
    future_directions: List[str]

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a senior academic researcher. Provide rigorous literature review following PRISMA guidelines.'),
    ('human', 'Systematic review on: {topic}')
])
r = (prompt | model.with_structured_output(LiteratureReview)).invoke({'topic': 'Transformer Models in NLP'})

print(f'  Topic: {r.topic}')
print(f'  Papers: {r.papers_analyzed}')
print(f'  Themes: {len(r.themes)}')
for t in r.themes[:3]:
    print(f'    - {t.name}: {t.description[:50]}...')
print(f'  Gaps: {len(r.research_gaps)}')

themes = ''.join([f'<div class="info"><h3>{t.name}</h3><p>{t.description}</p><p><strong>Consensus:</strong> {t.consensus}</p></div>' for t in r.themes])
html = f'''<div class="header"><h1>Systematic Literature Review</h1><p>{r.topic}</p></div>
<div class="abstract"><strong>Papers Analyzed:</strong> {r.papers_analyzed}</div>
<h2>Themes</h2>{themes}
<h2>Research Gaps</h2>{''.join([f'<div class="gap">{g}</div>' for g in r.research_gaps])}
<h2>Future Directions</h2>{''.join([f'<div class="finding">{d}</div>' for d in r.future_directions])}'''
print(f'  PDF: {pdf(html, "reviews", "lit_review")}')

# Test 2: Research Design
print('\n[2/3] HYPOTHESIS - Research Design...')

class Hypothesis(BaseModel):
    statement: str
    null_hypothesis: str
    alternative_hypothesis: str
    testability: int = Field(ge=1, le=10)

class ResearchDesign(BaseModel):
    title: str
    problem_statement: str
    hypotheses: List[Hypothesis]
    contribution: str

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a research methodologist. Generate testable hypotheses with clear operationalization.'),
    ('human', 'Design research for: {topic}')
])
r = (prompt | model.with_structured_output(ResearchDesign)).invoke({'topic': 'Explainable AI improves user trust'})

print(f'  Title: {r.title}')
print(f'  Hypotheses: {len(r.hypotheses)}')
for h in r.hypotheses[:2]:
    print(f'    H: {h.statement[:60]}...')
    print(f'      Testability: {h.testability}/10')

hyps = ''.join([f'''<div class="finding"><h3>{h.statement}</h3>
<p><strong>H0:</strong> {h.null_hypothesis}</p>
<p><strong>H1:</strong> {h.alternative_hypothesis}</p>
<p><strong>Testability:</strong> {h.testability}/10</p></div>''' for h in r.hypotheses])
html = f'''<div class="header"><h1>{r.title}</h1></div>
<h2>Problem Statement</h2><div class="abstract">{r.problem_statement}</div>
<h2>Hypotheses</h2>{hyps}
<h2>Contribution</h2><div class="info">{r.contribution}</div>'''
print(f'  PDF: {pdf(html, "papers", "research_design")}')

# Test 3: Peer Review
print('\n[3/3] REVIEW - Peer Review Simulation...')

class ReviewCriterion(BaseModel):
    criterion: str
    score: int = Field(ge=1, le=10)
    strengths: List[str]
    weaknesses: List[str]

class PeerReview(BaseModel):
    summary: str
    recommendation: str
    criteria: List[ReviewCriterion]
    major_concerns: List[str]
    overall_score: int = Field(ge=1, le=10)

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a rigorous peer reviewer for top journals. Evaluate critically but constructively.'),
    ('human', 'Review manuscript: {manuscript}')
])
r = (prompt | model.with_structured_output(PeerReview)).invoke({
    'manuscript': '''This paper studies LLM-based code generation. We evaluated GPT-4 and Claude on HumanEval 
    achieving 85% pass rate. Methods include prompt engineering and few-shot learning. Limitations include 
    small test set and lack of real-world evaluation.'''
})

print(f'  Recommendation: {r.recommendation}')
print(f'  Overall Score: {r.overall_score}/10')
print(f'  Criteria: {len(r.criteria)}')
for c in r.criteria[:3]:
    print(f'    - {c.criterion}: {c.score}/10')
print(f'  Major Concerns: {len(r.major_concerns)}')

criteria = ''.join([f'''<div class="{'finding' if c.score >= 7 else 'gap' if c.score >= 5 else 'critical'}">
<h3>{c.criterion}: {c.score}/10</h3>
<p><strong>Strengths:</strong> {', '.join(c.strengths)}</p>
<p><strong>Weaknesses:</strong> {', '.join(c.weaknesses)}</p></div>''' for c in r.criteria])
html = f'''<div class="header"><h1>Peer Review Report</h1></div>
<div class="score">{r.overall_score}/10</div>
<div class="info" style="text-align:center;font-size:14pt"><strong>Recommendation: {r.recommendation}</strong></div>
<h2>Summary</h2><div class="abstract">{r.summary}</div>
<h2>Criteria</h2>{criteria}
<h2>Major Concerns</h2>{''.join([f'<div class="critical">{c}</div>' for c in r.major_concerns])}'''
print(f'  PDF: {pdf(html, "reviews", "peer_review")}')

print('\n' + '='*60)
print('SCHOLAR TESTS COMPLETE!')
print('='*60)
