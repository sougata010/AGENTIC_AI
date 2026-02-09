import os
import json
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from xhtml2pdf import pisa
from dotenv import load_dotenv

from app.agents.base import BaseAgent
from app.config import settings

# Ensure environment variables are loaded
load_dotenv()

# --- Configuration & Setup ---

DATA_DIR = settings.DATA_DIR / "quanta_data"
CONFIG_REPORTS = DATA_DIR / "reports"
CONFIG_HISTORY = DATA_DIR / "history.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_REPORTS, exist_ok=True)

CSS = '''<style>
@page{size:A4;margin:2cm}body{font-family:"Segoe UI",Arial;font-size:10pt;line-height:1.6;color:#1a1a1a}
.header{background:linear-gradient(135deg,#1a237e,#4a148c);color:white;padding:20px;margin:-2cm -2cm 20px -2cm}
.header h1{margin:0;font-size:22pt}.header p{margin:5px 0 0;opacity:0.9;font-size:10pt}
h2{color:#1a237e;border-bottom:2px solid #e8eaf6;padding-bottom:5px;margin-top:25px}
h3{color:#4a148c;margin-top:15px}
.metric{display:inline-block;background:#e8eaf6;padding:8px 15px;border-radius:20px;margin:5px;font-weight:600}
.box{padding:15px;margin:12px 0;border-radius:6px;border-left:4px solid}
.critical{background:#ffebee;border-color:#c62828}.high{background:#fff3e0;border-color:#ef6c00}
.info{background:#e3f2fd;border-color:#1565c0}.success{background:#e8f5e9;border-color:#2e7d32}
.quantum{background:#f3e5f5;border-color:#7b1fa2}
table{width:100%;border-collapse:collapse;margin:15px 0;font-size:9pt}
th{background:#1a237e;color:white;padding:10px;text-align:left}td{padding:10px;border:1px solid #e0e0e0}
tr:nth-child(even){background:#fafafa}
.code{background:#263238;color:#b2ff59;padding:15px;font-family:Consolas;font-size:8pt;border-radius:4px;overflow-x:auto}
.citation{font-size:8pt;color:#666;font-style:italic}
.footer{margin-top:30px;padding-top:15px;border-top:1px solid #e0e0e0;font-size:8pt;color:#666}
.score-box{text-align:center;padding:20px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border-radius:8px;margin:15px 0}
.score-box .value{font-size:36pt;font-weight:700;color:#2e7d32}.score-box .label{color:#666}
</style>'''

class History:
    @staticmethod
    def load(): return json.load(open(CONFIG_HISTORY)) if os.path.exists(CONFIG_HISTORY) else []
    @staticmethod
    def save(h): json.dump(h, open(CONFIG_HISTORY, 'w'), indent=2)
    @staticmethod
    def add(module, func, query, result):
        h = History.load()
        # Convert result to string if it's a Pydantic model or dict
        res_str = str(result.model_dump()) if hasattr(result, "model_dump") else str(result)
        h.append({'ts': datetime.now().isoformat(), 'module': module, 'func': func, 'query': query[:100], 'id': hashlib.md5(res_str.encode()).hexdigest()[:8]})
        History.save(h[-100:])

def pdf(html, name):
    ts = datetime.now()
    footer = f'<div class="footer">Generated: {ts.strftime("%Y-%m-%d %H:%M")} | QUANTA v2.0 | Report ID: {hashlib.md5(html.encode()).hexdigest()[:8]}</div>'
    path = CONFIG_REPORTS / f'{name}_{ts.strftime("%Y%m%d_%H%M%S")}.pdf'
    with open(path, 'wb') as f: pisa.CreatePDF(CSS + html + footer, dest=f)
    print(f'Report: {path}')
    return str(path)

# --- QUANTUM MODULE ---

class Citation(BaseModel):
    authors: str = Field(description='Author names')
    title: str = Field(description='Paper title')
    venue: str = Field(description='Journal/Conference')
    year: int = Field(description='Publication year')

class QuantumGate(BaseModel):
    name: str
    symbol: str = Field(description='e.g., H, CNOT, T')
    qubits: int = Field(description='Number of qubits')
    unitary: str = Field(description='Matrix representation')
    purpose: str

class AlgorithmAnalysis(BaseModel):
    name: str
    category: str = Field(description='Search/Simulation/Optimization/Cryptography')
    complexity_classical: str = Field(description='Classical complexity')
    complexity_quantum: str = Field(description='Quantum complexity')
    speedup_type: str = Field(description='Exponential/Polynomial/Quadratic')
    key_concepts: List[str]
    gates: List[QuantumGate]
    circuit_depth: str
    qubit_requirements: str
    applications: List[str]
    limitations: List[str]
    nisq_score: int = Field(ge=1, le=10)
    fault_tolerant_score: int = Field(ge=1, le=10)
    citations: List[Citation]

class HardwareSpec(BaseModel):
    platform: str
    qubit_count: int
    connectivity: str
    t1_time: str
    t2_time: str
    gate_fidelity_1q: str
    gate_fidelity_2q: str
    readout_fidelity: str
    gate_time: str
    operating_temp: str
    companies: List[str]
    advantages: List[str]
    challenges: List[str]

class ErrorCode(BaseModel):
    name: str
    code_distance: int
    physical_per_logical: int
    threshold: str
    correctable_errors: List[str]
    overhead: str
    implementation_complexity: str
    best_for: str

class AdvantageAnalysis(BaseModel):
    problem: str
    problem_class: str
    classical_best: str
    classical_complexity: str
    quantum_algorithm: str
    quantum_complexity: str
    speedup: str
    proven_advantage: bool
    practical_advantage: bool
    qubits_for_advantage: int
    estimated_timeline: str
    caveats: List[str]
    industry_impact: str

QUANTUM_SYSTEM = '''You are QUANTUM, a senior quantum computing researcher.
Provide technically rigorous, publication-quality analysis.
Include real citations from arxiv, Nature, Science, PRX Quantum.
All scores are integers 1-10. Be precise with complexity notation.'''

class QUANTUM:
    def __init__(self, model):
        self.model = model

    def algorithm(self, name: str) -> AlgorithmAnalysis:
        prompt = ChatPromptTemplate.from_messages([('system', QUANTUM_SYSTEM), ('human', 'Comprehensive analysis of quantum algorithm: {name}')])
        chain = prompt | self.model.with_structured_output(AlgorithmAnalysis)
        r = chain.invoke({'name': name})
        History.add('QUANTUM', 'algorithm', name, r)
        
        gates_t = ''.join([f'<tr><td>{g.symbol}</td><td>{g.name}</td><td>{g.qubits}Q</td><td style="font-family:monospace;font-size:8pt">{g.unitary}</td><td>{g.purpose}</td></tr>' for g in r.gates])
        cites = ''.join([f'<li class="citation">{c.authors} ({c.year}). {c.title}. <em>{c.venue}</em></li>' for c in r.citations])
        
        html = f'''<div class="header"><h1>{r.name}</h1><p>Quantum Algorithm Analysis | Category: {r.category}</p></div>
        <h2>Complexity Analysis</h2>
        <table><tr><th>Metric</th><th>Classical</th><th>Quantum</th><th>Speedup</th></tr>
        <tr><td>Time Complexity</td><td>{r.complexity_classical}</td><td>{r.complexity_quantum}</td><td><strong>{r.speedup_type}</strong></td></tr>
        <tr><td>Circuit Depth</td><td>N/A</td><td>{r.circuit_depth}</td><td>-</td></tr>
        <tr><td>Qubit Requirements</td><td>N/A</td><td>{r.qubit_requirements}</td><td>-</td></tr></table>
        
        <h2>Key Quantum Concepts</h2><ul>{''.join([f'<li>{c}</li>' for c in r.key_concepts])}</ul>
        
        <h2>Quantum Gates</h2><table><tr><th>Symbol</th><th>Name</th><th>Qubits</th><th>Unitary</th><th>Purpose</th></tr>{gates_t}</table>
        
        <h2>Feasibility Scores</h2>
        <div class="score-box" style="display:inline-block;width:45%"><div class="value">{r.nisq_score}/10</div><div class="label">NISQ Era</div></div>
        <div class="score-box" style="display:inline-block;width:45%"><div class="value">{r.fault_tolerant_score}/10</div><div class="label">Fault-Tolerant</div></div>
        
        <h2>Applications</h2><div class="box info"><ul>{''.join([f'<li>{a}</li>' for a in r.applications])}</ul></div>
        <h2>Limitations</h2><div class="box high"><ul>{''.join([f'<li>{l}</li>' for l in r.limitations])}</ul></div>
        <h2>References</h2><ol>{cites}</ol>'''
        
        print(f'{r.name} | {r.speedup_type} speedup | NISQ: {r.nisq_score}/10')
        pdf(html, f'algorithm_{r.name.replace(" ", "_").replace("'", "")}')
        return r
    
    def hardware(self) -> List[HardwareSpec]:
        prompt = ChatPromptTemplate.from_messages([('system', QUANTUM_SYSTEM), ('human', 'Compare all major quantum hardware platforms with current specs')])
        chain = prompt | self.model.with_structured_output(List[HardwareSpec])
        platforms = chain.invoke({})
        History.add('QUANTUM', 'hardware', 'comparison', platforms)
        
        rows = ''.join([f'''<h3>{p.platform}</h3>
        <table><tr><td>Qubits</td><td>{p.qubit_count}</td><td>Connectivity</td><td>{p.connectivity}</td></tr>
        <tr><td>T1/T2</td><td>{p.t1_time} / {p.t2_time}</td><td>Gate Time</td><td>{p.gate_time}</td></tr>
        <tr><td>1Q Fidelity</td><td>{p.gate_fidelity_1q}</td><td>2Q Fidelity</td><td>{p.gate_fidelity_2q}</td></tr>
        <tr><td>Readout</td><td>{p.readout_fidelity}</td><td>Temp</td><td>{p.operating_temp}</td></tr>
        <tr><td colspan="4"><strong>Companies:</strong> {', '.join(p.companies)}</td></tr></table>
        <div class="box success"><strong>Advantages:</strong> {', '.join(p.advantages)}</div>
        <div class="box high"><strong>Challenges:</strong> {', '.join(p.challenges)}</div>''' for p in platforms])
        
        html = f'<div class="header"><h1>Quantum Hardware Comparison</h1><p>{len(platforms)} Platforms Analyzed</p></div>{rows}'
        print(f'Compared {len(platforms)} platforms')
        pdf(html, 'hardware_comparison')
        return platforms
    
    def error_codes(self) -> List[ErrorCode]:
        prompt = ChatPromptTemplate.from_messages([('system', QUANTUM_SYSTEM), ('human', 'Analyze major quantum error correction codes')])
        chain = prompt | self.model.with_structured_output(List[ErrorCode])
        codes = chain.invoke({})
        History.add('QUANTUM', 'error_codes', 'analysis', codes)
        
        rows = ''.join([f'<tr><td>{c.name}</td><td>{c.code_distance}</td><td>{c.physical_per_logical}</td><td>{c.threshold}</td><td>{c.overhead}</td><td>{c.best_for}</td></tr>' for c in codes])
        html = f'''<div class="header"><h1>Quantum Error Correction Codes</h1></div>
        <table><tr><th>Code</th><th>Distance</th><th>Physical/Logical</th><th>Threshold</th><th>Overhead</th><th>Best For</th></tr>{rows}</table>'''
        
        for c in codes:
            html += f'<div class="box quantum"><h3>{c.name}</h3><p><strong>Corrects:</strong> {", ".join(c.correctable_errors)}</p><p><strong>Complexity:</strong> {c.implementation_complexity}</p></div>'
        
        print(f'Analyzed {len(codes)} error codes')
        pdf(html, 'error_correction')
        return codes
    
    def advantage(self, problem: str) -> AdvantageAnalysis:
        prompt = ChatPromptTemplate.from_messages([('system', QUANTUM_SYSTEM), ('human', 'Rigorous quantum advantage analysis for: {problem}')])
        chain = prompt | self.model.with_structured_output(AdvantageAnalysis)
        r = chain.invoke({'problem': problem})
        History.add('QUANTUM', 'advantage', problem, r)
        
        html = f'''<div class="header"><h1>Quantum Advantage Analysis</h1><p>{r.problem}</p></div>
        <h2>Problem Classification</h2><div class="box info"><strong>Class:</strong> {r.problem_class}</div>
        <h2>Complexity Comparison</h2>
        <table><tr><th></th><th>Classical</th><th>Quantum</th></tr>
        <tr><td>Algorithm</td><td>{r.classical_best}</td><td>{r.quantum_algorithm}</td></tr>
        <tr><td>Complexity</td><td>{r.classical_complexity}</td><td>{r.quantum_complexity}</td></tr></table>
        <div class="score-box"><div class="value">{r.speedup}</div><div class="label">Theoretical Speedup</div></div>
        <h2>Advantage Status</h2>
        <table><tr><td>Proven Theoretical</td><td>{'Yes' if r.proven_advantage else 'No'}</td></tr>
        <tr><td>Practical Today</td><td>{'Yes' if r.practical_advantage else 'No'}</td></tr>
        <tr><td>Qubits Needed</td><td>~{r.qubits_for_advantage:,}</td></tr>
        <tr><td>Timeline</td><td>{r.estimated_timeline}</td></tr></table>
        <h2>Industry Impact</h2><div class="box success">{r.industry_impact}</div>
        <h2>Caveats</h2><div class="box high"><ul>{''.join([f'<li>{c}</li>' for c in r.caveats])}</ul></div>'''
        
        print(f'{r.problem[:40]}... | Speedup: {r.speedup} | Practical: {r.practical_advantage}')
        pdf(html, 'advantage_analysis')
        return r

# --- MEDICA MODULE ---

class DrugInteraction(BaseModel):
    drug_a: str
    drug_b: str
    severity: str = Field(description='Contraindicated/Major/Moderate/Minor')
    mechanism: str
    clinical_effect: str
    evidence_level: str = Field(description='Established/Probable/Suspected/Possible')
    management: str
    monitoring: List[str]

class InteractionReport(BaseModel):
    drugs: List[str]
    total_interactions: int
    critical_count: int
    interactions: List[DrugInteraction]
    contraindications: List[str]
    recommendations: List[str]
    monitoring_parameters: List[str]

class Diagnosis(BaseModel):
    name: str
    icd10: str = Field(description='ICD-10 code')
    probability: str = Field(description='High/Medium/Low')
    pathophysiology: str
    supporting_findings: List[str]
    against_findings: List[str]
    diagnostic_criteria: List[str]
    gold_standard_test: str
    initial_workup: List[str]

class DifferentialReport(BaseModel):
    chief_complaint: str
    clinical_synopsis: str
    red_flags: List[str]
    emergent_conditions: List[str]
    differentials: List[Diagnosis]
    recommended_workup: List[str]
    disposition: str

class TrialDesign(BaseModel):
    name: str
    registry_id: str = Field(description='NCT number or equivalent')
    phase: str
    design: str
    blinding: str
    population: str
    sample_size: int
    intervention: str
    comparator: str
    primary_endpoint: str
    secondary_endpoints: List[str]
    duration: str
    key_results: str
    statistical_analysis: str
    p_value: str
    confidence_interval: str
    nnt_or_effect_size: str
    limitations: List[str]
    clinical_implications: List[str]
    evidence_grade: str = Field(description='A/B/C/D')

class Treatment(BaseModel):
    name: str
    class_: str = Field(alias='drug_class')
    dosing: str
    route: str
    evidence_grade: str
    guideline_source: str

class TreatmentProtocol(BaseModel):
    condition: str
    icd10: str
    severity_classification: str
    first_line: List[Treatment]
    second_line: List[Treatment]
    contraindicated: List[str]
    special_populations: List[str]
    monitoring: List[str]
    targets: List[str]
    follow_up: str
    guideline_sources: List[str]

MEDICA_SYSTEM = '''You are MEDICA, a clinical research intelligence system.
Provide evidence-based, guideline-concordant analysis.
Reference UpToDate, NICE, ACC/AHA, Cochrane where applicable.
Include ICD-10 codes, evidence grades, NNT where relevant.
DISCLAIMER: Educational/research purposes only. Not for clinical use.'''

class MEDICA:
    def __init__(self, model):
        self.model = model

    def interactions(self, drugs: List[str]) -> InteractionReport:
        prompt = ChatPromptTemplate.from_messages([('system', MEDICA_SYSTEM), ('human', 'Drug interaction analysis: {drugs}')])
        chain = prompt | self.model.with_structured_output(InteractionReport)
        r = chain.invoke({'drugs': ', '.join(drugs)})
        History.add('MEDICA', 'interactions', str(drugs), r)
        
        sev_colors = {'Contraindicated': 'critical', 'Major': 'critical', 'Moderate': 'high', 'Minor': 'info'}
        ints = ''.join([f'''<div class="box {sev_colors.get(i.severity, 'info')}"><h3>{i.drug_a} + {i.drug_b}</h3>
        <p><span class="metric">{i.severity}</span> <span class="metric">{i.evidence_level}</span></p>
        <p><strong>Mechanism:</strong> {i.mechanism}</p>
        <p><strong>Effect:</strong> {i.clinical_effect}</p>
        <p><strong>Management:</strong> {i.management}</p>
        <p><strong>Monitor:</strong> {', '.join(i.monitoring)}</p></div>''' for i in r.interactions])
        
        html = f'''<div class="header"><h1>Drug Interaction Report</h1><p>Analyzed: {', '.join(r.drugs)}</p></div>
        <div class="box critical"><strong>DISCLAIMER:</strong> For educational purposes only. Verify with clinical pharmacist.</div>
        <h2>Summary</h2><p><span class="metric">Total: {r.total_interactions}</span> <span class="metric">Critical: {r.critical_count}</span></p>
        <h2>Interactions</h2>{ints}
        <h2>Contraindications</h2><div class="box critical"><ul>{''.join([f'<li>{c}</li>' for c in r.contraindications]) or '<li>None identified</li>'}</ul></div>
        <h2>Clinical Recommendations</h2><ol>{''.join([f'<li>{rec}</li>' for rec in r.recommendations])}</ol>
        <h2>Monitoring Parameters</h2><ul>{''.join([f'<li>{m}</li>' for m in r.monitoring_parameters])}</ul>'''
        
        print(f'Analyzed {len(r.drugs)} drugs | {r.total_interactions} interactions | {r.critical_count} critical')
        pdf(html, 'drug_interactions')
        return r
    
    def differential(self, symptoms: str, history: str = '', exam: str = '') -> DifferentialReport:
        prompt = ChatPromptTemplate.from_messages([('system', MEDICA_SYSTEM), ('human', 'Differential diagnosis:\nSymptoms: {s}\nHistory: {h}\nExam: {e}')])
        chain = prompt | self.model.with_structured_output(DifferentialReport)
        r = chain.invoke({'s': symptoms, 'h': history, 'e': exam})
        History.add('MEDICA', 'differential', symptoms, r)
        
        prob_colors = {'High': 'critical', 'Medium': 'high', 'Low': 'info'}
        diffs = ''.join([f'''<div class="box {prob_colors.get(d.probability, 'info')}"><h3>{d.name} <span class="metric">{d.icd10}</span> <span class="metric">{d.probability}</span></h3>
        <p><strong>Pathophysiology:</strong> {d.pathophysiology}</p>
        <p><strong>Supporting:</strong> {', '.join(d.supporting_findings)}</p>
        <p><strong>Against:</strong> {', '.join(d.against_findings) or 'None'}</p>
        <p><strong>Gold Standard:</strong> {d.gold_standard_test}</p>
        <p><strong>Initial Workup:</strong> {', '.join(d.initial_workup)}</p></div>''' for d in r.differentials])
        
        html = f'''<div class="header"><h1>Differential Diagnosis Report</h1><p>{r.chief_complaint}</p></div>
        <div class="box critical"><strong>DISCLAIMER:</strong> For educational purposes only. Not a substitute for clinical judgment.</div>
        <h2>Clinical Synopsis</h2><div class="box info">{r.clinical_synopsis}</div>
        <h2>Red Flags</h2><div class="box critical"><ul>{''.join([f'<li>{f}</li>' for f in r.red_flags])}</ul></div>
        <h2>Emergent Conditions to Rule Out</h2><ul>{''.join([f'<li><strong>{e}</strong></li>' for e in r.emergent_conditions])}</ul>
        <h2>Differential Diagnoses</h2>{diffs}
        <h2>Recommended Workup</h2><ol>{''.join([f'<li>{w}</li>' for w in r.recommended_workup])}</ol>
        <h2>Disposition</h2><div class="box success">{r.disposition}</div>'''
        
        print(f'{r.chief_complaint} | {len(r.differentials)} differentials | {len(r.red_flags)} red flags')
        pdf(html, 'differential_diagnosis')
        return r
    
    def trial(self, name: str) -> TrialDesign:
        prompt = ChatPromptTemplate.from_messages([('system', MEDICA_SYSTEM), ('human', 'Detailed analysis of clinical trial: {name}')])
        chain = prompt | self.model.with_structured_output(TrialDesign)
        r = chain.invoke({'name': name})
        History.add('MEDICA', 'trial', name, r)
        
        html = f'''<div class="header"><h1>Clinical Trial Analysis</h1><p>{r.name} | {r.registry_id}</p></div>
        <h2>Study Design</h2>
        <table><tr><td>Phase</td><td>{r.phase}</td><td>Design</td><td>{r.design}</td></tr>
        <tr><td>Blinding</td><td>{r.blinding}</td><td>Sample Size</td><td>n={r.sample_size:,}</td></tr>
        <tr><td>Duration</td><td>{r.duration}</td><td>Evidence Grade</td><td><strong>{r.evidence_grade}</strong></td></tr></table>
        <h2>Population</h2><div class="box info">{r.population}</div>
        <h2>Intervention vs Comparator</h2>
        <table><tr><th>Intervention</th><th>Comparator</th></tr><tr><td>{r.intervention}</td><td>{r.comparator}</td></tr></table>
        <h2>Endpoints</h2><p><strong>Primary:</strong> {r.primary_endpoint}</p><ul>{''.join([f'<li>{s}</li>' for s in r.secondary_endpoints])}</ul>
        <h2>Results</h2><div class="box success">{r.key_results}</div>
        <p><strong>Statistics:</strong> {r.statistical_analysis}</p>
        <p><span class="metric">p = {r.p_value}</span> <span class="metric">95% CI: {r.confidence_interval}</span> <span class="metric">NNT/Effect: {r.nnt_or_effect_size}</span></p>
        <h2>Limitations</h2><div class="box high"><ul>{''.join([f'<li>{l}</li>' for l in r.limitations])}</ul></div>
        <h2>Clinical Implications</h2><ul>{''.join([f'<li>{i}</li>' for i in r.clinical_implications])}</ul>'''
        
        print(f'{r.name} | Phase {r.phase} | n={r.sample_size} | Grade {r.evidence_grade}')
        pdf(html, f'trial_{r.name.replace(" ", "_").replace("-", "_")}')
        return r
    
    def protocol(self, condition: str) -> TreatmentProtocol:
        prompt = ChatPromptTemplate.from_messages([('system', MEDICA_SYSTEM), ('human', 'Evidence-based treatment protocol for: {condition}')])
        chain = prompt | self.model.with_structured_output(TreatmentProtocol)
        r = chain.invoke({'condition': condition})
        History.add('MEDICA', 'protocol', condition, r)
        
        first = ''.join([f'<tr><td>{t.name}</td><td>{t.class_}</td><td>{t.dosing}</td><td>{t.route}</td><td>{t.evidence_grade}</td><td>{t.guideline_source}</td></tr>' for t in r.first_line])
        second = ''.join([f'<tr><td>{t.name}</td><td>{t.class_}</td><td>{t.dosing}</td><td>{t.route}</td><td>{t.evidence_grade}</td><td>{t.guideline_source}</td></tr>' for t in r.second_line])
        
        html = f'''<div class="header"><h1>Treatment Protocol</h1><p>{r.condition} | {r.icd10}</p></div>
        <div class="box critical"><strong>DISCLAIMER:</strong> For educational purposes. Follow local guidelines.</div>
        <h2>Severity Classification</h2><div class="box info">{r.severity_classification}</div>
        <h2>First-Line Therapy</h2><table><tr><th>Drug</th><th>Class</th><th>Dosing</th><th>Route</th><th>Grade</th><th>Source</th></tr>{first}</table>
        <h2>Second-Line Therapy</h2><table><tr><th>Drug</th><th>Class</th><th>Dosing</th><th>Route</th><th>Grade</th><th>Source</th></tr>{second}</table>
        <h2>Contraindicated</h2><div class="box critical"><ul>{''.join([f'<li>{c}</li>' for c in r.contraindicated])}</ul></div>
        <h2>Special Populations</h2><ul>{''.join([f'<li>{s}</li>' for s in r.special_populations])}</ul>
        <h2>Monitoring & Targets</h2>
        <p><strong>Monitor:</strong> {', '.join(r.monitoring)}</p>
        <p><strong>Targets:</strong> {', '.join(r.targets)}</p>
        <h2>Follow-up</h2><p>{r.follow_up}</p>
        <h2>Guideline Sources</h2><ul>{''.join([f'<li class="citation">{g}</li>' for g in r.guideline_sources])}</ul>'''
        
        print(f'{r.condition} | {len(r.first_line)} first-line | {len(r.second_line)} second-line')
        pdf(html, f'protocol_{r.condition.replace(" ", "_")}')
        return r

# --- QUANTA Core ---

class QUANTA:
    def __init__(self, model):
        self.quantum = QUANTUM(model)
        self.medica = MEDICA(model)
    
    def history(self, n: int = 10):
        h = History.load()[-n:]
        print(f'\nLast {len(h)} queries:')
        for e in h: print(f"  [{e['ts'][:16]}] {e['module']}.{e['func']}({e['query'][:30]}...)")
        return h

# --- Agent Wrapper ---

class QuantaAgent(BaseAgent):
    name = "quanta"
    description = "Quantum Computing & Biomedical Research Intelligence"
    icon = "⚛️"
    
    def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Executes QUANTA operations.
        Args:
            topic: Primary input (algorithm name, drug list, symptoms, problem, etc.)
            kwargs:
                module (str): 'quantum' or 'medica'
                command (str): 'algorithm', 'hardware', 'error_codes', 'advantage', 'interactions', 'differential', 'trial', 'protocol', 'history'
        """
        quanta = QUANTA(self.model)
        module = kwargs.get("module")
        command = kwargs.get("command")
        
        if not module and not command:
             # Try simple history check or help
             if topic == "history":
                 return {"history": quanta.history()}
             return {"message": "Specify 'module' and 'command'."}

        try:
            if module == "quantum":
                if command == "algorithm":
                    return quanta.quantum.algorithm(topic).model_dump()
                elif command == "hardware":
                    return [h.model_dump() for h in quanta.quantum.hardware()]
                elif command == "error_codes":
                    return [c.model_dump() for c in quanta.quantum.error_codes()]
                elif command == "advantage":
                    return quanta.quantum.advantage(topic).model_dump()
            
            elif module == "medica":
                if command == "interactions":
                    # topic should be list of drugs or comma separated string
                    drugs = topic if isinstance(topic, list) else [d.strip() for d in topic.split(',')]
                    return quanta.medica.interactions(drugs).model_dump()
                elif command == "differential":
                    # kwargs need symptoms, history, exam
                    return quanta.medica.differential(topic, kwargs.get("history", ""), kwargs.get("exam", "")).model_dump()
                elif command == "trial":
                    return quanta.medica.trial(topic).model_dump()
                elif command == "protocol":
                    return quanta.medica.protocol(topic).model_dump()
                    
            elif command == "history":
                return {"history": quanta.history()}
                
            return {"error": f"Unknown module/command: {module}/{command}"}
        except Exception as e:
            return {"error": str(e)}
