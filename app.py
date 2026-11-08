import os
import streamlit as st
import core

st.set_page_config(page_title="Nyaya Saathi – AI Legal Helper (India)", page_icon="⚖️", layout="wide")


def get_api_key():
    try:
        k = st.secrets["GEMINI_API_KEY"]
        if k:
            return k
    except Exception:  # no secrets file present
        pass
    k = os.getenv("GEMINI_API_KEY")
    if k:
        return k
    return st.sidebar.text_input("Enter Gemini API Key", type="password") or None


st.title("⚖️ Nyaya Saathi – AI Legal Helper")
st.warning(core.DISCLAIMER)
st.sidebar.header("Settings")
key = get_api_key()
st.sidebar.caption(f"Model: {core.MODEL} (change via LAWYER_MODEL env var)")
if not key:
    st.info("🔑 Please enter your Gemini API key in the sidebar (or set GEMINI_API_KEY) to begin. "
            "Free keys: Google AI Studio.")
    st.stop()

for k, v in {"summary": "", "advice": "", "notice": "", "chat": []}.items():
    st.session_state.setdefault(k, v)

t1, t2, t3, t4 = st.tabs(["1️⃣ Build my case", "2️⃣ My rights & options", "3️⃣ Draft document", "4️⃣ Practise negotiation"])

with t1:
    story = st.text_area("Tell your story in your own words (Hindi / English / Hinglish is fine)", height=220,
                         placeholder="e.g. Landlord ne 3 mahine se deposit nahi lautaya...")
    if st.button("Create case summary", type="primary") and story.strip():
        flags = core.escalation_flags(story)
        if flags:
            st.error(f"🚨 Your message mentions {', '.join(flags)}. This may need a real lawyer or "
                     "legal aid (NALSA helpline 15100) soon. You can still continue below for general help.")
        with st.spinner("Organising your case..."):
            st.session_state.summary = core.case_summary(key, story)
        st.session_state.advice = st.session_state.notice = ""
        st.session_state.chat = []
    if st.session_state.summary:
        st.markdown(st.session_state.summary)
        st.session_state.summary = st.text_area("✏️ Edit the summary if anything is wrong (the AI uses this "
                                                "version from now on)", st.session_state.summary, height=200)

with t2:
    if not st.session_state.summary:
        st.info("Build your case in tab 1 first.")
    else:
        if st.button("Explain my rights and options"):
            with st.spinner("Thinking..."):
                st.session_state.advice = core.advice(key, st.session_state.summary)
        st.markdown(st.session_state.advice)

with t3:
    if not st.session_state.summary:
        st.info("Build your case in tab 1 first.")
    else:
        doc_type = st.selectbox("Document", ["Legal Notice", "Consumer Complaint (for Consumer Commission)",
                                             "Demand Letter for Unpaid Wages"])
        details = st.text_area("Your name/address and the other party's name/address (leave blank for placeholders)")
        if st.button("Draft document"):
            with st.spinner("Drafting..."):
                st.session_state.notice = core.legal_notice(key, st.session_state.summary,
                                                            details or "[NOT PROVIDED]", doc_type)
        if st.session_state.notice:
            st.text_area("Draft (review every line before sending)", st.session_state.notice, height=450)
            st.download_button("Download .txt", st.session_state.notice, "legal_draft.txt")

with t4:
    if not st.session_state.summary:
        st.info("Build your case in tab 1 first.")
    else:
        role = st.selectbox("The AI plays:", ["landlord", "employer", "e-commerce customer-care executive"])
        st.caption("Type COACH at any time to get feedback on how you are doing.")
        for r, t in st.session_state.chat:
            st.chat_message("user" if r == "user" else "assistant").write(t)
        msg = st.chat_input("Say something to the other party...")
        if msg:
            st.chat_message("user").write(msg)
            with st.spinner(""):
                reply = core.counterparty_reply(key, st.session_state.summary, role, st.session_state.chat, msg)
            st.session_state.chat += [("user", msg), ("model", reply)]
            st.chat_message("assistant").write(reply)
        if st.button("Reset chat"):
            st.session_state.chat = []
            st.rerun()
