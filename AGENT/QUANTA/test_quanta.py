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
import json, hashlib

load_dotenv('c:/Users/souga/Project-Own/LANGCHAIN/.env')
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.3)

DATA = 'quanta_data'
os.makedirs(f'{DATA}/reports', exist_ok=True)

CSS = '''<style>
@page{size:A4;margin:2cm}body{font-family:Segoe UI,Arial;font-size:10pt;line-height:1.6}
.header{background:linear-gradient(135deg,#1a237e,#4a148c);color:white;padding:20px;margin:-2cm -2cm 20px -2cm}
.header h1{margin:0;font-size:22pt}h2{color:#1a237e;border-bottom:2px solid #e8eaf6}
.metric{background:#e8eaf6;padding:8px 15px;border-radius:20px;margin:5px;font-weight:600;display:inline-block}
.box{padding:15px;margin:12px 0;border-radius:6px;border-left:4px solid}
.critical{background:#ffebee;border-color:#c62828}.high{background:#fff3e0;border-color:#ef6c00}
.info{background:#e3f2fd;border-color:#1565c0}.success{background:#e8f5e9;border-color:#2e7d32}
table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#1a237e;color:white;padding:10px}
td{padding:10px;border:1px solid #e0e0e0}.score-box{text-align:center;padding:20px;background:#e8f5e9;border-radius:8px}
.score-box .value{font-size:36pt;font-weight:700;color:#2e7d32}
</style>'''

def pdf(html, name):
    ts = datetime.now()
    footer = f'<div style="margin-top:30px;border-top:1px solid #ccc;padding-top:10px;font-size:8pt;color:#666">QUANTA v2.0 | {ts.strftime("%Y-%m-%d %H:%M")}</div>'
    path = f'{DATA}/reports/{name}_{ts.strftime("%H%M%S")}.pdf'
    with open(path, 'wb') as f: pisa.CreatePDF(CSS + html + footer, dest=f)
    return path

print('='*60)
print('QUANTA v2.0 PROFESSIONAL TEST')
print('='*60)

# Test 1: Quantum Algorithm with Citations
print('\n[1/2] QUANTUM - Algorithm Analysis with Citations...')

class Citation(BaseModel):
    authors: str
    title: str
    venue: str
    year: int

class AlgorithmAnalysis(BaseModel):
    name: str
    category: str
    complexity_classical: str
    complexity_quantum: str
    speedup_type: str
    key_concepts: List[str]
    applications: List[str]
    limitations: List[str]
    nisq_score: int = Field(ge=1, le=10)
    citations: List[Citation]

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are QUANTUM, a senior quantum computing researcher. Provide rigorous analysis with real citations from arxiv/Nature/PRX Quantum. NISQ score 1-10.'),
    ('human', 'Comprehensive analysis of: {name}')
])
r = (prompt | model.with_structured_output(AlgorithmAnalysis)).invoke({'name': "Variational Quantum Eigensolver (VQE)"})

print(f'  Algorithm: {r.name}')
print(f'  Category: {r.category}')
print(f'  Classical: {r.complexity_classical}')
print(f'  Quantum: {r.complexity_quantum}')
print(f'  Speedup: {r.speedup_type}')
print(f'  NISQ Score: {r.nisq_score}/10')
print(f'  Citations: {len(r.citations)}')
for c in r.citations[:2]:
    print(f'    - {c.authors[:30]}... ({c.year})')

cites = ''.join([f'<li style="font-size:8pt;color:#666">{c.authors} ({c.year}). <em>{c.title}</em>. {c.venue}</li>' for c in r.citations])
html = f'''<div class="header"><h1>{r.name}</h1><p>Category: {r.category} | Speedup: {r.speedup_type}</p></div>
<h2>Complexity</h2><table><tr><th>Classical</th><th>Quantum</th></tr><tr><td>{r.complexity_classical}</td><td>{r.complexity_quantum}</td></tr></table>
<h2>Key Concepts</h2><ul>{''.join([f'<li>{c}</li>' for c in r.key_concepts])}</ul>
<div class="score-box"><div class="value">{r.nisq_score}/10</div><div>NISQ Feasibility</div></div>
<h2>Applications</h2><div class="box success"><ul>{''.join([f'<li>{a}</li>' for a in r.applications])}</ul></div>
<h2>Limitations</h2><div class="box high"><ul>{''.join([f'<li>{l}</li>' for l in r.limitations])}</ul></div>
<h2>References</h2><ol>{cites}</ol>'''
print(f'  PDF: {pdf(html, "vqe_analysis")}')

# Test 2: Medical Trial with Evidence Grades
print('\n[2/2] MEDICA - Clinical Trial with Evidence Grades...')

class TrialAnalysis(BaseModel):
    name: str
    registry_id: str
    phase: str
    design: str
    sample_size: int
    intervention: str
    comparator: str
    primary_endpoint: str
    key_results: str
    p_value: str
    confidence_interval: str
    nnt: str
    evidence_grade: str = Field(description='A/B/C/D')
    limitations: List[str]
    clinical_implications: List[str]

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are MEDICA, a clinical research expert. Provide rigorous trial analysis with statistics, NNT, evidence grades (A/B/C/D).'),
    ('human', 'Detailed analysis of clinical trial: {name}')
])
r = (prompt | model.with_structured_output(TrialAnalysis)).invoke({'name': 'DAPA-HF'})

print(f'  Trial: {r.name} ({r.registry_id})')
print(f'  Phase: {r.phase} | Design: {r.design}')
print(f'  N = {r.sample_size}')
print(f'  Intervention: {r.intervention[:50]}...')
print(f'  p-value: {r.p_value} | CI: {r.confidence_interval}')
print(f'  NNT: {r.nnt}')
print(f'  Evidence Grade: {r.evidence_grade}')

html = f'''<div class="header"><h1>Clinical Trial: {r.name}</h1><p>{r.registry_id}</p></div>
<div class="box critical"><strong>DISCLAIMER:</strong> For educational purposes only.</div>
<h2>Study Design</h2><table>
<tr><td>Phase</td><td>{r.phase}</td><td>Design</td><td>{r.design}</td></tr>
<tr><td>Sample Size</td><td>n={r.sample_size:,}</td><td>Evidence Grade</td><td><strong>{r.evidence_grade}</strong></td></tr></table>
<h2>Intervention vs Comparator</h2><table><tr><th>Intervention</th><th>Comparator</th></tr>
<tr><td>{r.intervention}</td><td>{r.comparator}</td></tr></table>
<h2>Primary Endpoint</h2><div class="box info">{r.primary_endpoint}</div>
<h2>Key Results</h2><div class="box success">{r.key_results}</div>
<p><span class="metric">p = {r.p_value}</span> <span class="metric">95% CI: {r.confidence_interval}</span> <span class="metric">NNT: {r.nnt}</span></p>
<h2>Limitations</h2><div class="box high"><ul>{''.join([f'<li>{l}</li>' for l in r.limitations])}</ul></div>
<h2>Clinical Implications</h2><ul>{''.join([f'<li>{i}</li>' for i in r.clinical_implications])}</ul>'''
print(f'  PDF: {pdf(html, "dapa_hf_analysis")}')

print('\n' + '='*60)
print('PROFESSIONAL TESTS COMPLETE!')
print('='*60)
