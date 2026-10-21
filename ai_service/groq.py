import json
from openai import OpenAI
from ai_service.base import AIProvider
from config import SYSTEM_INSTRUCTION, JUDGE_SYSTEM_PROMPT

class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
        )

    def generate_response(self, prompt: str, model_name: str) -> str:
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

    def evaluate_prompt(self, student_prompt: str, llm_output: str, grade_class: str, capstone_info: dict) -> tuple:
        
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Student Prompt: {student_prompt}\nOutput: {llm_output}"}
            ],
            temperature=0.2
        )
        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:-3].strip()
        eval_data = json.loads(raw_json)
        return float(eval_data.get("score", 50)), eval_data