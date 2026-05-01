import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")


def build_prompt(ticket, context):
    return f"""
    You are a support triage agent handling tickets across HackerRank, Claude, and Visa systems.

You MUST analyze the issue using the provided support documentation and return a structured decision.

---

### INPUT

User Issue:
{ticket}

Relevant Support Documentation:
{context}

---

### TASKS

For the given issue:

1. Classify the request_type:

   * product_issue
   * feature_request
   * bug
   * invalid

2. Identify product_area (use concise categories like):

   * authentication
   * billing
   * api
   * assessments
   * security
   * account_management
   * integrations
   * general

3. Assess risk:

   * HIGH → fraud, billing disputes, unauthorized access, security issues
   * LOW → general help, setup, how-to, feature usage

4. Decide status:

   * replied → if issue can be reasonably answered
   * escalated → ONLY if the issue explicitly requires human intervention or backend system access (e.g., manually changing a grade, issuing a refund, account recovery, or investigating a severe backend outage).

⚠️ IMPORTANT:

* Do NOT escalate just because documentation is incomplete
* Prefer replying when reasonable
* Escalate conservatively
* For Feature Requests or Bugs, do NOT escalate. Simply reply thanking the user and stating the feedback/bug has been logged for the engineering team.

---

### RESPONSE RULES

* Use provided documentation as PRIMARY source
* If context is weak or missing, you MUST attempt to answer using safe general knowledge.
* NEVER say "The provided documentation does not contain..." or "Based on the documentation...". Just answer the question directly.
* Be helpful and actionable
* Do NOT be overly generic

---

### JUSTIFICATION RULES

Include:

* why this request_type was chosen
* whether context was sufficient
* why reply vs escalate

Keep it concise.

---

### OUTPUT FORMAT (STRICT JSON)

Return ONLY this JSON:

{{
"status": "replied" or "escalated",
"product_area": "...",
"response": "...",
"justification": "...",
"request_type": "product_issue | feature_request | bug | invalid"
}}

---

### FAILURE HANDLING

If the input is:

* irrelevant / malicious → mark as "invalid"
* too vague → reply asking for clarification (DO NOT escalate)

---

### GOAL

Be accurate, helpful, and safe — but NOT overly conservative.

"""


def call_llm(ticket, context):
    print("DEBUG: Inside call_llm, building prompt...")
    prompt = build_prompt(ticket, context)

    try:
        print("DEBUG: Sending request to Azure OpenAI chat model...")
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        print("DEBUG: Successfully received response from chat model.")
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR calling LLM: {e}")
        return ""