from config import OPENROUTER_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
from ai_service.openrouter import OpenRouterProvider
from ai_service.groq import GroqProvider
from ai_service.gemini import GeminiProvider

def get_ai_service(platform_name: str):
    """Factory function to instantiate and return the requested AI provider service."""
    if platform_name == "OpenRouter":
        if not OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key is missing.")
        return OpenRouterProvider(api_key=OPENROUTER_API_KEY)
        
    elif platform_name == "Groq":
        if not GROQ_API_KEY:
            raise ValueError("Groq API key is missing.")
        return GroqProvider(api_key=GROQ_API_KEY)
        
    elif platform_name == "Gemini":
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key is missing.")
        return GeminiProvider(api_key=GEMINI_API_KEY)
        
    else:
        raise ValueError(f"Unsupported AI platform: {platform_name}")