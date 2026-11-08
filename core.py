"""Core logic (no Streamlit) so app.py and run_tests.py share the same prompts.
To swap the model/provider, change MODEL or rewrite only `llm()`."""
import os, re, time
from google import genai
from google.genai import types

MODEL = os.getenv("LAWYER_MODEL", "gemini-3.8-flash")
FALLBACK = ("I do not have enough specific statutory context for this exact clause; "
            "please consult a licensed advocate.")
DISCLAIMER = ("⚠️ This is an informational AI tool, not legal advice or counsel from a licensed "
              "Indian advocate. Verify everything with a qualified lawyer before acting.")

# Small allow-list of law the model may name. Anything outside it must NOT be cited by section.
KB = """
ALLOWED REFERENCES (name these; do NOT cite any section number not listed here):
- Consumer Protection Act, 2019: complaint can be filed in the District/State/National Consumer
  Commission depending on value; Section 35 = how a consumer files a complaint; Section 69 = 2-year
  limitation (Commission may excuse delay with reasons). Filing online is possible via the e-Daakhil portal.
  A legal notice is NOT mandatory before a consumer complaint but is good practice.
- Consumer Protection (E-Commerce) Rules, 2020: duties of e-commerce entities, incl. grievance officer
  and acknowledging complaints within a set time. (No rule numbers.)
- National Consumer Helpline (1915) / NCH portal for pre-litigation grievance.
- Tenancy: rent control is a STATE subject. The Model Tenancy Act 2021 is only a template for states
  and applies only where a state has adopted it. Karnataka has its own Karnataka Rent Act, 1999.
  Security deposit rules depend on the state law and the signed rent agreement. (No section numbers.)
- Unpaid wages: Payment of Wages Act 1936 / Code on Wages 2019 (central labour codes; their
  commencement status and state rules must be verified). Remedy: written demand, complaint to the
  Labour Commissioner/Labour Department, and Labour Court. (No section numbers.)
- Indian Contract Act 1872 (general: agreements are enforceable; breach can lead to a civil claim).
- Free legal aid: District/State Legal Services Authority (NALSA 15100 helpline).
- Money recovery suit in civil court exists; court fees and limitation (generally 3 years for money
  claims, verify) apply.
Anything else: say "%s"
""" % FALLBACK

BASE = f"""You are 'Nyaya Saathi', an informational legal-help assistant for ordinary people in India.
RULES (strict):
1. NEVER invent acts, section numbers, rules or court cases. Use ONLY the allowed references below.
   Do not cite any case law. If unsure, output exactly: "{FALLBACK}"
2. Reply in the user's language (English, Hindi, or Hinglish in the same script they used). Use simple words.
3. Never promise outcomes. Say 'you may be able to', not 'you will win'.
4. If the matter is criminal, involves arrest/police/FIR, court summons, claims over Rs 50 lakh, more than one
   state, property title, family/custody law, or a deadline that may expire, begin with a line
   "🚨 LAWYER RECOMMENDED:" and why.
5. Do not invent facts. Mark missing facts as [NOT PROVIDED].
{KB}"""

SUMMARY_P = """Turn the user's messy story into a structured case file with exactly these headings:
## What happened (3-6 plain bullet points, chronological)
## Key dates (table: date | event; write [NOT PROVIDED] if unknown)
## Parties & amount involved
## Evidence available (what they have) and ## Evidence to collect (what they should gather)
## Questions I still need answered (max 4)
USER STORY:\n"""

ADVICE_P = """Using the case file below, give plain-language guidance with headings:
## Where you stand (honest strengths AND weaknesses)
## Your options (ordered cheapest/fastest first, each with what to do and rough effort)
## Which Indian law applies (only from allowed references; else the fallback sentence)
## Deadlines to watch
## When you must see a real lawyer
End with 2-3 next steps for this week.
CASE FILE:\n"""

NOTICE_P = """Draft a ready-to-send {doc_type} in formal Indian English based ONLY on the case file and details.
Include: date, sender and recipient blocks, subject line, numbered facts, the demand (amount, deadline of
15 days unless the case says otherwise), consequences of non-compliance (state in general terms; cite laws only
from allowed references), enclosure list, signature block. Use [PLACEHOLDER] for anything missing.
Do not invent facts, amounts or section numbers.
SENDER/RECIPIENT DETAILS: {details}
CASE FILE:\n"""

COUNTER_SYS = BASE + """
ROLEPLAY MODE: You play the {role} in this dispute, so the user can practise negotiating. Be realistic: firm,
sometimes evasive, use common excuses, but not abusive and never threatening violence. Keep each reply under
90 words. Stay in character. Do NOT give legal advice in character. If the user types 'COACH', break
character and give 3 bullet tips on what they did well/poorly. Case file:
"""

ESCALATION_WORDS = ["fir", "police", "arrest", "summons", "court order", "custody", "divorce", "threat",
                    "jail", "warrant", "violence", "harass", "पुलिस", "गिरफ्तार"]

def escalation_flags(text: str):
    """Rule-based human-in-the-loop trigger, independent of the model."""
    t = text.lower()
    return [w for w in ESCALATION_WORDS if re.search(r"\b" + re.escape(w) + r"\b", t)]

def _gemini(api_key, prompt, system=BASE, history=None, retries=5):
    client = genai.Client(api_key=api_key)
    contents = [types.Content(role=r, parts=[types.Part(text=t)]) for r, t in (history or [])]
    contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
    cfg = types.GenerateContentConfig(system_instruction=system, temperature=0.2)
    for i in range(retries + 1):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=cfg).text or FALLBACK
        except Exception as e:
            if i == retries:
                return f"[ERROR calling model: {e}]"
            time.sleep(2 ** i)

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

def _openai_compat(api_key, prompt, system, history, retries=5):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    msgs = [{"role": "system", "content": system}]
    for r, t in (history or []):
        msgs.append({"role": "assistant" if r == "model" else "user", "content": t})
    msgs.append({"role": "user", "content": prompt})
    for i in range(retries + 1):
        try:
            time.sleep(float(os.getenv("CALL_DELAY", "0")))
            resp = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0.2)
            return resp.choices[0].message.content or FALLBACK
        except Exception as e:
            if i == retries:
                return f"[ERROR calling model: {e}]"
            time.sleep(30 if "429" in str(e) else 2 ** i)

def llm(api_key, prompt, system=BASE, history=None):
    fn = _gemini if PROVIDER == "gemini" else _openai_compat
    return fn(api_key, prompt, system, history)

def case_summary(key, story): return llm(key, SUMMARY_P + story)
def advice(key, summary): return llm(key, ADVICE_P + summary)
def legal_notice(key, summary, details, doc_type):
    return llm(key, NOTICE_P.format(doc_type=doc_type, details=details) + summary)
def counterparty_reply(key, summary, role, history, user_msg):
    return llm(key, user_msg, system=COUNTER_SYS.format(role=role) + summary, history=history)
