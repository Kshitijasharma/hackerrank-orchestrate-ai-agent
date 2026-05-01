# import pandas as pd
# import os
# import json
# from dotenv import load_dotenv
# from anthropic import AnthropicFoundry

# load_dotenv()

# def get_module_responsibility():
#     """
#     Returns the responsibility of this module.
#     """
#     return "This file is responsible for orchestrating the overall data pipeline, including loading tickets, running the process loop, and outputting the final results."

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_PATH = os.path.join(BASE_DIR, "data")

# client = AnthropicFoundry(
#     api_key=os.getenv("FOUNDRY_API_KEY", ""),
#     base_url=os.getenv("FOUNDRY_ENDPOINT", "")
# )

# deployment_name = os.getenv("FOUNDRY_DEPLOYMENT_NAME", "claude-opus-4-7")

# def load_tickets(path):
#     """Load tickets from CSV."""
#     return pd.read_csv(path)

# def load_corpus():
#     corpus = []
#     if os.path.exists(DATA_PATH):
#         for root, _, files in os.walk(DATA_PATH):
#             for file in files:
#                 if file.endswith(".txt"):
#                     path = os.path.join(root, file)
#                     try:
#                         with open(path, "r", encoding="utf-8", errors="ignore") as f:
#                             corpus.append(f.read())
#                     except Exception as e:
#                         pass
#     return corpus

# def retrieve_context(text, corpus):
#     text_lower = text.lower()
#     best_match = ""
#     max_score = 0
    
#     for doc in corpus:
#         score = sum(1 for word in text_lower.split() if word in doc.lower())
#         if score > max_score:
#             max_score = score
#             best_match = doc[:1000] # limit size to avoid massive prompts
            
#     return best_match if best_match else "No relevant info found."

# def detect_risk(text):
#     text_lower = text.lower()
#     risk_keywords = ["fraud", "unauthorized", "charged", "refund", "suspicious"]
#     if any(word in text_lower for word in risk_keywords):
#         return "high"
#     return "low"

# def call_llm(prompt):
#     """Sends prompt to Anthropic Claude and returns response."""
#     if not client.api_key:
#         return ""
    
#     try:
#         response = client.messages.create(
#             model=deployment_name,
#             max_tokens=1024,
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response.content[0].text
#     except Exception as e:
#         print(f"Error calling LLM: {e}")
#         return ""

# def process_ticket(row, corpus):
#     """Process a single ticket row with Azure OpenAI RAG."""
#     subject = str(row.get('subject', ''))
#     issue = str(row.get('issue', ''))
#     text = f"{subject} {issue}".strip()
    
#     # 1. Retrieve context
#     context = retrieve_context(text, corpus)
    
#     # 2. Risk detection
#     risk = detect_risk(text)
    
#     # 3. Build Prompt
#     prompt = f"""You are a support triage agent. Based only on the provided context, return a JSON object with:

# {{
# "status": "replied" or "escalated",
# "product_area": "authentication" | "billing" | "api" | "assessments" | "general",
# "response": "...",
# "justification": "...",
# "request_type": "product_issue" | "feature_request" | "bug" | "invalid"
# }}

# Rules:
# * Use only the provided context
# * If issue involves risk (fraud, payment, account access), escalate
# * Do not hallucinate
# * Be concise and clear

# User Issue:
# {text}

# Retrieved Context:
# {context}
# """

#     # 4. Call LLM
#     llm_output = call_llm(prompt)
    
#     # 5. Parse JSON
#     parsed_json = None
#     if llm_output:
#         # try to strip markdown code blocks if any
#         llm_output_clean = llm_output.strip()
#         if llm_output_clean.startswith("```json"):
#             llm_output_clean = llm_output_clean[7:]
#         elif llm_output_clean.startswith("```"):
#             llm_output_clean = llm_output_clean[3:]
#         if llm_output_clean.endswith("```"):
#             llm_output_clean = llm_output_clean[:-3]
            
#         try:
#             parsed_json = json.loads(llm_output_clean.strip())
#         except json.JSONDecodeError:
#             pass
            
#     if parsed_json is None:
#         parsed_json = {
#             "status": "escalated",
#             "product_area": "general",
#             "response": "Failed to parse LLM response.",
#             "justification": "Fallback due to parsing error.",
#             "request_type": "invalid"
#         }
        
#     # 6. Apply Risk Override
#     if risk == "high":
#         parsed_json["status"] = "escalated"
        
#     # Ensure all required keys exist
#     return {
#         "status": parsed_json.get("status", "escalated"),
#         "product_area": parsed_json.get("product_area", "general"),
#         "response": parsed_json.get("response", "Fallback response."),
#         "justification": parsed_json.get("justification", "Fallback justification."),
#         "request_type": parsed_json.get("request_type", "product_issue")
#     }

# def write_output(df, path):
#     """Write the output dataframe to CSV without missing values."""
#     df.to_csv(path, index=False)

# def main():
#     input_path = os.path.join(BASE_DIR, "support_tickets", "support_tickets.csv")
#     output_path = os.path.join(BASE_DIR, "support_tickets", "output.csv")
    
#     print("Loading tickets...")
#     df = load_tickets(input_path)
    
#     print("Loading corpus...")
#     corpus = load_corpus()
    
#     results = []
#     print("Processing tickets with Azure OpenAI RAG...")
#     for _, row in df.iterrows():
#         result = process_ticket(row, corpus)
#         results.append(result)
        
#     output_df = pd.DataFrame(results)
    
#     # Ensure exact columns are present
#     required_columns = ["status", "product_area", "response", "justification", "request_type"]
#     output_df = output_df[required_columns]
    
#     print("Writing output...")
#     write_output(output_df, output_path)
#     print(f"Pipeline completed. Processed {len(output_df)} rows. Output saved to: {output_path}")

# if __name__ == "__main__":
#     main()

from dotenv import load_dotenv
load_dotenv()

from processor import run_pipeline

if __name__ == "__main__":
    print("DEBUG: Starting main.py...")
    run_pipeline()