# Nyaya Saathi – An AI Legal Helper for Everyday Problems in India
**Problem 2: Build an AI Lawyer** | Prototype: Streamlit app, model-swappable (final runs on `openai/gpt-oss-120b` via Groq free tier; Gemini also supported) | Repo: (https://github.com/Satyajit-11/nyaya-saathi-ai-legal-helper.git) | Raw outputs: `raw_outputs/`

## 1. Problem Choice & Scoping
**Why this one.** Everyday legal disputes are low-value and frequent: a Rs 90,000 deposit is too small for a lawyer's fee, so people give up. The value is in structuring the story and explaining options, which needs no private data, so a 3-hour prototype can show real value.

**Persona.** A salaried urban person (22–40), smartphone-first, comfortable in Hinglish, no legal vocabulary, who wants to know "what do I do on Monday?"

**Scope.** Three dispute types: rental security deposit, e-commerce refund, unpaid salary. **Not covered:** criminal matters, family law, property title, cheque bounce, tax, anything involving police or court orders.

**Assumptions.** (a) Text input only; voice would be speech-to-text in front of the same pipeline. (b) The user's facts are unverified. (c) State law varies, so the tool names the framework and avoids section-level claims unless allow-listed. (d) Labour-code commencement and state rules change, so they are marked "verify". (e) Every output is a draft for the user to review, never auto-sent.

## 2. Approach & Architecture
Four modules share one case file: **Case Builder** (story → what/when/evidence/missing questions), **Rights & Options** (strengths and weaknesses, cheapest option first), **Document Drafter** (notice, consumer complaint, wage demand), **Practice Mode** (AI plays landlord/employer/customer care). The user can edit the case file before later steps use it, a human check on the AI's reading of their story.

**AI vs. code.** AI handles messy Hinglish, summarising, explaining, drafting and roleplay. Plain code handles key handling, the escalation keyword check, the allow-list of law, retries and state. Model calls go through one `llm()` function that dispatches to Gemini or any OpenAI-compatible API (`LLM_PROVIDER`, `LAWYER_MODEL`), so a stronger model can be swapped in quickly.

**Anti-hallucination design.** (1) A short allow-list of acts in the system prompt, with only two section numbers I was confident of (CPA 2019 s.35 and s.69); nothing else may be cited. (2) A mandatory fallback sentence: *"I do not have enough specific statutory context for this exact clause; please consult a licensed advocate."* (3) No case law at all. (4) `[NOT PROVIDED]` / `[PLACEHOLDER]` instead of invented facts, temperature 0.2, and a disclaimer on every screen. The allow-list is my own knowledge and needs lawyer verification before launch.

**Human-in-the-loop.** A keyword check (FIR, police, arrest, summons, custody…) shows a red banner pointing to a lawyer and NALSA 15100, regardless of the model. The prompt also tells the model to open with "LAWYER RECOMMENDED" for high-stakes matters. Every document is a draft the user must review.

## 3. Scale & Economics (10,000 users/day)
**Tokens (estimated, not measured)** per full session (summary, advice, document, 5 practice turns): about 12,000 input and 5,000 output, since the allow-list and case file are resent each call.

**Cost**, assuming a Flash-class model at about $0.30 per 1M input and $2.50 per 1M output tokens (check current pricing): about $0.016, or Rs 1.4, per session. That is roughly **$160 (Rs 14,000) per day, about $4,800 a month**. Prompt caching and a smaller model for Practice Mode could cut this by an estimated 30–50%. The prototype ran on Groq's free tier.

**Architecture.** A stateless API behind a queue and rate limits, per-user keys, encrypted case storage with deletion, provider fallback, and caching. An escalation queue lets partner advocates review flagged cases and sampled drafts. The hard-coded allow-list would become a **lawyer-curated, dated retrieval corpus per state**.

## 4. Quality Control & Failure Analysis
**Method.** Three hand-written cases (Bengaluru deposit, Hinglish e-commerce refund, unpaid salary) were run through every module by `run_tests.py`; unedited outputs are in `raw_outputs/`. I read every output for invented law, invented facts, language, deadlines and lawyer warnings.

**Review of real runs.** I ran 3 cases on `openai/gpt-oss-120b` (Groq). **Held:** no case law was invented, CPA 2019 s.35/s.69 were used correctly, missing details became placeholders, and the fallback sentence fired once. **Failed:** (1) the Case 1 notice demanded ₹50,000 instead of ₹90,000, silently accepting the disputed deduction; (2) the model invented dates and a year, and Case 2's documents mix 2024 and 2026; (3) it invented institutions and a wrong portal URL, and stated unverified law (the Code on Wages "supersedes" the 1936 Act, limitation periods) without using the fallback; (4) the Hinglish case was answered in Devanagari despite the instruction; (5) the Case 2 "consumer complaint" came back as a grievance letter; (6) the Case 3 employer conceded too easily. **Lesson:** prompt-only guardrails block fabricated sections but not fabricated facts or institutions. Production needs a post-generation check against the allow-list and a lawyer-reviewed retrieval corpus. Free-tier runs also hit 503, 429 and 404 errors, so retries and provider fallback are needed.

**Not tested / known limits.** None of the three cases was high-stakes, so the escalation banner and "LAWYER RECOMMENDED" path were never triggered. Practice-mode COACH feedback and languages other than Hindi/Hinglish are untested. Jurisdiction differences (Karnataka vs Maharashtra), consumer-commission money limits and limitation periods change and must not be stated confidently. Multi-state or litigation-level disputes are escalated, not solved.

## 5. AI Tools Disclosure
**Tools:** Claude (code, prompts, drafting this document, which I edited), Streamlit (UI), Gemini API via `google-genai` (early testing), Groq with `openai/gpt-oss-120b` (final runs). Scoping and guardrail decisions are mine.

**One instance where the AI got it wrong:** Claude wrote the app with `gemini-2.5-flash` as the default model, from memory. When I ran it, every call failed with a 404 NOT_FOUND saying the model was no longer available to new users, and the error text was saved into the case summary box as if it were real output. I fixed it by switching to the model name the error message suggested. I also made the model name an environment variable (`LAWYER_MODEL`) so a retired model can be swapped without editing the code, and I now check the provider's model list instead of trusting a name from memory.

## Run steps
```
pip install -r requirements.txt
# Gemini: set GEMINI_API_KEY
# Groq: set LLM_PROVIDER=openai_compat, LLM_API_KEY, LAWYER_MODEL
streamlit run app.py
python run_tests.py              # writes raw_outputs/
```
