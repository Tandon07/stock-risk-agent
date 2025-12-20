import dotenv; dotenv.load_dotenv()
from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient
from planner.agent_planner import plan_and_retrieve
from risk.risk_engine import compute_risk_score
from risk.explainer import explain_result
from advisor.advisor_reasoner import generate_advisor_output
import json

def main():
    print("=== Stock Risk Advisor — Full Pipeline ===")
    client = LLMClient()
    sf = SlotFiller(llm_client=client)

    while True:
        q = input("\nYou: ").strip()
        if q.lower() in ("exit", "quit"):
            break

        # 1️⃣ Slot Filling
        slots = sf.interactive_fill(q)
        print("\n[DEBUG] Extracted Slots:", json.dumps(slots, indent=2))   # ⬅️ ADD THIS

        # 2️⃣ Planner decides mode (single-stock / screener)
        context = plan_and_retrieve(slots)

        # 3️⃣ Handle errors
        if "error" in context:
            print(f"⚠️ Data retrieval error: {context['error']}")
            continue

        # 4️⃣ Handle STOCK SCREENER mode FIRST
        if context.get("mode") == "screener":
            print("\n📊 Suggested Stocks (Low-Risk Ranked):")
            for item in context["suggestions"]:
                ticker = item["ticker"]
                risk = item["risk"]["risk_score"]
                cls = item["risk"]["classification"]
                print(f"- {ticker}: Risk {risk} ({cls})")

            print("\n⚠️ These are analytical insights, not financial advice.")
            print("--------------------------------------------------------")

            # IMPORTANT: Skip normal risk-engine flow
            continue

        # 5️⃣ Normal Single-Stock Mode → Risk Engine
        analysis = compute_risk_score(context)

        # 6️⃣ Explanation Layer
        explanation = explain_result(
            slots["stock_name"],
            analysis,
            context,
            slots.get("language", "en")
        )

        # 7️⃣ Final LLM Advisor Layer (Summarization, Reasoning)
        advisor = generate_advisor_output(slots, context, analysis, explanation)

        # 8️⃣ Display Output
        print("\n🧠 Advisor Output:")
        print(advisor["advisor_text"])

        print("\n📊 JSON Summary:")
        print(json.dumps(advisor["advisor_json"], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
