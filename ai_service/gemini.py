import os
import json
from google import genai
from google.genai import types
from ai_service.base import AIProvider
from config import SYSTEM_INSTRUCTION, JUDGE_SYSTEM_PROMPT

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        # Initialize official Google GenAI client
        self.client = genai.Client(api_key=api_key)

    def generate_response(self, prompt: str, model_name: str) -> str:
        # Use stable Gemini model ID
        model = model_name if model_name else "gemini-2.5-flash"
        
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            ),
        )
        return response.text

    def evaluate_prompt(self, student_prompt: str, llm_output: str, grade_class: str, capstone_info: dict) -> tuple:
                
        judge_user_prompt = f"Student Class: {grade_class}\nStudent Prompt: {student_prompt}\nAI Generated Response: {llm_output}"

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=judge_user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json"
            ),
        )
        
        eval_data = json.loads(response.text.strip())
        return float(eval_data.get("score", 50)), eval_data