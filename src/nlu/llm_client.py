import os
import json
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Optional

BACKEND = os.getenv("NLU_BACKEND", "groq").lower()

class LLMClientBase:
    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        raise NotImplementedError

# Groq client
class OpenAIClient(LLMClientBase):
    def __init__(self, model: str = "mixtral-8x7b-32768"):
        self.model = model
        self.client = ChatGroq(
            model_name=self.model,
            temperature=0.0,
            api_key=os.getenv("GROQ_API_KEY")
        )

    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate completion using LangChain ChatGroq."""
        messages = [
            SystemMessage(content="You are a JSON extraction assistant."),
            HumanMessage(content=prompt)
        ]
        response = self.client.invoke(messages)
        return response.content

LLMClient = OpenAIClient
