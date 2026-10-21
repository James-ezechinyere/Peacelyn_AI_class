from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, model_name: str) -> str:
        """Sends student prompt to the LLM and returns the text response."""
        pass

    @abstractmethod
    def evaluate_prompt(self, student_prompt: str, llm_output: str, grade_class: str, capstone_info: dict) -> tuple:
        """Runs the LLM Judge evaluation and returns (score, evaluation_dict)."""
        pass