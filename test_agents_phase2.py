import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

from app.agents import get_agents

def test_scholar():
    print("\ntesting SCHOLAR...")
    try:
        from app.agents.scholar import ScholarAgent
        agent = ScholarAgent() 
        print("✅ SCHOLAR loaded successfully")
    except Exception as e:
        print(f"❌ SCHOLAR failed: {e}")

def test_security():
    print("\ntesting SECURITY_RECON...")
    try:
        from app.agents.security_recon import SecurityReconAgent
        agent = SecurityReconAgent()
        print("✅ SECURITY_RECON loaded successfully")
    except Exception as e:
        print(f"❌ SECURITY_RECON failed: {e}")

def test_student():
    print("\ntesting STUDENT_GEN...")
    try:
        from app.agents.student_gen import StudentGenAgent
        agent = StudentGenAgent()
        print("✅ STUDENT_GEN loaded successfully")
    except Exception as e:
        print(f"❌ STUDENT_GEN failed: {e}")

def test_registry():
    print("\nTesting Agent Registry...")
    try:
        agents = get_agents()
        required = ['scholar', 'security_recon', 'student_gen']
        for r in required:
            if r in agents:
                print(f"✅ Registry contains {r}")
            else:
                print(f"❌ Registry MISSING {r}")
    except Exception as e:
        print(f"❌ Registry failed: {e}")

if __name__ == "__main__":
    test_registry()
    test_scholar()
    test_security()
    test_student()
