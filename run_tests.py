"""Runs every test case through every module and saves UNEDITED outputs to raw_outputs/.
Usage:  GEMINI_API_KEY=xxx python run_tests.py"""
import json, os, pathlib, datetime
import core

key = os.getenv("LLM_API_KEY") or os.environ["GEMINI_API_KEY"]
out = pathlib.Path("raw_outputs"); out.mkdir(exist_ok=True)
for c in json.load(open("test_cases.json", encoding="utf-8")):
    log = {"model": core.MODEL, "run_at": datetime.datetime.now().isoformat(), "input": c,
           "escalation_flags": core.escalation_flags(c["story"])}
    log["case_summary"] = core.case_summary(key, c["story"])
    log["advice"] = core.advice(key, log["case_summary"])
    log["legal_document"] = core.legal_notice(key, log["case_summary"], c["details"], c["doc_type"])
    hist, chat = [], []
    for u in c["negotiation_turns"]:
        r = core.counterparty_reply(key, log["case_summary"], c["role"], hist, u)
        hist += [("user", u), ("model", r)]; chat.append({"user": u, "counterparty": r})
    log["negotiation"] = chat
    (out / f"{c['id']}.json").write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / f"{c['id']}.md").write_text(
        f"# {c['id']}\nModel: {core.MODEL}\n\n## Input\n{c['story']}\n\n## Case summary\n{log['case_summary']}\n\n"
        f"## Advice\n{log['advice']}\n\n## Document\n{log['legal_document']}\n\n## Negotiation\n" +
        "\n".join(f"**User:** {x['user']}\n\n**Counterparty:** {x['counterparty']}\n" for x in chat), encoding="utf-8")
    print("done", c["id"])
