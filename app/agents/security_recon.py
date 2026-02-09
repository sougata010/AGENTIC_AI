import os
import asyncio
import json
import socket
import logging
import requests
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

DATA_DIR = settings.DATA_DIR / "security_data"
LOG_DIR = DATA_DIR / "logs"
REPORT_DIR = DATA_DIR / "reports"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Update log configuration to use absolute paths
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "security_recon.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- Models ---

class SecurityReport(BaseModel):
    risk_level: str = Field(description="LOW/MEDIUM/HIGH/CRITICAL")
    summary: str = Field(description="2-3 sentence summary")
    findings: List[str] = Field(description="Key findings")
    recommendations: List[str] = Field(description="Recommendations")
    attack_surface: List[str] = Field(description="Attack vectors")

# --- Scanning Logic ---

def get_dns_info(target: str) -> Dict[str, Any]:
    print("\n📡 DNS RECONNAISSANCE\n" + "-"*40)
    dns_info = {"A": [], "MX": [], "NS": [], "TXT": []}
    try:
        dns_info["A"].append(socket.gethostbyname(target))
    except Exception as e:
        logger.error(f"DNS A record error: {e}")

    for t in ["MX", "NS", "TXT"]:
        try:
            r = requests.get(f"https://dns.google/resolve?name={target}&type={t}", timeout=10).json()
            dns_info[t] = [a.get("data", "") for a in r.get("Answer", [])]
        except Exception as e:
            logger.error(f"DNS {t} record error: {e}")
            
    print(f"A: {dns_info['A']}\nMX: {dns_info['MX']}\nNS: {dns_info['NS']}\nTXT: {len(dns_info['TXT'])} records")
    return dns_info

def get_security_headers(target: str) -> Dict[str, Any]:
    print("\n🔍 SECURITY HEADERS\n" + "-"*40)
    sec_headers = {
        "Strict-Transport-Security": "❌", "Content-Security-Policy": "❌", "X-Frame-Options": "❌",
        "X-Content-Type-Options": "❌", "X-XSS-Protection": "❌", "Referrer-Policy": "❌"
    }
    server_info = {}
    try:
        r = requests.get(f"https://{target}", timeout=10, allow_redirects=True)
        for h in sec_headers:
            if h.lower() in [x.lower() for x in r.headers]: sec_headers[h] = "✅"
        server_info = {"Server": r.headers.get("Server", "Hidden"), "Status": r.status_code}
    except Exception as e:
        logger.error(f"Headers error: {e}")
        server_info = {"Error": str(e)}

    for h, s in sec_headers.items(): print(f"{h}: {s}")
    print(f"\nServer: {server_info}")
    return {"headers": sec_headers, "server": server_info}

def detect_tech(target: str) -> List[str]:
    print("\n🔧 TECHNOLOGY DETECTION\n" + "-"*40)
    technologies = []
    try:
        r = requests.get(f"https://{target}", timeout=10)
        content = r.text.lower() + str(r.headers).lower()
        sigs = {
            "WordPress": "wp-content", "React": "react", "Vue": "vue", "Angular": "angular",
            "jQuery": "jquery", "Next.js": "_next", "Nginx": "nginx", "Apache": "apache", 
            "Cloudflare": "cf-ray", "Bootstrap": "bootstrap"
        }
        technologies = [t for t, s in sigs.items() if s in content]
    except Exception as e:
        logger.error(f"Tech detection error: {e}")
    
    print(f"Detected: {technologies if technologies else 'None'}")
    return technologies

def enum_subdomains(target: str) -> List[str]:
    print("\n🌐 SUBDOMAIN ENUMERATION\n" + "-"*40)
    subdomains = set()
    try:
        r = requests.get(f"https://crt.sh/?q=%.{target}&output=json", timeout=20)
        if r.ok:
            for e in r.json():
                for s in e.get("name_value", "").split("\n"):
                    s = s.strip().lower()
                    if s.endswith(target) and "*" not in s: subdomains.add(s)
    except Exception as e:
        logger.error(f"CRT.sh error: {e}")

    # Common subdomains check
    for sub in ["www", "mail", "api", "admin", "dev", "app", "test", "staging"]:
        try: 
            socket.gethostbyname(f"{sub}.{target}")
            subdomains.add(f"{sub}.{target}")
        except: pass
    
    sorted_subs = sorted(list(subdomains))[:20] # Limit to 20
    print(f"Found {len(sorted_subs)}:")
    for s in sorted_subs[:10]: print(f"  • {s}")
    return sorted_subs

def generate_dorks(target: str) -> List[str]:
    print("\n🔎 GOOGLE DORKS\n" + "-"*40)
    dorks = [
        f"site:{target}", f"site:{target} filetype:pdf", f"site:{target} inurl:admin",
        f"site:{target} inurl:login", f"site:{target} inurl:api", f'site:{target} intitle:"index of"',
        f"site:{target} filetype:sql", f"site:{target} inurl:.git"
    ]
    for i, d in enumerate(dorks, 1): print(f"{i}. {d}")
    return dorks

# --- Report Generation ---

def save_report(target: str, report: SecurityReport) -> str:
    filename = REPORT_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{target.replace('.', '_')}.md"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(f"# Security Report: {target}\n\n**Risk:** {report.risk_level}\n\n")
        f.write(f"## Summary\n{report.summary}\n\n")
        f.write("## Findings\n" + "\n".join([f"- {x}" for x in report.findings]) + "\n\n")
        f.write("## Attack Surface\n" + "\n".join([f"- {x}" for x in report.attack_surface]) + "\n\n")
        f.write("## Recommendations\n" + "\n".join([f"- {x}" for x in report.recommendations]))
    
    print(f"\n💾 Saved: {filename}")
    return str(filename)

# --- Agent Core ---

class SecurityReconAgent(BaseAgent):
    name = "security_recon"
    description = "Real-time Security Reconnaissance (DNS, Headers, Tech, Subdomains, AI Analysis)"
    icon = "🔒"
    
    SYSTEM_PROMPT = """You are a senior penetration tester. Analyze the gathered reconnaissance data.
    Determine the risk level (LOW/MEDIUM/HIGH/CRITICAL) based on findings like missing headers, exposed subdomains, old tech, etc.
    Provide a professional summary, key findings, attack surface analysis, and actionable recommendations.
    """

    async def execute(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Executes Security Reconnaissance.
        Args:
            topic: The target domain (e.g., example.com)
        """
        target = topic.replace("https://", "").replace("http://", "").strip("/")
        print(f"🎯 Target: {target}")
        
        # 1. Gather Data
        # Run independent scans concurrently
        loop = asyncio.get_running_loop()
        
        dns_task = loop.run_in_executor(None, get_dns_info, target)
        headers_task = loop.run_in_executor(None, get_security_headers, target)
        tech_task = loop.run_in_executor(None, detect_tech, target)
        subs_task = loop.run_in_executor(None, enum_subdomains, target)
        
        dns_info, headers_info, technologies, subdomains = await asyncio.gather(
            dns_task, headers_task, tech_task, subs_task
        )
        
        dorks = generate_dorks(target) # Fast enough to run sync or could be async too
        
        # 2. AI Analysis
        print("\n🤖 AI SECURITY ANALYSIS\n" + "-"*40)
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "Analyze this recon:\nTarget: {target}\nDNS: {dns}\nHeaders: {headers}\nTech: {tech}\nSubdomains: {subs}")
        ])
        
        chain = prompt | self.get_structured_model(SecurityReport)
        report = await self._safe_invoke(chain, {
            "target": target,
            "dns": json.dumps(dns_info),
            "headers": json.dumps(headers_info),
            "tech": str(technologies),
            "subs": len(subdomains)
        })
        
        # 3. Save Report
        report_path = await asyncio.to_thread(save_report, target, report)
        
        return {
            "report": report.model_dump(),
            "output_file": report_path
        }
