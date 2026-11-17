from google import genai
from google.genai import types
from ai_service.base import AIProvider
from ai_service.image_gen import generate_open_source_image

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def _format_history(self, messages: list[dict]) -> list[types.Content]:
        formatted = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            text_content = msg.get("content", "")
            if text_content:
                formatted.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=text_content)])
                )
        return formatted

    def chat(self, messages: list[dict], model_name: str = "gemini-2.5-flash", system_instruction: str = "") -> str:
        model = model_name or "gemini-2.5-flash"
        sys_inst = system_instruction or "You are a helpful, encouraging AI learning assistant for secondary school students."
        
        response = self.client.models.generate_content(
            model=model,
            contents=self._format_history(messages),
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                temperature=0.7,
            ),
        )
        return response.text or ""

    def research_with_reasoning(self, messages: list[dict], model_name: str = "gemini-2.5-flash") -> tuple[str, str]:
        research_system = (
            "You are an academic Research & Writing Assistant for senior secondary (SS2) students. "
            "Break down complex topics rigorously, verify assumptions, structure arguments with clear headings, "
            "evidence, counterarguments, and academic clarity. Help the student research, outline, and write."
        )
        
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=self._format_history(messages),
            config=types.GenerateContentConfig(
                system_instruction=research_system,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2048,
                    include_thoughts=True
                ),
            ),
        )

        thoughts = []
        answer_parts = []
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if getattr(part, "thought", False):
                    thoughts.append(part.text)
                elif part.text:
                    answer_parts.append(part.text)

        thought_text = "\n\n".join(thoughts).strip()
        final_text = "\n\n".join(answer_parts).strip() or (response.text or "")
        return thought_text, final_text

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes | None, str]:
        """
        1. Primary: Tries Gemini native image generation first.
        2. Fallback: Automatically falls back to FLUX (Pollinations) if Gemini fails or hits 429 quota.
        """
        gemini_image_models = ["gemini-3.1-flash-image", "gemini-2.5-flash-image"]

        for model_id in gemini_image_models:
            try:
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                    ),
                )
                img_bytes = None
                caption_parts = []

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if getattr(part, "thought", False):
                            continue
                        if part.inline_data and part.inline_data.data:
                            img_bytes = part.inline_data.data
                        elif part.text:
                            caption_parts.append(part.text)

                if img_bytes:
                    caption = "\n".join(caption_parts).strip() or f"✨ Generated with **Gemini** ({aspect_ratio})"
                    return img_bytes, caption

            except Exception:
                # If Gemini hits 429 quota, rate limit, or error, try next Gemini model or fall back to FLUX
                continue

        # --- AUTOMATIC FALLBACK TO FLUX & POLLINATIONS ---
        return generate_open_source_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            fallback_reason="gemini_unavailable"
        )