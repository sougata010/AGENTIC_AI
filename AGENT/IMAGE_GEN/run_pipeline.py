import os
import json
import subprocess
import sys
from dotenv import load_dotenv
from functions import (
    init_gemini_client,
    generate_full_pin_concept,
    build_super_prompt,
    generate_image_with_pollinations,
    get_latest_image,
    grade_image_quality,
    log_to_daily_jsonl
)

load_dotenv()
API = os.environ.get('POLLINATION_API_KEY')
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pinterest_images")
STRATEGY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "current_strategy.json")


def run_brain_agent(topic: str) -> dict:
    print("🧠 Phase 1: Planning...")
    
    client = init_gemini_client(temperature=0.7, response_mime_type="application/json")
    strategy_json = generate_full_pin_concept(client, topic)
    
    try:
        strategy = json.loads(strategy_json)
    except json.JSONDecodeError:
        print("❌ Failed to parse strategy JSON, retrying...")
        strategy_json = generate_full_pin_concept(client, topic)
        strategy = json.loads(strategy_json)
    
    with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2)
    
    print(f"✅ Strategy saved to {STRATEGY_FILE}")
    log_to_daily_jsonl({"phase": "planning", "topic": topic, "strategy": strategy})
    return strategy


def run_image_agent(strategy: dict) -> str:
    print("🎨 Phase 2: Executing (Media Gen)...")
    
    super_prompt = build_super_prompt(strategy)
    print(f"📝 Super Prompt: {super_prompt[:100]}...")
    
    image_path = generate_image_with_pollinations(super_prompt, api_key=API, folder=IMG_DIR)
    
    if image_path:
        print(f"✅ Image generated: {image_path}")
        log_to_daily_jsonl({"phase": "image_generation", "image_path": image_path, "prompt": super_prompt})
    else:
        print("❌ Image generation failed")
    
    return image_path


def run_critic_agent(image_path: str) -> dict:
    print("⚖️ Phase 3: Validating...")
    
    if not image_path:
        image_path = get_latest_image(IMG_DIR)
    
    if not image_path:
        print("❌ No image found to validate")
        return {"overall_score": 0, "error": "No image found"}
    
    client = init_gemini_client(temperature=0.3)
    result = grade_image_quality(image_path, client)
    
    print(f"📊 Grading Result: {result}")
    log_to_daily_jsonl({"phase": "validation", "image_path": image_path, "result": result})
    
    return result


def run_full_pipeline(initial_topic: str, max_retries: int = 3) -> dict:
    print(f"\n{'='*50}")
    print(f"🚀 Starting Pipeline for: {initial_topic}")
    print(f"{'='*50}\n")
    
    for attempt in range(max_retries):
        print(f"\n--- Attempt {attempt + 1}/{max_retries} ---\n")
        
        # Phase 1: Planning
        strategy = run_brain_agent(initial_topic)
        
        # Phase 2: Image Generation
        image_path = run_image_agent(strategy)
        
        if not image_path:
            print("⚠️ Image generation failed, retrying...")
            continue
        
        # Phase 3: Validation
        result = run_critic_agent(image_path)
        final_score = result.get("overall_score", 0)
        
        if final_score >= 7:
            print(f"\n✅ Success! Final Score: {final_score}")
            return {
                "success": True,
                "score": final_score,
                "image_path": image_path,
                "strategy": strategy,
                "grading": result
            }
        else:
            print(f"⚠️ Score {final_score} too low. Retrying...")
    
    print(f"\n❌ Failed after {max_retries} attempts")
    return {"success": False, "error": "Max retries exceeded"}


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "Cozy Gaming Setup"
    result = run_full_pipeline(topic)
    print(f"\n{'='*50}")
    print("📋 Final Result:")
    print(json.dumps(result, indent=2, default=str))
