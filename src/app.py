import dotenv; dotenv.load_dotenv()
from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient
from planner.agent_planner import plan_and_retrieve
import json

def main():
    print("=== Stock Risk Agent — NLU + Planner Demo ===")
    client = LLMClient()
    sf = SlotFiller(llm_client=client)

    while True:
        q = input("\nYou: ").strip()
        if q.lower() in ("exit","quit"):
            break

        slots = sf.interactive_fill(q)
        print("\n✅ Extracted Slots:")
        print(json.dumps(slots, indent=2, ensure_ascii=False))

        context = plan_and_retrieve(slots)
        print("\n🧠 Planner Output:")
        print(json.dumps(context, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
