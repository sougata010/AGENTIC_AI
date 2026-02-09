import os
import json
import math
import random
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
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

DATA_DIR = settings.DATA_DIR / "nacle_data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DATA_DIR / "reports", exist_ok=True)
os.makedirs(DATA_DIR / "reviews", exist_ok=True)

KG_FILE = DATA_DIR / "knowledge_graph.json"
ANALYTICS_FILE = DATA_DIR / "analytics.json"

PDF_CSS = '''<style>
@page { margin: 1.5cm; }
body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333; }
h1 { color: #1565c0; font-size: 20pt; border-bottom: 3px solid #1565c0; padding-bottom: 8px; margin-bottom: 15px; }
h2 { color: #2e7d32; font-size: 14pt; margin-top: 20px; margin-bottom: 10px; }
h3 { color: #6a1b9a; font-size: 12pt; margin-top: 15px; }
.score-box { background: #e8f5e9; border: 2px solid #4caf50; padding: 15px; text-align: center; font-size: 24pt; font-weight: bold; color: #2e7d32; margin: 15px 0; }
.warning-box { background: #ffebee; border-left: 4px solid #f44336; padding: 12px; margin: 10px 0; }
.info-box { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 12px; margin: 10px 0; }
.success-box { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 12px; margin: 10px 0; }
.code-box { background: #263238; color: #aed581; padding: 15px; font-family: Consolas, monospace; font-size: 10pt; white-space: pre-wrap; margin: 10px 0; }
.analogy-box { background: #fff8e1; border-left: 4px solid #ff9800; padding: 12px; margin: 15px 0; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
th { background: #1565c0; color: white; padding: 10px; text-align: left; }
td { border: 1px solid #ddd; padding: 8px; }
tr:nth-child(even) { background: #f5f5f5; }
ul, ol { margin: 8px 0; padding-left: 25px; }
li { margin: 5px 0; }
</style>'''

def save_pdf(html: str, path_suffix: str) -> str:
    path = DATA_DIR / path_suffix
    with open(path, 'wb') as f:
        pisa.CreatePDF(PDF_CSS + html, dest=f)
    return str(path)

# --- Models & Enums ---

class BloomLevel(int, Enum):
    REMEMBER = 1
    UNDERSTAND = 2
    APPLY = 3
    ANALYZE = 4
    EVALUATE = 5
    CREATE = 6

BLOOM_VERBS = {
    1: ['define', 'list', 'recall', 'identify', 'name'],
    2: ['explain', 'describe', 'summarize', 'interpret', 'classify'],
    3: ['apply', 'demonstrate', 'solve', 'use', 'implement'],
    4: ['analyze', 'compare', 'contrast', 'differentiate', 'examine'],
    5: ['evaluate', 'judge', 'critique', 'justify', 'assess'],
    6: ['create', 'design', 'construct', 'develop', 'formulate']
}

BLOOM_NAMES = ['', 'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']

class KnowledgeNode(BaseModel):
    concept_id: str
    name: str
    description: str
    prerequisites: List[str] = []
    mastery: float = 0.0
    bloom_level: int = 1
    ease_factor: float = 2.5
    interval_days: float = 1.0
    repetitions: int = 0
    lapses: int = 0
    last_review: Optional[str] = None
    next_review: Optional[str] = None
    p_know: float = 0.1
    p_forget: float = 0.0
    study_count: int = 0
    total_study_time: int = 0
    review_history: List[Dict] = []

class ConceptMap(BaseModel):
    topic: str
    concepts: List[str] = Field(description='List of atomic, learnable concepts')
    descriptions: Dict[str, str] = Field(description='Brief description for each concept')
    prerequisites_map: Dict[str, List[str]] = Field(description='Prerequisites for each concept')
    learning_order: List[str] = Field(description='Optimal learning sequence')
    difficulty_levels: Dict[str, int] = Field(description='1-5 difficulty rating per concept')

class FeynmanAssessment(BaseModel):
    accuracy_score: int = Field(description='0-10 factual accuracy')
    clarity_score: int = Field(description='0-10 explanation clarity')
    completeness_score: int = Field(description='0-10 coverage completeness')
    depth_score: int = Field(description='0-10 conceptual depth')
    gaps: List[str] = Field(description='Knowledge gaps identified')
    misconceptions: List[str] = Field(description='Misconceptions detected')
    strengths: List[str] = Field(description='Strong points in explanation')
    feedback: str = Field(description='Detailed improvement feedback')
    suggested_topics: List[str] = Field(description='Topics to review')

class BloomQuestion(BaseModel):
    question: str
    bloom_level: int
    cognitive_verb: str
    expected_answer: str
    scoring_rubric: str
    hints: List[str]

class BloomAssessment(BaseModel):
    concept: str
    current_level: int
    questions: List[BloomQuestion]
    level_justification: str

class DualCodeContent(BaseModel):
    verbal_explanation: str = Field(description='Clear text explanation')
    key_points: List[str] = Field(description='3-5 key takeaways')
    visual_description: str = Field(description='What a diagram would show')
    mermaid_diagram: str = Field(description='Mermaid.js diagram code')
    code_example: str = Field(description='Working code with comments')
    real_world_analogy: str = Field(description='Relatable analogy')
    common_mistakes: List[str] = Field(description='Mistakes to avoid')
    practice_questions: List[str] = Field(description='2-3 practice questions')

# --- Helper Classes ---

class BayesianKnowledgeTracer:
    def __init__(self, p_init=0.1, p_learn=0.15, p_guess=0.25, p_slip=0.1):
        self.P_L0 = p_init
        self.P_T = p_learn
        self.P_G = p_guess
        self.P_S = p_slip
    
    def update(self, p_know: float, correct: bool) -> Tuple[float, float]:
        if correct:
            p_obs = p_know * (1 - self.P_S) + (1 - p_know) * self.P_G
            p_know_given_obs = (p_know * (1 - self.P_S)) / p_obs if p_obs > 0 else p_know
        else:
            p_obs = p_know * self.P_S + (1 - p_know) * (1 - self.P_G)
            p_know_given_obs = (p_know * self.P_S) / p_obs if p_obs > 0 else p_know
        
        new_p_know = p_know_given_obs + (1 - p_know_given_obs) * self.P_T
        confidence = abs(new_p_know - 0.5) * 2
        return min(0.99, max(0.01, new_p_know)), confidence

class SM2PlusScheduler:
    def __init__(self):
        self.min_ease = 1.3
        self.default_ease = 2.5
        self.max_interval = 365
    
    def schedule(self, node: KnowledgeNode, quality: int) -> KnowledgeNode:
        node.review_history.append({
            'date': datetime.now().isoformat(),
            'quality': quality,
            'p_know': node.p_know,
            'interval': node.interval_days
        })
        
        if quality < 3:
            node.lapses += 1
            node.repetitions = 0
            node.interval_days = 1
            node.ease_factor = max(self.min_ease, node.ease_factor - 0.2)
        else:
            if node.repetitions == 0:
                node.interval_days = 1
            elif node.repetitions == 1:
                node.interval_days = 6
            else:
                mastery_boost = 1 + (node.p_know * 0.3)
                node.interval_days = min(self.max_interval, node.interval_days * node.ease_factor * mastery_boost)
            node.repetitions += 1
            node.ease_factor = max(self.min_ease, node.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        
        node.last_review = datetime.now().isoformat()
        node.next_review = (datetime.now() + timedelta(days=node.interval_days)).isoformat()
        node.mastery = min(1.0, max(0.0, node.mastery + (quality - 2.5) * 0.1))
        return node
    
    def get_due(self, nodes: Dict[str, KnowledgeNode]) -> List[str]:
        now = datetime.now()
        due = []
        for cid, node in nodes.items():
            if node.repetitions == 0:
                due.append((cid, 0))
            elif node.next_review:
                days_overdue = (now - datetime.fromisoformat(node.next_review)).days
                if days_overdue >= 0:
                    due.append((cid, days_overdue))
        return [cid for cid, _ in sorted(due, key=lambda x: -x[1])]
    
    def calculate_retention(self, node: KnowledgeNode) -> float:
        if not node.last_review:
            return 1.0
        days_since = (datetime.now() - datetime.fromisoformat(node.last_review)).days
        stability = node.interval_days * (node.ease_factor / 2.5)
        retention = math.exp(-days_since / stability) if stability > 0 else 0
        return min(1.0, max(0.0, retention))

class InterleavedMixer:
    def __init__(self, interleave_ratio=0.3):
        self.interleave_ratio = interleave_ratio
    
    def get_optimal_sequence(self, nodes: Dict[str, KnowledgeNode], srs: SM2PlusScheduler, session_length: int = 5) -> List[str]:
        if not nodes:
            return []
        
        scored = []
        for cid, node in nodes.items():
            # Create lightweight dict for check to avoid loading whole node structure if p is missing
            default_node = KnowledgeNode(concept_id='', name='', description='') 
            # Note: In real app, all nodes are loaded.
            
            prereqs_met = all(nodes.get(p, default_node).p_know > 0.6 for p in node.prerequisites)
            retention = srs.calculate_retention(node)
            urgency = 1 - retention
            difficulty_match = 1 - abs(node.p_know - 0.5)
            score = urgency * 0.4 + difficulty_match * 0.3 + (0.3 if prereqs_met else 0)
            scored.append((cid, score, node.bloom_level))
        
        scored.sort(key=lambda x: -x[1])
        sequence = []
        last_bloom = 0
        
        for cid, score, bloom in scored[:session_length * 2]:
            if len(sequence) >= session_length:
                break
            if len(sequence) > 0 and random.random() < self.interleave_ratio:
                candidates = [s for s in scored if s[2] != last_bloom and s[0] not in sequence]
                if candidates:
                    cid, score, bloom = candidates[0]
            sequence.append(cid)
            last_bloom = bloom
        
        return sequence

class MetacognitiveAnalytics:
    def __init__(self):
        self.sessions = []
        self.load()
    
    def load(self):
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE) as f:
                self.sessions = json.load(f)
    
    def save(self):
        with open(ANALYTICS_FILE, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def log(self, concept: str, activity: str, score: float, bloom: int, duration: int = 5):
        self.sessions.append({
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour,
            'weekday': datetime.now().weekday(),
            'concept': concept,
            'activity': activity,
            'score': score,
            'bloom_level': bloom,
            'duration_min': duration
        })
        self.save()
    
    def generate_report(self):
        if len(self.sessions) < 3:
            print(f'Need {3 - len(self.sessions)} more sessions for analytics')
            return None
        
        total_time = sum(s['duration_min'] for s in self.sessions)
        avg_score = sum(s['score'] for s in self.sessions) / len(self.sessions)
        activities = {}
        for s in self.sessions:
            activities[s['activity']] = activities.get(s['activity'], 0) + 1
        
        hours = {}
        for s in self.sessions:
            h = s['hour']
            if h not in hours:
                hours[h] = {'count': 0, 'score_sum': 0}
            hours[h]['count'] += 1
            hours[h]['score_sum'] += s['score']
        
        best_hour = max(hours.items(), key=lambda x: x[1]['score_sum'] / x[1]['count'])[0] if hours else 12
        bloom_progression = [s['bloom_level'] for s in self.sessions[-10:]]
        
        recent_rows = ''.join([f"<tr><td>{s['concept'][:20]}</td><td>{s['activity']}</td><td>{s['score']:.1f}</td><td>{BLOOM_NAMES[s['bloom_level']]}</td></tr>" for s in self.sessions[-10:]])
        
        html = f'''<h1>Metacognitive Analytics Report</h1>
        <div class="score-box">{avg_score:.1f}<br><small>Average Score</small></div>
        
        <h2>Learning Statistics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Sessions</td><td>{len(self.sessions)}</td></tr>
            <tr><td>Total Study Time</td><td>{total_time} minutes</td></tr>
            <tr><td>Average Score</td><td>{avg_score:.2f}</td></tr>
            <tr><td>Best Study Hour</td><td>{best_hour}:00</td></tr>
        </table>
        
        <h2>Activity Breakdown</h2>
        <table>
            <tr><th>Activity</th><th>Count</th></tr>
            {''.join([f'<tr><td>{a}</td><td>{c}</td></tr>' for a, c in activities.items()])}
        </table>
        
        <h2>Bloom's Progression (Last 10)</h2>
        <div class="info-box">{' → '.join([BLOOM_NAMES[b] for b in bloom_progression])}</div>
        
        <h2>Recent Sessions</h2>
        <table>
            <tr><th>Concept</th><th>Activity</th><th>Score</th><th>Bloom</th></tr>
            {recent_rows}
        </table>
        
        <h2>Recommendations</h2>
        <div class="success-box">
            <ul>
                <li>Best time to study: Around {best_hour}:00</li>
                <li>{'Focus on harder concepts' if avg_score > 7 else 'Review fundamentals before advancing'}</li>
                <li>{'Great consistency!' if len(self.sessions) > 20 else 'Try to study more regularly'}</li>
            </ul>
        </div>'''
        
        pdf_path = save_pdf(html, f'reports/Analytics_{datetime.now().strftime("%Y%m%d")}.pdf')
        print(f'Analytics Report Generated: {pdf_path}')
        return pdf_path

# --- Prompts ---

KG_PROMPT = '''Role: Knowledge Architect.
For topic, ID: atomic concepts, descriptions, prerequisites, learning order, difficulty(1-5).
Output strict JSON.'''

FEYNMAN_PROMPT = '''Role: Expert Educator.
Assess explanation on Accuracy, Clarity, Completeness, Depth (0-10 each).
ID gaps/misconceptions. Provide feedback.'''

BLOOM_PROMPT = '''Generate Bloom Level {level} ({level_name}) questions.
Verbs: {verbs}. Create 3 deep questions with answers/rubrics/hints.'''

DUAL_PROMPT = '''Create multi-modal content:
Explanation, Key Points, Visual Desc, Mermaid Code, Code Example, Analogy, Mistakes, Practice Qs.'''

# --- NACLE Core ---

class NACLE:
    def __init__(self, model):
        self.model = model
        self.bkt = BayesianKnowledgeTracer()
        self.srs = SM2PlusScheduler()
        self.mixer = InterleavedMixer()
        self.analytics = MetacognitiveAnalytics()
        self.nodes = self.load_kg()
        print(f'NACLE Ready | {len(self.nodes)} concepts loaded')
    
    def load_kg(self) -> Dict[str, KnowledgeNode]:
        if not os.path.exists(KG_FILE):
            return {}
        with open(KG_FILE) as f:
            return {k: KnowledgeNode(**v) for k, v in json.load(f).items()}

    def save_kg_file(self):
        with open(KG_FILE, 'w') as f:
            json.dump({k: v.model_dump() for k, v in self.nodes.items()}, f, indent=2)

    async def build(self, topic: str):
        prompt = ChatPromptTemplate.from_messages([('system', KG_PROMPT), ('human', 'Create knowledge graph for: {topic}')])
        chain = prompt | self.model.with_structured_output(ConceptMap)
        cmap = await self._safe_invoke(chain, {"topic": topic})
        
        nodes = {}
        concept_to_id = {c: f'c{i:03d}' for i, c in enumerate(cmap.concepts)}
        
        for concept in cmap.concepts:
            cid = concept_to_id[concept]
            prereq_ids = [concept_to_id[p] for p in cmap.prerequisites_map.get(concept, []) if p in concept_to_id]
            nodes[cid] = KnowledgeNode(
                concept_id=cid,
                name=concept,
                description=cmap.descriptions.get(concept, ''),
                prerequisites=prereq_ids,
                bloom_level=min(cmap.difficulty_levels.get(concept, 1), 3)
            )
        
        self.nodes = nodes
        self.save_kg_file()
        
        rows = ''.join([f'<tr><td>{i+1}</td><td>{c}</td><td>{cmap.descriptions.get(c, "")[:100]}</td><td>{cmap.difficulty_levels.get(c, 1)}/5</td></tr>' for i, c in enumerate(cmap.concepts)])
        html = f'''<h1>{topic} - Knowledge Graph</h1>
        <div class="info-box"><strong>{len(nodes)} concepts</strong> organized for optimal learning</div>
        <h2>Concept Map</h2>
        <table><tr><th>#</th><th>Concept</th><th>Description</th><th>Difficulty</th></tr>{rows}</table>
        <h2>Recommended Learning Path</h2>
        <ol>{''.join([f'<li>{c}</li>' for c in cmap.learning_order])}</ol>'''
        
        pdf_path = await asyncio.to_thread(save_pdf, html, f'reports/{topic.replace(" ", "_")}_KnowledgeGraph.pdf')
        print(f'Knowledge Graph: {len(nodes)} concepts')
        print(f'PDF: {pdf_path}')
        return {"nodes": nodes, "pdf": pdf_path}
    
    async def study(self, cid: str):
        node = self.nodes.get(cid)
        if not node:
            return {"error": f"Concept {cid} not found"}
        
        prompt = ChatPromptTemplate.from_messages([('system', DUAL_PROMPT), ('human', 'Create study material for: {concept}')])
        chain = prompt | self.model.with_structured_output(DualCodeContent)
        result = await self._safe_invoke(chain, {"concept": node.name})
        
        code_escaped = result.code_example.replace('<', '&lt;').replace('>', '&gt;')
        html = f'''<h1>{node.name}</h1>
        <h2>Explanation</h2><p>{result.verbal_explanation}</p>
        <h2>Key Points</h2><ul>{''.join([f'<li>{p}</li>' for p in result.key_points])}</ul>
        <h2>Visual Representation</h2><div class="info-box">{result.visual_description}</div>
        <h2>Code Example</h2><div class="code-box">{code_escaped}</div>
        <h2>Real-World Analogy</h2><div class="analogy-box">{result.real_world_analogy}</div>
        <h2>Common Mistakes</h2><div class="warning-box"><ul>{''.join([f'<li>{m}</li>' for m in result.common_mistakes])}</ul></div>
        <h2>Practice Questions</h2><ol>{''.join([f'<li>{q}</li>' for q in result.practice_questions])}</ol>'''
        
        pdf_path = await asyncio.to_thread(save_pdf, html, f'reports/{node.name.replace(" ", "_")}_StudyGuide.pdf')
        self.analytics.log(node.name, 'study', node.p_know * 10, node.bloom_level)
        return {"result": result.model_dump(), "pdf": pdf_path}

    async def test(self, concept: str, explanation: str):
        prompt = ChatPromptTemplate.from_messages([
            ('system', FEYNMAN_PROMPT),
            ('human', 'CONCEPT: {concept}\\n\\nSTUDENT EXPLANATION:\\n{explanation}\\n\\nAssess this explanation.')
        ])
        chain = prompt | self.model.with_structured_output(FeynmanAssessment)
        result = await self._safe_invoke(chain, {"concept": concept, "explanation": explanation})
        
        avg = (result.accuracy_score + result.clarity_score + result.completeness_score + result.depth_score) / 4
        
        gaps_html = ''.join([f'<li>{g}</li>' for g in result.gaps]) if result.gaps else '<li>No major gaps identified</li>'
        misconceptions_html = ''.join([f'<li>{m}</li>' for m in result.misconceptions]) if result.misconceptions else '<li>None detected</li>'
        strengths_html = ''.join([f'<li>{s}</li>' for s in result.strengths]) if result.strengths else '<li>Keep practicing!</li>'
        
        html = f'''<h1>Feynman Assessment: {concept}</h1>
        <div class="score-box">{avg:.1f}/10</div>
        <h2>Dimension Scores</h2>
        <table>
            <tr><th>Dimension</th><th>Score</th></tr>
            <tr><td>Accuracy</td><td>{result.accuracy_score}/10</td></tr>
            <tr><td>Clarity</td><td>{result.clarity_score}/10</td></tr>
            <tr><td>Completeness</td><td>{result.completeness_score}/10</td></tr>
            <tr><td>Depth</td><td>{result.depth_score}/10</td></tr>
        </table>
        <h2>Your Explanation</h2><div class="info-box">{explanation}</div>
        <h2>Strengths</h2><div class="success-box"><ul>{strengths_html}</ul></div>
        <h2>Knowledge Gaps</h2><div class="warning-box"><ul>{gaps_html}</ul></div>
        <h2>Misconceptions</h2><div class="warning-box"><ul>{misconceptions_html}</ul></div>
        <h2>Feedback</h2><div class="info-box">{result.feedback}</div>'''
        
        pdf_path = await asyncio.to_thread(save_pdf, html, f'reviews/Feynman_{concept.replace(" ", "_")}_{datetime.now().strftime("%H%M%S")}.pdf')
        self.analytics.log(concept, 'feynman', avg, 2)
        return {"result": result.model_dump(), "pdf": pdf_path}

    async def review(self, cid: str, quality: int):
        node = self.nodes.get(cid)
        if not node: return {"error": f"Concept {cid} not found"}
        
        node.p_know, _ = self.bkt.update(node.p_know, quality >= 3)
        node = self.srs.schedule(node, quality)
        self.nodes[cid] = node
        self.save_kg_file()
        self.analytics.log(node.name, 'review', quality * 2, node.bloom_level)
        return {"message": f"Reviewed {node.name}, new mastery: {node.p_know:.0%}, next review: {node.next_review[:10]}"}

    async def bloom(self, cid: str):
        node = self.nodes.get(cid)
        if not node: return {"error": f"Concept {cid} not found"}
        
        level = node.bloom_level
        verbs = ', '.join(BLOOM_VERBS.get(level, BLOOM_VERBS[1]))
        prompt = ChatPromptTemplate.from_messages([
            ('system', BLOOM_PROMPT.format(level=level, level_name=BLOOM_NAMES[level], verbs=verbs)),
            ('human', 'Create Bloom Level {level} questions for: {concept}')
        ])
        chain = prompt | self.model.with_structured_output(BloomAssessment)
        result = await self._safe_invoke(chain, {"concept": node.name, "level": level})
        
        questions_html = ''.join([f'''
            <div class="info-box">
                <h3>Question {i+1} <small>({q.cognitive_verb})</small></h3>
                <p><strong>{q.question}</strong></p>
                <p><em>Expected:</em> {q.expected_answer}</p>
                <p><em>Rubric:</em> {q.scoring_rubric}</p>
                <p><em>Hints:</em> {', '.join(q.hints)}</p>
            </div>''' for i, q in enumerate(result.questions)])
        
        html = f'''<h1>Bloom's Assessment: {node.name}</h1>
        <div class="score-box">Level {level}: {BLOOM_NAMES[level]}</div>
        <p>{result.level_justification}</p>
        <h2>Assessment Questions</h2>
        {questions_html}'''
        
        pdf_path = await asyncio.to_thread(save_pdf, html, f'reviews/Bloom_{node.name.replace(" ", "_")}_L{level}.pdf')
        self.analytics.log(node.name, 'bloom', level * 2, level)
        return {"result": result.model_dump(), "pdf": pdf_path}

    async def promote_bloom(self, cid: str):
        node = self.nodes.get(cid)
        if not node: return {"error": "Not found"}
        if node.bloom_level < 6 and node.p_know > 0.7:
            node.bloom_level += 1
            self.nodes[cid] = node
            self.save_kg_file()
            return {"message": f"Promoted to Bloom Level {node.bloom_level}: {BLOOM_NAMES[node.bloom_level]}"}
        return {"message": "Not eligible for promotion (needs >70% mastery and level < 6)"}

    async def due(self):
        due_list = self.srs.get_due(self.nodes)
        return [{"id": cid, "name": self.nodes[cid].name} for cid in due_list[:10]]

    async def session(self, length: int = 5):
        sequence = self.mixer.get_optimal_sequence(self.nodes, self.srs, length)
        return [{"id": cid, "name": self.nodes[cid].name, "mastery": self.nodes[cid].p_know} for cid in sequence]

    async def insights(self):
        pdf_path = self.analytics.generate_report()
        return {"pdf": pdf_path}

# --- Agent Wrapper ---

class NacleAgent(BaseAgent):
    name = "nacle"
    description = "Neuro-Adaptive Cognitive Learning Engine (Knowledge Graph, Spaced Repetition, Feynman, Bloom)"
    icon = "🧠"
    
    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Executes NACLE operations.
        Args:
            topic: Primary input (topic name, concept ID, etc.)
            kwargs:
                command (str): 'build', 'study', 'test', 'review', 'bloom', 'promote', 'due', 'session', 'insights'
                explanation (str): For Feynman test
                quality (int): For review (0-5)
                length (int): For session length
        """
        nacle = NACLE(self.model)
        command = kwargs.get("command")
        
        if not command:
            return {"message": "Specify 'command' (build, study, test, review, bloom, promote, due, session, insights)"}

        try:
            if command == "build":
                result = await nacle.build(topic)
                return {"nodes": {k: v.model_dump() for k, v in result["nodes"].items()}, "pdf": result["pdf"]}
            elif command == "study":
                return await nacle.study(topic) # topic is cid here usually, or handle name mapping? 
                # Notebook logic uses 'study(cid)'. So user must pass cid.
            elif command == "test":
                return await nacle.test(kwargs.get("concept", topic), kwargs.get("explanation", ""))
            elif command == "review":
                return await nacle.review(topic, kwargs.get("quality", 3))
            elif command == "bloom":
                return await nacle.bloom(topic)
            elif command == "promote":
                return await nacle.promote_bloom(topic)
            elif command == "due":
                return {"due": await nacle.due()}
            elif command == "session":
                return {"session": await nacle.session(kwargs.get("length", 5))}
            elif command == "insights":
                return await nacle.insights()
            else:
                return {"error": f"Unknown command: {command}"}
                
        except Exception as e:
            return {"error": str(e)}
