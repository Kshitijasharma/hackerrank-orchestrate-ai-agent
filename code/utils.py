import json


def safe_parse(response_text):
    print("DEBUG: Inside safe_parse, attempting to parse JSON...")
    
    # Simple cleanup
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        print("DEBUG: JSON parsed successfully!")
        
        return {
            "status": parsed.get("status", "escalated"),
            "product_area": parsed.get("product_area", "unknown"),
            "response": parsed.get("response", "Could not generate a response."),
            "justification": parsed.get("justification", "No justification provided."),
            "request_type": parsed.get("request_type", "invalid")
        }
    except Exception as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        return {
            "status": "escalated",
            "product_area": "general",
            "response": "Failed to parse LLM output.",
            "justification": f"JSON Decode Error: {e}",
            "request_type": "invalid"
        }