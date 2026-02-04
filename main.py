import os
import sys
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

sys.path.append(os.path.join(os.path.dirname(__file__), 'AGENT'))

from AGENT.functions import (
    init_gemini_client,
    generate_trending_topic,
    generate_full_pin_concept,
    PinterestPinStrategy,
    log_to_daily_jsonl
)
from AGENT.prompts import get_system_prompt

def main():
    print("🚀 Starting Agentic AI Workflow...")
    load_dotenv()
    
    if not os.environ.get('GEMINI_API_KEY'):
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    try:
        client_creative = init_gemini_client(temperature=0.7)
        
        print("1️⃣  Generating Trending Topic...")
        topic = generate_trending_topic(client_creative)
        print(f"   Topic: {topic}")
        
        print("2️⃣  Expanding Visual Concept...")
        full_concept = generate_full_pin_concept(client_creative, topic)
        
        print("3️⃣  Creating Structured Strategy...")
        model_structured = init_gemini_client(temperature=0, response_mime_type="application/json")
        structured_llm = model_structured.with_structured_output(PinterestPinStrategy)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", get_system_prompt()),
            ("human", "{topic}")
        ])
        
        chain = prompt_template | structured_llm
        result = chain.invoke({'topic': full_concept})
        
        output_file = 'AGENT/current_strategy.json'
        with open(output_file, 'w') as f:
            if hasattr(result, 'model_dump'):
                json.dump(result.model_dump(), f, indent=2)
            else:
                json.dump(result.dict(), f, indent=2)
        
        log_file = log_to_daily_jsonl(result, folder="AGENT/logs")
        
        print(f"✅ Workflow Complete!")
        print(f"   Strategy saved to: {output_file}")
        print(f"   Log appended to: {log_file}")

    except Exception as e:
        print(f"❌ Execution Failed: {e}")

if __name__ == "__main__":
    main()
