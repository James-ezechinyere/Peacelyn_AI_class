import json
from openai import OpenAI
from ai_service.base import AIProvider
from config import SYSTEM_INSTRUCTION, JUDGE_SYSTEM_PROMPT

class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def generate_response(self, prompt: str, model_name: str) -> str:
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            extra_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "AI Prompt Lab"}
        )
        return response.choices[0].message.content

    def evaluate_prompt(self, student_prompt: str, llm_output: str, grade_class: str, capstone_info: dict) -> tuple:
        
        
        judge_user_prompt = f"Student Class: {grade_class}\nStudent Prompt: {student_prompt}\nAI Generated Response: {llm_output}"

        response = self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": judge_user_prompt}
            ],
            temperature=0.2,
            extra_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "AI Prompt Lab"}
        )
        
        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:-3].strip()
        elif raw_json.startswith("```"):
            raw_json = raw_json[3:-3].strip()

        eval_data = json.loads(raw_json)
        return float(eval_data.get("score", 50)), eval_data