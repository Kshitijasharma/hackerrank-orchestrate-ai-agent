def detect_risk(text):
    print("DEBUG: Checking for high risk keywords...")
    text_lower = text.lower()
    high_risk_keywords = [
        "fraud", "unauthorized", "charged", "payment",
        "refund", "account locked", "suspicious"
    ]
    for keyword in high_risk_keywords:
        if keyword in text_lower:
            print(f"DEBUG: High risk keyword '{keyword}' found!")
            return "high"
    return "low"