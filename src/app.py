# src/app.py
import os
from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient

def main():
    print("=== Stock Risk Agent — Slot Filler Demo ===")
    print("Type 'exit' to quit.")
    client = LLMClient()
    sf = SlotFiller(llm_client=client)
    while True:
        q = input("\nYou: ").strip()
        if not q or q.lower() in ("exit","quit"):
            break
        result = sf.interactive_fill(q)
        print("\n--- Parsed Slots ---")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
