import os
import json
from typing import Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()

BACKEND = os.getenv("NLU_BACKEND", "groq").lower()
print(f"[INFO] Using LLM backend: {BACKEND}")

class LLMClientBase:
    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        raise NotImplementedError

class GroqClient(LLMClientBase):
    """
    LLM client wrapper for Groq models (via langchain_groq).
    """
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in environment.")
        self.model = model
        self.client = ChatGroq(
            model_name=self.model,
            temperature=temperature,
            api_key=api_key
        )

    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate completion using Groq."""
        messages = [
            SystemMessage(content="You are a JSON extraction assistant."),
            HumanMessage(content=prompt)
        ]
        response = self.client.invoke(messages)
        # Some versions return .content, others .text
        text = getattr(response, "content", None) or getattr(response, "text", None)
        if not text:
            raise ValueError("Groq returned empty response")
        return text.strip()

LLMClient = GroqClient
