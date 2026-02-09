import sys
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.main import app
from app.config import settings

def verify_production():
    print("🔍 Verifying Production Setup...")
    
    # 1. Check Middleware
    middleware_types = [m.cls for m in app.user_middleware]
    
    if GZipMiddleware in middleware_types:
        print("✅ GZipMiddleware present")
    else:
        print("❌ GZipMiddleware MISSING")
        
    if CORSMiddleware in middleware_types:
        print("✅ CORSMiddleware present")
    else:
        print("❌ CORSMiddleware MISSING")
        
    # 2. Check Config
    print(f"ℹ️  Production Mode: {settings.PRODUCTION}")
    print(f"ℹ️  Allowed Origins: {settings.ALLOWED_ORIGINS}")
    
    if settings.PRODUCTION:
        print("✅ Production flag is set (Ensure this is intended)")
    else:
        print("ℹ️  Running in Development Mode (Production flag is False)")

    # 3. Check Exception Handlers
    handlers = app.exception_handlers
    if Exception in handlers:
        print("✅ Global Exception Handler registered")
    else:
        print("❌ Global Exception Handler MISSING")

    print("🚀 Verification Complete")

if __name__ == "__main__":
    verify_production()
