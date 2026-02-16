# src/nlu/slot_filler.py
import json
import re
from typing import Optional
from .prompts import SLOT_EXTRACTION_PROMPT
from .llm_client import LLMClient

from utils.lang_detect import detect_lang
from utils.schema import SlotFrame, find_missing_mandatory


class SlotFiller:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        # helper for rupee tokens to numbers
        self._num_pattern = re.compile(r"₹\s*([\d,]+)|(\d{2,7})\s*(rs|rupee|₹)?", re.I)

    # --------------------------------------------------
    # JSON NORMALIZATION
    # --------------------------------------------------
    def _normalize_json_text(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return text
        return text[start:end + 1]

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

    # --------------------------------------------------
    # SLOT EXTRACTION
    # --------------------------------------------------
    def extract_slots(self, user_query: str):
        print("\n================ SLOT FILLER START ================")
        print("[SlotFiller] User query:", user_query)

        prompt = SLOT_EXTRACTION_PROMPT.format(query=user_query)

        raw = self.llm.complete(prompt, temperature=0.0)

        print("\n[SlotFiller] RAW LLM OUTPUT ↓↓↓")
        print(raw)
        print("[SlotFiller] RAW LLM OUTPUT ↑↑↑\n")

        parsed = self._parse_json(raw)

        print("[SlotFiller] PARSED JSON:", parsed)

        # ---------- FALLBACK ----------
        if parsed is None or not isinstance(parsed, dict):
            print("[SlotFiller] ❌ JSON parsing failed. Using fallback.")
            parsed = {
                "intent": None,
                "stock_name": None,
                "commodity": None,
                "sector": None,
                "capital": None,
                "target_return_pct": None,
                "language": detect_lang(user_query),
                "action": "unknown",
            }

        # ---------- MULTI-STOCK SPLIT ----------
        if isinstance(parsed.get("stock_name"), str):
            text = parsed["stock_name"].lower()
            if any(x in text for x in [" vs ", " or ", ",", "compare"]):
                names = re.split(r" vs | or |, ", parsed["stock_name"], flags=re.I)
                parsed["stock_name"] = [n.strip() for n in names if n.strip()]

        # ---------- INFO GENERAL OVERRIDE ----------
        q = user_query.lower()
        if any(k in q for k in ["how to", "process", "procedure", "open", "transfer", "change", "documents", "kyc", "demat"]):
            if parsed.get("intent") == "info_general":
                parsed["query_text"] = user_query
                parsed["stock_name"] = None
                parsed["commodity"] = None
                parsed["sector"] = None

        # ---------- COMMODITY SAFETY OVERRIDE ----------
        commodity_keywords = ["gold", "silver", "crude", "oil", "gas", "copper"]
        for c in commodity_keywords:
            if c in q:
                if parsed.get("intent") in ["price_trend", "risk_analysis", None]:
                    print("[SlotFiller] ⚠️ Overriding intent → commodity_trend")
                    parsed["intent"] = "commodity_trend"
                parsed["commodity"] = c
                parsed["stock_name"] = None
                break

        # ---------- LANGUAGE ----------
        if not parsed.get("language"):
            parsed["language"] = detect_lang(user_query)

        print("[SlotFiller] FINAL SLOTS:", parsed)
        print("================ SLOT FILLER END =================\n")

        return parsed

    # --------------------------------------------------
    # FOLLOW-UP GENERATION
    # --------------------------------------------------
    def generate_followup(self, slots: dict):
        missing = find_missing_mandatory(slots)
        if not missing:
            return None

        lang = slots.get("language", "en")
        key = missing[0]

        if lang == "hi":
            mapping = {
                "stock_name": "कृपया बताइए आप किस कंपनी/स्टॉक के बारे में पूछ रहे हैं?",
                "sector": "कृपया बताइए आप किस सेक्टर के बारे में पूछ रहे हैं?",
                "commodity": "कृपया बताइए आप किस कमोडिटी के बारे में पूछ रहे हैं?",
                "capital": "कृपया बताइए आप कितनी राशि निवेश करना चाहते हैं?",
                "query_text": "कृपया अपना सवाल थोड़ा और स्पष्ट करें।",
                "intent": "आप क्या जानना चाहते हैं — ट्रेंड, जोखिम, तुलना या जानकारी?",
            }
        else:
            mapping = {
                "stock_name": "Which stock or company are you referring to?",
                "sector": "Which sector are you referring to?",
                "commodity": "Which commodity are you asking about?",
                "capital": "How much capital are you planning to invest?",
                "query_text": "Could you please clarify your question?",
                "intent": "What would you like to know — trend, risk, comparison, or general info?",
            }

        return mapping.get(key, f"Please provide {key}")

    # --------------------------------------------------
    # INTERACTIVE LOOP
    # --------------------------------------------------
    def interactive_fill(self, initial_query: str, respond_fn=None):
        slots = self.extract_slots(initial_query)

        while True:
            missing = find_missing_mandatory(slots)
            if not missing:
                break

            followup_q = self.generate_followup(slots)
            if respond_fn:
                answer = respond_fn(followup_q)
            else:
                print(f"\nAgent: {followup_q}")
                answer = input("You: ").strip()

            combined = (slots.get("_original_query", initial_query) if slots.get("_original_query") else initial_query) + " " + answer

            slots = self.extract_slots(combined)
            slots["_original_query"] = combined

        # Validate with pydantic
        try:
            validated = SlotFrame(**slots)
            return validated.dict()
        except Exception as e:
            print("[SlotFiller] ⚠️ Validation error, applying fallback:", e)

            if not slots.get("language"):
                slots["language"] = detect_lang(initial_query)
            if not slots.get("intent"):
                slots["intent"] = "risk_analysis"

            validated = SlotFrame(**slots)
            return validated.dict()
