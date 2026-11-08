# Nyaya Saathi – AI Legal Helper (India)

A Streamlit prototype that helps ordinary people in India with everyday legal problems
(rental deposits, e-commerce refunds, unpaid salary).

**Features:** case summary from a messy story, plain-language rights and options,
draft legal notice or complaint, and a negotiation practice mode where the AI plays the other side.

> Informational tool only, not legal advice from a licensed advocate.

## Run
pip install -r requirements.txt

# Gemini: set GEMINI_API_KEY
# Groq: set LLM_PROVIDER=openai_compat, LLM_API_KEY, LAWYER_MODEL
streamlit run app.py

python run_tests.py   # writes raw_outputs/

## Files
- `app.py`: Streamlit app
- `core.py`: prompts, allow-list of law, model calls
- `run_tests.py` and `test_cases.json`: 3 test cases
- `raw_outputs/`: unedited outputs from the test run
- `solution_doc.pdf`: solution document