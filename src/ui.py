import streamlit as st
import dotenv
dotenv.load_dotenv()

from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient
from planner.agent_planner import plan_and_retrieve
from utils.schema import find_missing_mandatory

from advisor.advisor_reasoner import (
    generate_advisor_output,
    generate_comparison_output,
    generate_competitor_analysis_output,
    generate_sector_screener_output,
    generate_sector_trend_output,
    generate_stock_news_output,
)

from risk.risk_engine import compute_risk_score
from risk.explainer import explain_result

# -------------------------------------------------
# INIT PIPELINE OBJECTS (ONCE PER SESSION)
# -------------------------------------------------
if "client" not in st.session_state:
    st.session_state.client = LLMClient()
    st.session_state.sf = SlotFiller(llm_client=st.session_state.client)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "pending_followup" not in st.session_state:
    st.session_state.pending_followup = None

# -------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------
st.set_page_config(page_title="Stock Risk Advisor", layout="centered")
st.title("📈 Stock Risk Advisor — Chatbot")

st.markdown(
    """
Ask about **any stock**, **sector**, **competitors**, or **portfolio guidance**.

Examples:
- *TCS or Infosys*
- *What is the risk?*
- *Energy sector stocks*
- *I have 5 lakh to invest*
"""
)

# -------------------------------------------------
# RENDER CHAT HISTORY
# -------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------------------------------
# USER INPUT
# -------------------------------------------------
user_input = st.chat_input("Ask a market or stock-related question...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Exit / reset
    if user_input.lower() in ("exit", "quit", "reset"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.session_state.pending_followup = None
        st.experimental_rerun()

    sf = st.session_state.sf

    with st.chat_message("assistant"):
        try:
            # -------------------------------------------------
            # HANDLE FOLLOW-UP ANSWER
            # -------------------------------------------------
            if st.session_state.pending_followup:
                combined_query = (
                    st.session_state.pending_query + " " + user_input
                )
                st.session_state.pending_followup = None
                st.session_state.pending_query = None
            else:
                combined_query = user_input

            # -------------------------------------------------
            # SLOT EXTRACTION (NON-BLOCKING)
            # -------------------------------------------------
            slots = sf.extract_slots(combined_query)

            missing = find_missing_mandatory(slots)
            if missing:
                followup = sf.generate_followup(slots)

                st.write(f"🤖 {followup}")

                st.session_state.pending_query = combined_query
                st.session_state.pending_followup = followup

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": followup
                })
                st.stop()

            # -------------------------------------------------
            # PLANNER
            # -------------------------------------------------
            context = plan_and_retrieve(slots)

            if "error" in context:
                st.error(f"Data retrieval error: {context['error']}")
                st.stop()

            mode = context.get("mode")

            # -------------------------------------------------
            # MODE HANDLERS
            # -------------------------------------------------
            if mode == "portfolio_guidance":
                text = (
                    f"With ₹{context['capital']}, it’s important to think about "
                    "your investment horizon and risk comfort.\n\n"
                    "You may explore diversified large-cap stocks or sector-based exposure.\n\n"
                    "Would you like short-term, medium-term, or long-term guidance?\n\n"
                    "⚠️ This is a data-based analytical insight, not financial advice."
                )
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            if mode == "stock_comparison":
                text = generate_comparison_output(context, context["language"])
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            if mode == "competitor_analysis":
                text = generate_competitor_analysis_output(context, context["language"])
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            if mode == "sector_screener":
                text = generate_sector_screener_output(context, context["language"])
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            if mode == "sector_trend":
                text = generate_sector_trend_output(context, context["language"])
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            if mode == "stock_news":
                text = generate_stock_news_output(context, context["language"])
                st.write(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
                st.stop()

            # -------------------------------------------------
            # SINGLE-STOCK MODES (price_trend / risk_analysis / buy_decision)
            # -------------------------------------------------
            analysis = compute_risk_score(context)

            explanation = explain_result(
                slots["stock_name"],
                analysis,
                context,
                slots.get("language", "en"),
            )

            advisor = generate_advisor_output(
                slots,
                context,
                analysis,
                explanation
            )

            st.write(advisor["advisor_text"])
            st.session_state.messages.append({
                "role": "assistant",
                "content": advisor["advisor_text"]
            })

        except Exception as e:
            st.error(f"Unexpected error: {e}")
