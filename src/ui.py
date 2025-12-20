import streamlit as st
import dotenv
dotenv.load_dotenv()

from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient
from planner.agent_planner import plan_and_retrieve
from risk.risk_engine import compute_risk_score
from risk.explainer import explain_result
from advisor.advisor_reasoner import generate_advisor_output
import json

# ---------------------------
# INIT PIPELINE OBJECTS ONCE
# ---------------------------
if "client" not in st.session_state:
    st.session_state.client = LLMClient()
    st.session_state.sf = SlotFiller(llm_client=st.session_state.client)

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.set_page_config(page_title="Stock Risk Advisor", layout="centered")
st.title("📈 Stock Risk Advisor — Chatbot")

st.markdown(
    """
    Ask about **any stock**, or ask for a **low-risk stock screener**.
    Type *exit* or *quit* to clear the conversation.
    """
)

# Conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------
# USER INPUT
# ---------------------------
user_input = st.chat_input("Ask about a stock, e.g., 'Analyze AAPL risk'")

if user_input:
    # Render user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Exit command
    if user_input.lower() in ("exit", "quit"):
        st.session_state.messages.append({"role": "assistant", "content": "Conversation cleared."})
        st.session_state.messages = []
        st.experimental_rerun()

    # ---------------------------
    # RUN PIPELINE
    # ---------------------------
    sf = st.session_state.sf

    with st.chat_message("assistant"):
        try:
            # 1️⃣ Slot Filling
            slots = sf.interactive_fill(user_input)
            st.write("### 🎯 Extracted Slots")
            st.json(slots)

            # 2️⃣ Planner
            context = plan_and_retrieve(slots)

            # 3️⃣ Handle errors
            if "error" in context:
                st.error(f"Data retrieval error: {context['error']}")
                st.stop()

            # 4️⃣ Screener Mode
            if context.get("mode") == "screener":
                st.write("### 📊 Suggested Low-Risk Stocks")
                for item in context["suggestions"]:
                    ticker = item["ticker"]
                    risk = item["risk"]["risk_score"]
                    cls = item["risk"]["classification"]
                    st.write(f"- **{ticker}** — Risk: `{risk}` ({cls})")

                st.info("⚠️ These are analytical insights, not financial advice.")
                advisor_output = "Provided low-risk stock screener results."

                st.session_state.messages.append(
                    {"role": "assistant", "content": advisor_output}
                )
                st.stop()

            # 5️⃣ Single-Stock Mode → Risk Engine
            analysis = compute_risk_score(context)

            # 6️⃣ Explanation Layer
            explanation = explain_result(
                slots["stock_name"],
                analysis,
                context,
                slots.get("language", "en"),
            )

            # 7️⃣ Final Advisor Layer
            advisor = generate_advisor_output(slots, context, analysis, explanation)

            # 8️⃣ Display
            st.write("### 🧠 Advisor Output")
            st.write(advisor["advisor_text"])

            st.write("### 📊 JSON Summary")
            st.json(advisor["advisor_json"])

            st.session_state.messages.append(
                {"role": "assistant", "content": advisor["advisor_text"]}
            )

        except Exception as e:
            st.error(f"Unexpected error: {e}")
