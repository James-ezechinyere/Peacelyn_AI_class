from openai import OpenAI
from ai_service.base import AIProvider
import os
import streamlit as st
from ai_service.image_gen import generate_open_source_image

class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)

    def chat(self, messages: list[dict], model_name: str = "llama-3.3-70b-versatile", system_instruction: str = "") -> str:
        sys_inst = system_instruction or "You are a helpful AI learning assistant for secondary school students."
        formatted = [{"role": "system", "content": sys_inst}] + [
            {"role": m["role"], "content": m["content"]} for m in messages if m.get("content")
        ]
        response = self.client.chat.completions.create(
            model=model_name or "llama-3.3-70b-versatile",
            messages=formatted,
            temperature=0.7
        )
        return response.choices[0].message.content

    def research_with_reasoning(self, messages: list[dict], model_name: str = "deepseek-r1-distill-llama-70b") -> tuple[str, str]:
        sys_inst = (
            "You are an academic Research & Writing Assistant for SS2 students. "
            "First enclose your step-by-step analytical reasoning inside <think>...</think> tags, "
            "then provide a structured, well-researched essay or report."
        )
        formatted = [{"role": "system", "content": sys_inst}] + [
            {"role": m["role"], "content": m["content"]} for m in messages if m.get("content")
        ]
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=formatted,
            temperature=0.4
        )
        raw = response.choices[0].message.content or ""
        if "<think>" in raw and "</think>" in raw:
            thought = raw.split("<think>")[1].split("</think>")[0].strip()
            final = raw.split("</think>")[1].strip()
            return thought, final
        return "", raw

    # Inside GroqProvider and OpenRouterProvider:
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes | None, str]:
        gemini_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
        if gemini_key:
            from ai_service.gemini import GeminiProvider
            return GeminiProvider(gemini_key).generate_image(prompt, aspect_ratio=aspect_ratio)
        return generate_open_source_image(prompt, aspect_ratio=aspect_ratio)