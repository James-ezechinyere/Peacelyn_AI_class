import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- GRADE-LEVEL WORKSPACE CONFIGURATIONS ---

GRADE_WORKSPACES = {
    "JS1 (Grade 7)": {
        "mode": "image_studio",
        "title": "🎨 JS1 AI Image Generation Studio",
        "subtitle": "Describe characters, scenes, or posters in chat and bring your ideas to life with AI art.",
        "placeholder": "Describe the image you want to create (e.g., A futuristic Nigerian solar-powered school bus in Lagos, digital art)..."
    },
    "JS2 (Grade 8)": {
        "mode": "image_studio",
        "title": "💬 JS2 AI Exploration Chat",
        "subtitle": "Ask questions, brainstorm ideas, and practice clear instructions in a conversational chat.",
        "placeholder": "Ask anything or give the AI a creative task..."
    },
    "JS3 (Grade 9)": {
        "mode": "image_studio",
        "title": "🎨 JS3 AI Visual Design Studio",
        "subtitle": "Design concept art, product mockups, and visual stories through conversational image prompts.",
        "placeholder": "Describe the visual scene, lighting, and art style you want to generate..."
    },
    "SS1 (Grade 10)": {
        "mode": "ss1_web_studio",
        "title": "🚀 SS1 Collaborative Web Studio — School Project Showcase",
        "subtitle": "Claim a feature module and engineer the official school showcase portal (Grade 3 to SS2).",
        "placeholder": ""
    },
    "SS2 (Grade 11)": {
        "mode": "reasoning_agent",
        "title": "🔬 SS2 Deep Research & Reasoning Agent",
        "subtitle": "Conduct structured research, analyze complex topics, and draft well-reasoned essays with transparent step-by-step AI thinking.",
        "placeholder": "Enter a research topic, essay thesis, or complex analytical question..."
    }
}