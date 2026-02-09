import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import urllib.parse

from app.config import settings
from app.routers.agents import router as agents_router

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.logging import setup_logging
from app.core.exceptions import add_exception_handlers
import time

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic AI API",
    description="""
    🚀 **Agentic AI Enterprise Console**
    
    Autonomous multi-agent system for complex problem solving, research, and generation.
    """,
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register Exception Handlers
add_exception_handlers(app)

# Simple Rate Limiter Middleware
class RateLimitMiddleware:
    def __init__(self, app, requests_per_minute=20):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.calls = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = scope.get("client", ["unknown"])[0]
        now = time.time()
        
        # Clean old calls
        self.calls = {ip: times for ip, times in self.calls.items() if any(t > now - 60 for t in times)}
        
        user_calls = self.calls.get(client_ip, [])
        user_calls = [t for t in user_calls if t > now - 60]
        
        if len(user_calls) >= self.requests_per_minute:
            # Send 429 Too Many Requests
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail": "Rate limit exceeded. Please wait a minute."}',
            })
            return

        user_calls.append(now)
        self.calls[client_ip] = user_calls
        await self.app(scope, receive, send)

# Middleware Pipeline
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(RateLimitMiddleware, requests_per_minute=30)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DATA_DIR = Path(__file__).parent.parent / "data"
IMAGES_DIR = DATA_DIR / "images"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents": 12}

@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

# Mount images directory for direct access
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Mount entire data directory
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

@app.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    """Serve generated files from any data subdirectory"""
    decoded_path = urllib.parse.unquote(file_path)
    
    # Handle Windows paths - convert backslashes
    decoded_path = decoded_path.replace('\\', '/')
    filename = Path(decoded_path).name
    
    # Check all possible locations
    possible_paths = [
        Path(decoded_path),  # Absolute path
        DATA_DIR / decoded_path,  # Relative to data dir
        DATA_DIR / filename,  # Just filename in data root
    ]
    
    # Check for direct existence first
    for file in possible_paths:
        if file.exists() and file.is_file():
            return FileResponse(file, filename=file.name, media_type=get_media_type(file.suffix))
            
    # If not found, do a recursive search within DATA_DIR
    if DATA_DIR.exists():
        # Search for exact filename recursively
        # rglob returns a generator, we take the first match
        try:
            matches = list(DATA_DIR.rglob(filename))
            if matches:
                target_file = matches[0]
                return FileResponse(
                    target_file,
                    filename=target_file.name,
                    media_type=get_media_type(target_file.suffix)
                )
        except Exception as e:
            logger.error(f"Error during recursive file search: {e}")
    
    raise HTTPException(status_code=404, detail=f"File not found: {filename}")

def get_media_type(suffix: str) -> str:
    types = {
        '.pdf': 'application/pdf',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.txt': 'text/plain',
    }
    return types.get(suffix.lower(), 'application/octet-stream')

if FRONTEND_DIR.exists():
    if (FRONTEND_DIR / "styles").exists():
        app.mount("/styles", StaticFiles(directory=FRONTEND_DIR / "styles"), name="styles")
    if (FRONTEND_DIR / "scripts").exists():
        app.mount("/scripts", StaticFiles(directory=FRONTEND_DIR / "scripts"), name="scripts")
    
    # Mount assets unconditionally to debug 404
    assets_dir = FRONTEND_DIR / "assets"
    if not assets_dir.exists():
        print(f"WARNING: Assets directory not found at {assets_dir}")
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Trigger Reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
