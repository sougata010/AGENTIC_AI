import asyncio
import os
import sys

# Ensure app can be imported
sys.path.append(os.getcwd())

from app.agents import get_agents

# Mocking internal dependencies if needed, but we'll try running with real agents first.
# Note: This requires GEMINI_API_KEY to be set in .env

async def test_agents():
    print("🚀 Starting Async Agent Verification...")
    
    try:
        agents_dict = get_agents()
    except Exception as e:
        print(f"❌ Failed to load agents: {e}")
        return

    test_cases = [
        # (agent_key, test_name, params)
        ("resume_opt", "Resume Analysis", {"resume_text": "Software Engineer with 5 years experience.", "job_description": "Senior Python Developer"}),
        ("debate_coach", "Debate Logic", {"topic": "AI will replace doctors", "user_argument": "AI is more accurate."}),
        ("travel_plan", "Travel Itinerary", {"destination": "Tokyo", "duration": "3 days"}),
        ("student_gen", "Study Notes", {"topic": "Binary Search", "command": "notes"}),
        ("security_recon", "Security Scan", {"topic": "example.com"}),
        ("email_gen", "Email Writer", {"topic": "Sick leave for 2 days"}),
    ]
    
    for agent_key, test_name, params in test_cases:
        if agent_key not in agents_dict:
            print(f"⚠️ Agent '{agent_key}' not found in registry, skipping.")
            continue
            
        print(f"\n🧪 Testing {test_name} ({agent_key})...")
        try:
            agent_cls = agents_dict[agent_key]
            agent = agent_cls()
            
            # Execute async
            result = await agent.execute(**params)
            
            if isinstance(result, dict) and "error" in result:
                 print(f"❌ {agent_key} returned error: {result['error']}")
            else:
                 print(f"✅ {agent_key} executed successfully.")
                 print(f"   Keys returned: {list(result.keys())}")
                 
        except Exception as e:
            print(f"❌ {agent_key} CRASHED: {e}")
            import traceback
            traceback.print_exc()

    print("\n🏁 Agent Verification Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_agents())
