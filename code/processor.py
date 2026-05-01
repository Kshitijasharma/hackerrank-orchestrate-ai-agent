import os
import pandas as pd
from retriever import build_retriever
from llm import call_llm
from risk import detect_risk
from utils import safe_parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "support_tickets", "support_tickets.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "support_tickets", "output.csv")


def run_pipeline():
    print("DEBUG: Loading input data from CSV...")
    df = pd.read_csv(INPUT_PATH)
    # Convert all column names to lowercase to avoid case-sensitivity issues
    df.columns = [str(col).lower() for col in df.columns]
    
    print("DEBUG: Initializing Retriever...")
    retriever = build_retriever()

    results = []

    print(f"DEBUG: Processing {len(df)} tickets...")
    for index, row in df.iterrows():
        print(f"DEBUG: --- Ticket {index + 1}/{len(df)} ---")
        # Safely handle NaN values
        subject = row.get('subject', '')
        if pd.isna(subject): subject = ""
        
        issue = row.get('issue', '')
        if pd.isna(issue): issue = ""
        
        text = f"{subject} {issue}".strip()

        # If the ticket is completely empty, skip expensive API calls and escalate
        if not text:
            print("DEBUG: Ticket text is empty. Escalating automatically.")
            parsed = {
                "status": "escalated",
                "product_area": "general",
                "response": "No issue details provided.",
                "justification": "Input text was completely empty.",
                "request_type": "invalid"
            }
            results.append(parsed)
            continue

        print("DEBUG: Retrieving context...")
        context = retriever.retrieve(text)

        print("DEBUG: Calling LLM...")
        llm_response = call_llm(text, context)
        
        print("DEBUG: Parsing LLM response...")
        parsed = safe_parse(llm_response)

        print("DEBUG: Detecting risk...")
        risk = detect_risk(text)

        # risk override
        if risk == "high":
            print("DEBUG: High risk detected! Overriding status to 'escalated'.")
            parsed["status"] = "escalated"

        results.append(parsed)

    print("DEBUG: Saving results to CSV...")
    pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)
    print("✅ Output saved to:", OUTPUT_PATH)