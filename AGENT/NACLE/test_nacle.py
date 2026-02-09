import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/souga/Project-Own/LANGCHAIN')
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict
from xhtml2pdf import pisa

load_dotenv('c:/Users/souga/Project-Own/LANGCHAIN/.env')

class ConceptMap(BaseModel):
    topic: str
    concepts: List[str]
    relationships: List[Dict]
    prerequisites_map: Dict[str, List[str]]
    learning_order: List[str]

class DualCodeContent(BaseModel):
    concept: str
    verbal_explanation: str
    visual_description: str
    mermaid_diagram: str
    code_example: str
    analogy: str

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.7)
os.makedirs('reports', exist_ok=True)

CSS = '''<style>
@page { margin: 1cm; }
body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.4; margin: 0; padding: 0; }
h1 { color: #1a5f7a; font-size: 18pt; margin-bottom: 10px; border-bottom: 2px solid #1a5f7a; padding-bottom: 5px; }
h2 { color: #2c3e50; font-size: 13pt; margin-top: 15px; margin-bottom: 8px; }
p { margin: 5px 0; }
ol, ul { margin: 5px 0; padding-left: 25px; }
li { margin: 3px 0; }
.code-block { background: #f5f5f5; border: 1px solid #ddd; padding: 10px; font-family: Courier, monospace; font-size: 9pt; white-space: pre-wrap; word-wrap: break-word; margin: 10px 0; }
.analogy-box { background: #fff8e1; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
.visual-box { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px; margin: 10px 0; }
</style>'''

print('TESTING NACLE: Python Basics')
print('='*50)

prompt = ChatPromptTemplate.from_messages([
    ('system', 'Create a comprehensive concept map with core concepts, prerequisites, and learning order.'),
    ('human', 'Create concept map for: {topic}')
])
chain = prompt | model.with_structured_output(ConceptMap)
result = chain.invoke({'topic': 'Python Basics'})

print(f'\nGenerated {len(result.concepts)} concepts:\n')
for i, c in enumerate(result.concepts[:10]):
    print(f'  {i+1}. {c}')

concepts_html = ''.join([f'<li>{c}</li>' for c in result.concepts])
order_html = ', '.join(result.learning_order[:8])

html = f'''{CSS}
<h1>Python Basics - Learning Roadmap</h1>
<h2>Core Concepts ({len(result.concepts)} topics)</h2>
<ol>{concepts_html}</ol>
<h2>Recommended Learning Order</h2>
<p>{order_html}...</p>
'''

with open('reports/Python_Basics_Roadmap.pdf', 'wb') as f:
    pisa.CreatePDF(html, dest=f)
print(f'\nPDF saved: reports/Python_Basics_Roadmap.pdf')

print('\n' + '='*50)
print('GENERATING STUDY MATERIAL: Variables')
print('='*50)

dual_prompt = ChatPromptTemplate.from_messages([
    ('system', 'Create learning content: verbal explanation, visual description, code example with comments, real-world analogy'),
    ('human', 'Create educational content for: {concept}')
])
dual_chain = dual_prompt | model.with_structured_output(DualCodeContent)
dual = dual_chain.invoke({'concept': 'Variables in Python'})

print(f'\nExplanation:\n{dual.verbal_explanation[:300]}...')
print(f'\nAnalogy: {dual.analogy[:200]}...')

code_escaped = dual.code_example.replace('<', '&lt;').replace('>', '&gt;')

dual_html = f'''{CSS}
<h1>Variables in Python</h1>

<h2>What are Variables?</h2>
<p>{dual.verbal_explanation}</p>

<div class="visual-box">
<h2>Visualization</h2>
<p>{dual.visual_description}</p>
</div>

<h2>Code Example</h2>
<div class="code-block">{code_escaped}</div>

<div class="analogy-box">
<h2>Real-World Analogy</h2>
<p>{dual.analogy}</p>
</div>
'''

with open('reports/Variables_Study_Guide.pdf', 'wb') as f:
    pisa.CreatePDF(dual_html, dest=f)
print(f'\nPDF saved: reports/Variables_Study_Guide.pdf')

print('\nTEST COMPLETE!')
