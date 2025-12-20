# src/nlu/slot_filler.py
import json
import re
from typing import Optional
from .prompts import SLOT_EXTRACTION_PROMPT
from .llm_client import LLMClient

from utils.lang_detect import detect_lang
from utils.schema import SlotFrame, find_missing_mandatory

class SlotFiller:
    def __init__(self, llm_client: Optional[LLMClient]=None):
        self.llm = llm_client or LLMClient()
        # helper for rupee tokens to numbers
        self._num_pattern = re.compile(r"₹\s*([\d,]+)|(\d{2,7})\s*(rs|rupee|₹)?", re.I)

    def _normalize_json_text(self, text: str) -> str:
        """
        Clean assistant output to try to extract only JSON.
        """
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return text
        return text[start:end+1]

    def _parse_json(self, raw_text: str):
        try:
            cleaned = self._normalize_json_text(raw_text)
            return json.loads(cleaned)
        except Exception:
            t = raw_text.replace("'", '"')
            t = re.sub(r",\s*}", "}", t)
            t = re.sub(r",\s*]", "]", t)
            try:
                return json.loads(self._normalize_json_text(t))
            except Exception:
                return None

    def extract_slots(self, user_query: str):
        """
        Calls LLM to extract slots according to SLOT_EXTRACTION_PROMPT.
        """
        prompt = SLOT_EXTRACTION_PROMPT.format(query=user_query)
        raw = self.llm.complete(prompt, temperature=0.0)
        parsed = self._parse_json(raw)

        # fallback: attach detected language
        if parsed is None:
            parsed = {"intent": None, "stock_name": None, "language": detect_lang(user_query)}
        else:
            if "language" not in parsed or not parsed.get("language"):
                parsed["language"] = detect_lang(user_query)

        return parsed

    def generate_followup(self, slots: dict):
        """
        Create a focused follow-up question for missing mandatory slots.
        (stock_screener should NOT ask for stock_name)
        """
        missing = find_missing_mandatory(slots)
        if not missing:
            return None

        lang = slots.get("language", "en")

        # ⬅️ UPDATED: stock_screener DOES NOT require stock_name
        if slots.get("intent") == "stock_screener":
            # Only ask for missing intent (rare)
            missing = [m for m in missing if m != "stock_name"]

        if not missing:
            return None

        # Ask for the first missing slot
        key = missing[0]

        if lang == "hi":
            mapping = {
                "stock_name": "कृपया बताइए आप किस कंपनी/स्टॉक के बारे में पूछ रहे हैं?",
                "intent": "क्या आप जोखिम, खरीदने का मौका या ट्रेंड जानना चाह रहे हैं?"
            }
        else:
            mapping = {
                "stock_name": "Which stock or company are you referring to?",
                "intent": "Would you like to know about risk, a buy opportunity, or trend?"
            }
        return mapping.get(key, f"Please provide {key}")

    def interactive_fill(self, initial_query: str, respond_fn=None):
        """
        Interactive filling with LLM + follow-up questions.
        """
        slots = self.extract_slots(initial_query)

        # loop until mandatory slots present
        while True:
            missing = find_missing_mandatory(slots)

            # ⬅️ UPDATED: For stock_screener intent, stock_name is NOT mandatory
            if slots.get("intent") == "stock_screener":
                missing = [m for m in missing if m != "stock_name"]

            if not missing:
                break

            followup_q = self.generate_followup(slots)
            if respond_fn:
                answer = respond_fn(followup_q)
            else:
                print(f"\nAgent: {followup_q}")
                answer = input("You: ").strip()

            combined = (slots.get("_original_query", initial_query) if slots.get("_original_query") else initial_query) \
                       + " " + answer

            slots = self.extract_slots(combined)
            slots["_original_query"] = combined

        # Validate with pydantic — fill defaults if needed
        try:
            validated = SlotFrame(**slots)
            return validated.dict()
        except Exception:
            # ensure language
            if not slots.get("language"):
                slots["language"] = detect_lang(initial_query)
            # ensure intent fallback
            if not slots.get("intent"):
                slots["intent"] = "risk_analysis"
            validated = SlotFrame(**slots)
            return validated.dict()
