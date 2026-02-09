# AGENTIC AI

AI-powered agents for content generation, analysis, and automation.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange)

## 🚀 Features

12 specialized AI agents powered by Google Gemini:

| Agent | Purpose |
|-------|---------|
| 🎨 **Image Gen** | Pinterest-optimized image generation |
| 📊 **Presentation Gen** | PowerPoint presentations |
| 📝 **Quiz Gen** | Educational quizzes with PDF export |
| 🗺️ **Roadmap Gen** | Learning roadmaps |
| 🎬 **Video Gen** | Video content strategies |
| ✉️ **Email Gen** | Professional email templates |
| 🔒 **Security Recon** | Security analysis reports |
| 🧠 **NACLE** | Knowledge graphs |
| ⚡ **NEXUS** | Code review, debugging, system design |
| 🔬 **QUANTA** | Scientific research analysis |
| 📚 **SCHOLAR** | Academic literature reviews |
| 🎓 **Student Gen** | Student progress analysis |

## 📁 Project Structure

```
├── app/                    # Backend API
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration
│   ├── agents/            # 12 AI agent modules
│   ├── models/            # Pydantic schemas
│   └── routers/           # API routes
├── frontend/              # Web UI
│   ├── index.html
│   ├── styles/
│   └── scripts/
├── data/                  # Generated outputs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `GEMINI_API_KEY` - Google Gemini API key

### 3. Run the Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/agents` | List all agents |
| POST | `/api/execute` | Execute an agent |

### Execute Agent Example

```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"agent": "quiz_gen", "topic": "Python Basics", "options": {"num_questions": 5}}'
```

## 📄 License

MIT License - see [LICENSE](LICENSE)
