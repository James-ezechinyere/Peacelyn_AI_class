from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], model_name: str, system_instruction: str = "") -> str:
        """Handles multi-turn conversational chat."""
        pass

    @abstractmethod
    def research_with_reasoning(self, messages: list[dict], model_name: str) -> tuple[str, str]:
        """Returns (thought_summary, final_research_response) for SS2."""
        pass

    @abstractmethod
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes | None, str]:
        """Returns (image_bytes, text_caption) for JS1/JS3."""
        pass