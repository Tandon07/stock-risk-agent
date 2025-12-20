# import dotenv; dotenv.load_dotenv()
# from nlu.slot_filler import SlotFiller
# from nlu.llm_client import LLMClient
# from planner.agent_planner import plan_and_retrieve
# import json

# def main():
#     print("=== Stock Risk Agent — NLU + Planner Demo ===")
#     client = LLMClient()
#     sf = SlotFiller(llm_client=client)

#     while True:
#         q = input("\nYou: ").strip()
#         if q.lower() in ("exit","quit"):
#             break

#         slots = sf.interactive_fill(q)
#         print("\nExtracted Slots:")
#         print(json.dumps(slots, indent=2, ensure_ascii=False))

#         context = plan_and_retrieve(slots)
#         print("\nPlanner Output:")
#         print(json.dumps(context, indent=2, ensure_ascii=False))

# if __name__ == "__main__":
#     main()
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
        if q.lower() in ("exit","quit"):
            break

        slots = sf.interactive_fill(q)
        context = plan_and_retrieve(slots)
        if "error" in context:
            print(f"⚠️ Data retrieval error: {context['error']}")
            continue

        analysis = compute_risk_score(context)
        explanation = explain_result(slots["stock_name"], analysis, context, slots.get("language", "en"))
        advisor = generate_advisor_output(slots, context, analysis, explanation)

        print("\n🧠 Advisor Output:")
        print(advisor["advisor_text"])
        print("\n📊 JSON Summary:")
        print(json.dumps(advisor["advisor_json"], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

# import streamlit as st
# import json
# import dotenv; dotenv.load_dotenv()

# from nlu.slot_filler import SlotFiller
# from nlu.llm_client import LLMClient
# from planner.agent_planner import plan_and_retrieve
# from risk.risk_engine import compute_risk_score
# from risk.explainer import explain_result
# from advisor.advisor_reasoner import generate_advisor_output


# # -------------------- PAGE CONFIG --------------------

# st.set_page_config(
#     page_title="Stock Risk Advisor",
#     page_icon="📈",
#     layout="centered",
# )

# st.title("📈 Stock Risk Advisor")
# st.write("Ask about any stock and receive a risk-based advisor response.")


# # -------------------- AGENT SETUP --------------------

# client = LLMClient()
# slot_filler = SlotFiller(llm_client=client)


# # -------------------- SESSION STATE ------------------

# if "chat" not in st.session_state:
#     st.session_state.chat = []


# # -------------------- CHAT DISPLAY -------------------

# with st.container():
#     for msg in st.session_state.chat:
#         if msg["role"] == "user":
#             st.markdown(f"**You:** {msg['content']}")
#         else:
#             st.markdown(f"**Advisor:**\n\n{msg['content']}")
#         st.divider()


# # -------------------- USER INPUT ---------------------

# user_input = st.text_area(
#     "Your message",
#     placeholder="e.g. Analyze risk for Apple stock",
# )

# send = st.button("Send")


# # -------------------- CHAT LOGIC ---------------------

# if send and user_input.strip():

#     # ---- Store user message
#     st.session_state.chat.append({
#         "role": "user",
#         "content": user_input
#     })

#     try:
#         slots = slot_filler.interactive_fill(user_input)
#         context = plan_and_retrieve(slots)

#         if "error" in context:
#             bot_response = f"⚠️ Data retrieval error: {context['error']}"

#         else:
#             analysis = compute_risk_score(context)
#             explanation = explain_result(
#                 slots["stock_name"],
#                 analysis,
#                 context,
#                 slots.get("language", "en")
#             )

#             advisor = generate_advisor_output(
#                 slots, context, analysis, explanation
#             )

#             advisor_text = advisor["advisor_text"]
#             advisor_json = json.dumps(
#                 advisor["advisor_json"],
#                 indent=2,
#                 ensure_ascii=False
#             )

#             bot_response = f"""
# 🧠 **Advisor Output**

# {advisor_text}

# 📊 **Risk Summary (JSON)**

# ```json
# {advisor_json}
# """
#     except Exception as e:
#         bot_response = f"❗ Unexpected error: {e}"

#     # ---- Store assistant message
#     st.session_state.chat.append({
#         "role": "assistant",
#         "content": bot_response
#     })

#     # ---- Rerun (input clears automatically)
#     st.rerun()
